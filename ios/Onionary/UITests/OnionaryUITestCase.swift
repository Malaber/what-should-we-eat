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

    @MainActor
    func captureMarketingScenes(
        in app: XCUIApplication,
        tap: (String) throws -> Void,
        capture: (String) -> Void
    ) throws {
        try tap("Choose a recipe")
        XCTAssertTrue(app.buttons.matching(identifier: "recipe-1").firstMatch.waitForExistence(timeout: 5))
        capture("01-recipe-book")
        try tap("recipe-1")
        try tap("preview-cook")
        try tap("ingredient-1")
        try tap("ingredient-2")
        try tap("undo")
        try tap("redo")
        try tap("ingredient-1")
        try tap("ingredient-1")
        XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
        XCTAssertTrue(app.staticTexts["recent-action"].waitForNonExistence(timeout: 8))
        capture("02-cooking-companion")
        try tap("Adjust portions")
        XCTAssertTrue(app.textFields["portions"].waitForExistence(timeout: 5))
        capture("03-flexible-portions")
        try tap("apply-portions")
        try tap("History")
        XCTAssertTrue(app.staticTexts["Tap history"].waitForExistence(timeout: 5))
        capture("04-every-tap-remembered")
    }

    @MainActor
    func attachMarketingScreenshot(_ screenshot: XCUIScreenshot, name: String) {
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "marketing-" + name
        attachment.lifetime = .keepAlways
        add(attachment)
    }
}
