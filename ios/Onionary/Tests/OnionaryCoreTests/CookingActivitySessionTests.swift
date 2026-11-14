import XCTest
@testable import OnionaryCore

@MainActor private final class ActivityBackend: CookingActivityBackend {
    var live: [CookingActivityReference: Bool] = [:]
    var exposeRequests = false
    var denyStart = false
    var starts = 0
    var ended: [String] = []
    var updated: [CookingSnapshot] = []
    var updateGate: CheckedContinuation<Void, Never>?
    var blockUpdates = false
    var onUpdate: (() -> Void)?
    func discovered() -> [CookingActivityReference] { exposeRequests ? Array(live.keys) : [] }
    func isRunning(_ activity: CookingActivityReference) -> Bool { live[activity] == true }
    func start(_ snapshot: CookingSnapshot, scope: String) throws -> CookingActivityReference {
        if denyStart { throw CookingError.response("Activity denied") }
        starts += 1
        let ref = CookingActivityReference(id: String(starts), scope: scope, recipeID: snapshot.recipeID)
        live[ref] = true
        return ref
    }
    func update(_ activity: CookingActivityReference, snapshot: CookingSnapshot) async {
        updated.append(snapshot)
        if blockUpdates {
            await withCheckedContinuation { continuation in updateGate = continuation; onUpdate?() }
        }
    }
    func end(_ activity: CookingActivityReference) async { live[activity] = false; ended.append(activity.id) }
}

final class CookingActivitySessionTests: XCTestCase {
    private func snapshot(id: Int = 1, complete: Bool = false) throws -> CookingSnapshot {
        let recipe = try JSONDecoder().decode(Recipe.self, from: Data("{\"id\":\(id),\"householdId\":1,\"name\":\"Soup\",\"ingredients\":[{\"id\":1,\"name\":\"Milk\"}],\"instructionSteps\":[]}".utf8))
        var adventure = Adventure(recipe: recipe)
        if complete { adventure.toggle(key: "ingredient-1", label: "Milk") }
        return CookingSnapshot(adventure)
    }

    @MainActor func testRequestStaysActiveBeforeSystemDiscoveryWithoutDuplicateStart() async throws {
        let backend = ActivityBackend()
        let session = CookingActivitySession(backend: backend)
        let soup = try snapshot()
        try await session.synchronize(soup, scope: "cook", start: true)
        XCTAssertTrue(session.active)
        XCTAssertTrue(backend.discovered().isEmpty)
        try await session.synchronize(soup, scope: "cook", start: true)
        XCTAssertTrue(session.active)
        XCTAssertEqual(backend.starts, 1)
        XCTAssertEqual(backend.updated, [soup])
        try await session.synchronize(nil, scope: "cook")
        XCTAssertFalse(session.active)
        XCTAssertEqual(backend.ended, ["1"])
    }

    @MainActor func testRecipeAndAccountSwitchEndPreviousActivity() async throws {
        let backend = ActivityBackend()
        let session = CookingActivitySession(backend: backend)
        try await session.synchronize(snapshot(), scope: "cook", start: true)
        try await session.synchronize(snapshot(id: 2), scope: "cook", start: true)
        XCTAssertEqual(backend.ended, ["1"])
        try await session.synchronize(snapshot(id: 2), scope: "other", start: true)
        XCTAssertEqual(backend.ended, ["1", "2"])
        XCTAssertEqual(backend.starts, 3)
        XCTAssertTrue(session.active)
    }

    @MainActor func testCompletionEndsActivityWithoutRestarting() async throws {
        let backend = ActivityBackend()
        let session = CookingActivitySession(backend: backend)
        try await session.synchronize(snapshot(), scope: "cook", start: true)
        try await session.synchronize(snapshot(complete: true), scope: "cook", start: true)
        XCTAssertFalse(session.active)
        XCTAssertEqual(backend.starts, 1)
        XCTAssertEqual(backend.ended, ["1"])
    }

    @MainActor func testDeniedStartIsReportedAndNeverShownActive() async throws {
        let backend = ActivityBackend(); backend.denyStart = true
        let session = CookingActivitySession(backend: backend)
        do {
            try await session.synchronize(snapshot(), scope: "cook", start: true)
            XCTFail("Denied request succeeded")
        } catch { XCTAssertEqual(session.lastFailure, error.localizedDescription) }
        XCTAssertFalse(session.active)
        XCTAssertEqual(backend.starts, 0)
    }

    @MainActor func testRestoresDiscoveredActivityAndHonorsExternalEnd() async throws {
        let backend = ActivityBackend(); backend.exposeRequests = true
        let soup = try snapshot()
        let ref = try backend.start(soup, scope: "cook")
        let session = CookingActivitySession(backend: backend)
        try await session.synchronize(soup, scope: "cook")
        XCTAssertTrue(session.active)
        XCTAssertEqual(backend.starts, 1)
        backend.live[ref] = false
        try await session.synchronize(soup, scope: "cook")
        XCTAssertFalse(session.active)
    }

    @MainActor func testDelayedUpdateCannotOvertakeStop() async throws {
        let backend = ActivityBackend()
        let session = CookingActivitySession(backend: backend)
        let soup = try snapshot()
        try await session.synchronize(soup, scope: "cook", start: true)
        backend.blockUpdates = true
        let began = expectation(description: "Update entered backend")
        backend.onUpdate = { began.fulfill() }
        let update = Task { try await session.synchronize(soup, scope: "cook") }
        await fulfillment(of: [began], timeout: 2)
        let stop = Task { try await session.synchronize(nil, scope: "cook") }
        backend.updateGate?.resume()
        try await update.value
        try await stop.value
        XCTAssertFalse(session.active)
        XCTAssertEqual(backend.ended, ["1"])
    }
}
