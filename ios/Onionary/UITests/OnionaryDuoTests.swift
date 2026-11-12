import XCTest

/// Runs on the dedicated Duo CI profile. Other profiles run the full compact suite.
final class OnionaryDuoTests: OnionaryUITestCase {

    @MainActor private func tap(_ title: String, in app: XCUIApplication) throws {
        var resolved: XCUIElement?
        let visible = NSPredicate { _, _ in
            resolved = UIReadiness.visibleButtons(title, in: app).first
            return resolved != nil
        }
        let ready = XCTNSPredicateExpectation(predicate: visible, object: nil)
        let result = XCTWaiter.wait(for: [ready], timeout: 10)
        if result != .completed {
            // One coherent hierarchy, rather than re-querying window indices
            // while a keyboard is disappearing after a fold.
            let snapshot = XCTAttachment(string: app.debugDescription)
            snapshot.name = "Unreachable control hierarchy"; snapshot.lifetime = .keepAlways; add(snapshot)
        }
        XCTAssertEqual(result, .completed, "Navigation did not settle after folding: \(title)")
        let button = try XCTUnwrap(resolved, "No visible control: \(title)")
        button.tap()
    }

    @MainActor private func pose(_ angle: Int, in app: XCUIApplication) async throws {
        XCTAssertEqual(OnionarySetHingeAngle(Double(angle)), 0, "Native hinge dispatch failed at \(angle)°")
        XCUIDevice.shared.orientation = angle == 0 ? .portrait : .landscapeLeft
        // Native dispatch confirms injection, not completion of the display handoff.
        // Require the selected display bounds before reading any UI.
        let displayChanged = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            UIReadiness.duoViewport(app.frame, angle: angle)
        }, object: nil)
        await fulfillment(of: [displayChanged], timeout: 15)

    }

    @MainActor private func capture(_ angle: Int, in app: XCUIApplication) {
        // Capture the active app through the existing automation connection;
        // spawning simctl screenshot for every fold can stall the display service.
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = "Duo-workspace-\(angle)"; attachment.lifetime = .keepAlways; add(attachment)
    }

    @MainActor func testInvalidHingeAnglesAreRejected() {
        for angle in [-1.0, 181.0, Double.nan, Double.infinity] {
            XCTAssertEqual(OnionarySetHingeAngle(angle), 1)
        }
    }

    func testReadinessRejectsWrongDisplayAndHiddenFrames() {
        XCTAssertTrue(UIReadiness.duoViewport(CGRect(x: 0, y: 0, width: 466, height: 678), angle: 0))
        XCTAssertTrue(UIReadiness.duoViewport(CGRect(x: 0, y: 0, width: 678, height: 466), angle: 0))
        XCTAssertTrue(UIReadiness.duoViewport(CGRect(x: 0, y: 0, width: 951, height: 669), angle: 180))
        XCTAssertTrue(UIReadiness.duoViewport(CGRect(x: 0, y: 0, width: 669, height: 951), angle: 180))
        // Same area as the outer display, but not a valid display shape.
        XCTAssertFalse(UIReadiness.duoViewport(CGRect(x: 0, y: 0, width: 233, height: 1356), angle: 0))
        let viewport = CGRect(x: 0, y: 0, width: 466, height: 678)
        XCTAssertTrue(UIReadiness.validControlFrame(CGRect(x: 12, y: 600, width: 44, height: 44), in: viewport))
        XCTAssertFalse(UIReadiness.validControlFrame(.zero, in: viewport))
        XCTAssertFalse(UIReadiness.validControlFrame(.null, in: viewport))
        XCTAssertFalse(UIReadiness.validControlFrame(CGRect(x: 12, y: 900, width: 44, height: 44), in: viewport))
        let landscapeWindow = CGRect(x: 0, y: 0, width: 951, height: 669)
        let toolbar = CGRect(x: 884, y: 185, width: 38, height: 38)
        XCTAssertFalse(UIReadiness.validControlFrame(toolbar, in: CGRect(x: 0, y: 0, width: 669, height: 951)))
        XCTAssertTrue(UIReadiness.validControlFrame(toolbar, in: landscapeWindow))
    }

    @MainActor func testCookingPreviewAndDraftSurviveFolds() async throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        XCTAssertTrue(app.buttons["Choose a recipe"].waitForExistence(timeout: 10))
        try tap("Recipes", in: app)
        try tap("recipe-1", in: app)
        XCTAssertTrue(app.buttons["preview-cook"].waitForExistence(timeout: 5))
        // Previewing must not start a cooking adventure.
        try tap("Cooking", in: app)
        XCTAssertTrue(app.buttons["Choose a recipe"].exists)
        try tap("Recipes", in: app)
        try tap("preview-cook", in: app)
        try tap("portion-plus", in: app)
        try tap("ingredient-1", in: app)
        for angle in [0, 180, 90, 180, 0, 180] {
            try await pose(angle, in: app)
            XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
            XCTAssertTrue(app.staticTexts["2× recipe"].exists)
            XCTAssertTrue(app.buttons["undo"].isEnabled)
            capture(angle, in: app)
        }
        try tap("undo", in: app)
        XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Unchecked")
        try tap("redo", in: app)
        XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
        try tap("Cooking options", in: app)
        try tap("Edit recipe", in: app)
        let name = app.textFields["Name"]
        XCTAssertTrue(name.waitForExistence(timeout: 5))
        name.tap(); name.typeText(" Duo draft")
        let expected = name.value as? String
        for angle in [0, 90, 180] {
            try await pose(angle, in: app)
            XCTAssertEqual(app.textFields["Name"].value as? String, expected)
        }
        try tap("Cancel", in: app)
        XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
        try tap("Kitchen", in: app)
        try tap("Add meals", in: app)
        try tap("Lemon & cheese pasta", in: app)
        try tap("Add", in: app)
        XCTAssertTrue(app.buttons["Mark cooked"].waitForExistence(timeout: 5))
        try tap("Generate shopping list", in: app)
        XCTAssertTrue(app.buttons["shopping-cheese"].waitForExistence(timeout: 5))
        try tap("shopping-cheese", in: app)
        for angle in [0, 180] {
            try await pose(angle, in: app)
            XCTAssertEqual(app.buttons["shopping-cheese"].value as? String, "Checked")
        }
        try tap("Refresh shopping list", in: app)
        XCTAssertEqual(app.buttons["shopping-cheese"].value as? String, "Checked")
    }

    @MainActor func testExpiredSessionKeepsAdaptiveNavigationReachable() async throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "--expired-session", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        XCTAssertTrue(app.buttons["Sign in with passkey"].waitForExistence(timeout: 10))
        for angle in [0, 180, 90] {
            try await pose(angle, in: app)
            try tap("Settings", in: app)
            XCTAssertTrue(!UIReadiness.visibleButtons("Sign in with passkey", in: app).isEmpty)
            try tap("Recipes", in: app)
            XCTAssertTrue(app.buttons["add-recipe"].exists)
        }
    }
}
