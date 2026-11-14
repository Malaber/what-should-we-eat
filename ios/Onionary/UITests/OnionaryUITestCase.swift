import XCTest

@MainActor enum UIAppLifecycle {
    static func background() {
        // Use the system Home action without activating a second app's
        // automation session. Wait for SpringBoard to finish the handoff.
        XCUIDevice.shared.press(.home)
        let home = XCUIApplication(bundleIdentifier: "com.apple.springboard")
        XCTAssertTrue(home.wait(for: .runningForeground, timeout: 10))
    }
}

/// Each UI scenario calls launch(), which terminates an existing instance and
/// starts its own reset fixture. Cold-persistence tests launch again without
/// clearing the fixture files; do not add a global Home/terminate boundary.
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
}
