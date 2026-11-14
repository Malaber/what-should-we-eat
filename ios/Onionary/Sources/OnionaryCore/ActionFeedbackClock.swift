import Foundation
#if DEBUG
import notify
#endif

/// UI feedback has its own lifetime, independent of cooking/menu state.
public enum ActionFeedbackClock {
    public static func waitForExpiry() async throws {
        #if DEBUG
        let process = ProcessInfo.processInfo
        if process.arguments.contains("--ui-testing"),
           let name = process.environment["ONIONARY_TEST_FEEDBACK_CLOCK"],
           name.hasPrefix("de.malaber.onionary.uitest.feedback.") {
            try await FeedbackExpirySignal(name: name).wait()
            return
        }
        #endif
        try await Task.sleep(for: .seconds(4))
    }
}

#if DEBUG
/// A test controls time, not UI state. No server, file polling or guest RPC.
struct FeedbackExpirySignal: Sendable {
    let events: AsyncStream<Void>
    let token: Int32

    init(name: String) throws {
        let (events, continuation) = AsyncStream<Void>.makeStream()
        var registeredToken: Int32 = 0
        let result = notify_register_dispatch(name, &registeredToken, .main) { _ in
            continuation.yield(())
            continuation.finish()
        }
        guard result == NOTIFY_STATUS_OK else {
            continuation.finish()
            throw NSError(domain: "OnionaryFeedbackClock", code: Int(result))
        }
        let token = registeredToken
        continuation.onTermination = { _ in notify_cancel(token) }
        self.events = events
        self.token = token
    }

    func wait() async throws {
        var iterator = events.makeAsyncIterator()
        guard await iterator.next() != nil else { throw CancellationError() }
        try Task.checkCancellation()
    }
}
#endif
