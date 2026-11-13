// This SDK exposes nonisolated async methods on Activity without Sendable
// annotations. App-side handles stay MainActor-owned; the session serializes
// all OS operations. Keep legacy framework interoperability local to this file.
@preconcurrency import ActivityKit
import Foundation
import OnionaryCore
import Observation

/// Keep the actual Activity object returned by request, including before it is
/// visible in Activity.activities. Its own state remains the authority.
@MainActor private final class AppleCookingActivityBackend: CookingActivityBackend {
    private var handles: [String: Activity<CookingActivityAttributes>] = [:]
    func discovered() -> [CookingActivityReference] {
        let discovered = Activity<CookingActivityAttributes>.activities.map { activity in
            handles[activity.id] = activity
            return reference(activity)
        }
        handles = handles.filter { $0.value.activityState == .active || $0.value.activityState == .stale }
        return discovered
    }
    func isRunning(_ activity: CookingActivityReference) -> Bool {
        guard let state = handles[activity.id]?.activityState else { return false }
        return state == .active || state == .stale
    }
    func start(_ snapshot: CookingSnapshot, scope: String) throws -> CookingActivityReference {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else {
            throw CookingError.response("Enable Live Activities for Onionary in iOS Settings.")
        }
        let activity = try Activity.request(attributes: CookingActivityAttributes(scope: scope, recipeID: snapshot.recipeID),
            content: content(snapshot), pushType: nil)
        handles[activity.id] = activity
        return reference(activity)
    }
    func update(_ activity: CookingActivityReference, snapshot: CookingSnapshot) async {
        await handles[activity.id]?.update(content(snapshot))
    }
    func end(_ activity: CookingActivityReference) async {
        await handles[activity.id]?.end(nil, dismissalPolicy: .immediate)
        handles.removeValue(forKey: activity.id)
    }
    private func reference(_ activity: Activity<CookingActivityAttributes>) -> CookingActivityReference {
        CookingActivityReference(id: activity.id, scope: activity.attributes.scope, recipeID: activity.attributes.recipeID)
    }
    private func content(_ snapshot: CookingSnapshot) -> ActivityContent<CookingSnapshot> {
        ActivityContent(state: snapshot, staleDate: Date().addingTimeInterval(3 * 3600))
    }
}

@MainActor @Observable final class CookingActivityController {
    private let session: CookingActivitySession
    init() {
        #if DEBUG
        let arguments = ProcessInfo.processInfo.arguments
        if arguments.contains("--ui-testing"), !arguments.contains("--system-live-activity") {
            session = CookingActivitySession(backend: UITestCookingActivityBackend())
            return
        }
        #endif
        // Real ActivityKit is mandatory for production and its dedicated UI
        // integration case. Other fixtures must not leak OS activities across
        // app launches or animate SpringBoard during unrelated recipe tests.
        session = CookingActivitySession(backend: AppleCookingActivityBackend())
    }
    var active: Bool { session.active }
    var lastFailure: String? { session.lastFailure }
    func synchronize(_ snapshot: CookingSnapshot?, scope: String, start: Bool = false) async throws {
        try await session.synchronize(snapshot, scope: scope, start: start)
    }
}
