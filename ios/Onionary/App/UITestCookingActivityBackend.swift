#if DEBUG
import Foundation
import OnionaryCore

/// Process-local external-service fixture. The real session still owns all
/// automatic starts, updates, completion, account changes and toggle behavior.
/// Never compiled into Release; the real-OS UI case explicitly uses ActivityKit.
@MainActor final class UITestCookingActivityBackend: CookingActivityBackend {
    private var activities: [String: (reference: CookingActivityReference, snapshot: CookingSnapshot)] = [:]

    func discovered() -> [CookingActivityReference] { activities.values.map(\.reference) }
    func isRunning(_ activity: CookingActivityReference) -> Bool {
        activities[activity.id]?.reference == activity
    }
    func start(_ snapshot: CookingSnapshot, scope: String) throws -> CookingActivityReference {
        let reference = CookingActivityReference(id: UUID().uuidString, scope: scope, recipeID: snapshot.recipeID)
        activities[reference.id] = (reference, snapshot)
        return reference
    }
    func update(_ activity: CookingActivityReference, snapshot: CookingSnapshot) async {
        guard isRunning(activity) else { return }
        activities[activity.id] = (activity, snapshot)
    }
    func end(_ activity: CookingActivityReference) async {
        activities.removeValue(forKey: activity.id)
    }
}
#endif
