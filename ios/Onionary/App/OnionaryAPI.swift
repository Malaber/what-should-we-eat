import Foundation
import OnionaryCore

/// Reject redirects so an arbitrary backend cannot redirect authenticated requests elsewhere.
final class NoRedirects: NSObject, URLSessionTaskDelegate, Sendable {
    func urlSession(_ session: URLSession, task: URLSessionTask,
                    willPerformHTTPRedirection response: HTTPURLResponse,
                    newRequest request: URLRequest,
                    completionHandler: @escaping @Sendable (URLRequest?) -> Void) { completionHandler(nil) }
}

struct OnionaryAPI: Sendable {
    let server: URL
    let token: String
    static var decoder: JSONDecoder {
        let decoder = JSONDecoder(); decoder.keyDecodingStrategy = .convertFromSnakeCase; return decoder
    }
    func data(_ path: String, method: String = "GET", body: Data? = nil) async throws -> Data {
        #if DEBUG
        if server.host == "ui-test.invalid" && ProcessInfo.processInfo.arguments.contains("--ui-testing") {
            return try await UITestBackend.data(path, method: method, body: body)
        }
        #endif
        var request = URLRequest(url: server.appending(path: path))
        request.httpMethod = method; request.httpBody = body; request.timeoutInterval = 30
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if !token.isEmpty { request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization") }
        let config = URLSessionConfiguration.ephemeral
        config.httpCookieStorage = nil
        let session = URLSession(configuration: config, delegate: NoRedirects(), delegateQueue: nil)
        defer { session.finishTasksAndInvalidate() }
        let (data, response) = try await session.data(for: request)
        guard let response = response as? HTTPURLResponse else { throw CookingError.response("No response from your kitchen.") }
        guard (200..<300).contains(response.statusCode) else {
            if response.statusCode == 401 { throw CookingError.response("Your sign-in expired. Reconnect in Settings; your cooking progress is saved.") }
            throw CookingError.response("Your backend returned HTTP \(response.statusCode). Please try again.")
        }
        return data
    }
}
