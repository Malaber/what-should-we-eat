import XCTest

@MainActor enum UIAppLifecycle {
    static func background() {
        // Use the system Home action without activating a second app's
        // automation session. Resolve the background process after that handoff;
        // do not send further state queries through the old foreground proxy.
        XCUIDevice.shared.press(.home)
        let home = XCUIApplication(bundleIdentifier: "com.apple.springboard")
        XCTAssertTrue(home.wait(for: .runningForeground, timeout: 10))
    }

    static func terminate() {
        background()
        let background = XCUIApplication()
        if background.state != .notRunning { background.terminate() }
        XCTAssertTrue(background.wait(for: .notRunning, timeout: 10))
    }
}

/// Every device profile releases the old foreground scene/automation session
/// before the next case launches. Duo must follow the same lifecycle as iPad/iPhone.
class OnionaryUITestCase: XCTestCase {
    override class func setUp() {
        super.setUp()
        // Read in-process after XCTest has initialized; no extra host/guest RPC.
        print("Onionary test runtime: \(ProcessInfo.processInfo.operatingSystemVersionString)")
    }

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
    }
    override func tearDownWithError() throws {
        // XCTest invokes synchronous UI lifecycle hooks on the main thread.
        // Keep cleanup synchronous, including after an async test aborts.
        MainActor.assumeIsolated {
            let app = XCUIApplication()
            if app.state != .notRunning { UIAppLifecycle.terminate() }
        }
        try super.tearDownWithError()
    }
}
