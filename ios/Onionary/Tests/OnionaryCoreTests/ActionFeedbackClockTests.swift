import XCTest
#if DEBUG
import notify
#endif
@testable import OnionaryCore

final class ActionFeedbackClockTests: XCTestCase {
    @MainActor func testDefaultExpiryHonorsCancellation() async throws {
        let wait = Task { try await ActionFeedbackClock.waitForExpiry() }
        wait.cancel()
        do {
            try await wait.value
            XCTFail("Cancelled feedback must not expire normally")
        } catch is CancellationError {}
    }

    #if DEBUG
    @MainActor func testSignalExpiresPendingFeedbackAndDisposesObserver() async throws {
        let name = "de.malaber.onionary.uitest.feedback." + UUID().uuidString
        let signal = try FeedbackExpirySignal(name: name)
        defer { notify_cancel(signal.token) }
        XCTAssertTrue(notify_is_valid_token(signal.token))
        let expired = expectation(description: "Controlled feedback expired")
        let wait = Task {
            try await signal.wait()
            expired.fulfill()
        }
        XCTAssertEqual(notify_post(name), UInt32(NOTIFY_STATUS_OK))
        await fulfillment(of: [expired], timeout: 5)
        wait.cancel()
        try await wait.value
        XCTAssertFalse(notify_is_valid_token(signal.token))
    }

    @MainActor func testReplacingFeedbackCancelsObserverWithoutExpiringReplacement() async throws {
        let old = try FeedbackExpirySignal(name: "de.malaber.onionary.uitest.feedback." + UUID().uuidString)
        let nextName = "de.malaber.onionary.uitest.feedback." + UUID().uuidString
        let replacement = try FeedbackExpirySignal(name: nextName)
        defer { notify_cancel(old.token); notify_cancel(replacement.token) }
        let wait = Task { try await old.wait() }
        wait.cancel()
        do {
            try await wait.value
            XCTFail("Cancelled feedback must not expire normally")
        } catch is CancellationError {}
        XCTAssertFalse(notify_is_valid_token(old.token))
        XCTAssertTrue(notify_is_valid_token(replacement.token))
        let expired = expectation(description: "Replacement has its own expiry")
        let next = Task { try await replacement.wait(); expired.fulfill() }
        XCTAssertEqual(notify_post(nextName), UInt32(NOTIFY_STATUS_OK))
        await fulfillment(of: [expired], timeout: 5)
        next.cancel()
        try await next.value
        XCTAssertFalse(notify_is_valid_token(replacement.token))
    }
    #endif
}
