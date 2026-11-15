import Foundation
import Observation

public struct CookingActivityReference: Hashable, Sendable {
    public let id: String
    public let scope: String
    public let recipeID: Int
    public init(id: String, scope: String, recipeID: Int) {
        self.id = id; self.scope = scope; self.recipeID = recipeID
    }
}

@MainActor public protocol CookingActivityBackend {
    func discovered() -> [CookingActivityReference]
    func isRunning(_ activity: CookingActivityReference) -> Bool
    func start(_ snapshot: CookingSnapshot, scope: String) throws -> CookingActivityReference
    func update(_ activity: CookingActivityReference, snapshot: CookingSnapshot) async
    func end(_ activity: CookingActivityReference) async
}

/// Retain successful requests independently of eventual system-list discovery.
/// Serialize requests so a delayed update cannot overtake a stop/account switch.
@MainActor @Observable public final class CookingActivitySession {
    public private(set) var active = false
    public private(set) var lastFailure: String?
    private let backend: any CookingActivityBackend
    private var known: [String: CookingActivityReference] = [:]
    private var pending: Task<Void, Never>?

    public init(backend: any CookingActivityBackend) { self.backend = backend }

    public func synchronize(_ snapshot: CookingSnapshot?, scope: String, start: Bool = false) async throws {
        let previous = pending
        var failure: Error?
        let task = Task { @MainActor in
            await previous?.value
            for activity in backend.discovered() { known[activity.id] = activity }
            known = known.filter { backend.isRunning($0.value) }
            for activity in Array(known.values) {
                if snapshot == nil || activity.scope != scope || activity.recipeID != snapshot?.recipeID || snapshot?.complete == true {
                    await backend.end(activity)
                    known.removeValue(forKey: activity.id)
                } else if let snapshot {
                    await backend.update(activity, snapshot: snapshot)
                }
            }
            if start, let snapshot, !snapshot.complete, known.isEmpty {
                do {
                    let created = try backend.start(snapshot, scope: scope)
                    known[created.id] = created
                    lastFailure = nil
                } catch {
                    failure = error
                    lastFailure = error.localizedDescription
                }
            }
            active = known.values.contains { backend.isRunning($0) }
            if snapshot == nil { lastFailure = nil }
        }
        pending = task
        await task.value
        if let failure { throw failure }
    }
}
