import XCTest

@MainActor enum UIAppLifecycle {
    static func terminate(_ app: XCUIApplication) {
        let home = XCUIApplication(bundleIdentifier: "com.apple.springboard")
        home.activate()
        XCTAssertTrue(home.wait(for: .runningForeground, timeout: 10))
        app.terminate()
        XCTAssertTrue(app.wait(for: .notRunning, timeout: 10))
    }
}

/// Every device profile releases the old foreground scene/automation session
/// before the next case launches. Duo must follow the same lifecycle as iPad/iPhone.
class OnionaryUITestCase: XCTestCase {
    override func setUp() {
        super.setUp()
        continueAfterFailure = false
    }
    override func tearDownWithError() throws {
        // XCTest invokes synchronous UI lifecycle hooks on the main thread.
        // Keep cleanup synchronous, including after an async test aborts.
        MainActor.assumeIsolated {
            let app = XCUIApplication()
            if app.state != .notRunning { UIAppLifecycle.terminate(app) }
        }
        try super.tearDownWithError()
    }
}
