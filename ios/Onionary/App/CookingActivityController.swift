import ActivityKit
import Foundation
import OnionaryCore
import Observation

/// Serialize updates so rapid checks, recipe switches and sign-out cannot overtake each other.
@MainActor @Observable
final class CookingActivityController {
    private var pending: Task<Void, Never>?
    var active = false

    func synchronize(_ snapshot: CookingSnapshot?, scope: String, start: Bool = false) async throws {
        let previous = pending
        var failure: Error?
        let task = Task { @MainActor in
            await previous?.value
            let existing = Activity<CookingActivityAttributes>.activities
            for activity in existing {
                if snapshot == nil || activity.attributes.scope != scope || activity.attributes.recipeID != snapshot?.recipeID || snapshot?.complete == true {
                    await activity.end(nil, dismissalPolicy: .immediate)
                } else if let snapshot {
                    await activity.update(ActivityContent(state: snapshot, staleDate: Date().addingTimeInterval(3 * 3600)))
                }
            }
            let matching = Activity<CookingActivityAttributes>.activities.filter {
                $0.attributes.scope == scope && $0.attributes.recipeID == snapshot?.recipeID
                    && ($0.activityState == .active || $0.activityState == .stale)
            }
            if start, let snapshot, !snapshot.complete, matching.isEmpty {
                do {
                    guard ActivityAuthorizationInfo().areActivitiesEnabled else {
                        throw CookingError.response("Enable Live Activities for Onionary in iOS Settings.")
                    }
                    _ = try Activity.request(attributes: CookingActivityAttributes(scope: scope, recipeID: snapshot.recipeID),
                        content: ActivityContent(state: snapshot, staleDate: Date().addingTimeInterval(3 * 3600)), pushType: nil)
                } catch { failure = error }
            }
            active = Activity<CookingActivityAttributes>.activities.contains {
                $0.attributes.scope == scope && $0.attributes.recipeID == snapshot?.recipeID
                    && ($0.activityState == .active || $0.activityState == .stale)
            }
        }
        pending = task
        await task.value
        if let failure { throw failure }
    }
}
