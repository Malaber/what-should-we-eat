import XCTest

/// Runs on the dedicated Duo CI profile. Other profiles run the full compact suite.
final class OnionaryDuoTests: OnionaryUITestCase {

    @MainActor private func tap(_ title: String, in app: XCUIApplication) throws {
        let window = app.windows.element(boundBy: 0)
        // Resolve through the receiving window after every display handoff.
        // A unique query also fails if duplicate controls become actionable.
        let button = UIReadiness.buttons(title, in: window).element
        let exists = button.waitForExistence(timeout: 10)
        let validFrame = exists && UIReadiness.validControlFrame(button.frame, in: window.frame)
        if !validFrame {
            captureFailure("Unreachable control: \(title)", in: app)
        }
        XCTAssertTrue(exists, "Missing control after folding: \(title)")
        XCTAssertTrue(validFrame, "Invalid control geometry: \(title)")
        // Native tap synchronizes and computes a hittable point itself. An
        // additional isHittable preflight can error on a stale fold snapshot
        // before this action gets a chance to synchronize or scroll the row.
        // This is one real element tap, never a forced/coordinate fallback.
        button.tap()
    }

    @MainActor private func pose(_ angle: Int, in app: XCUIApplication) throws {
        XCTAssertEqual(OnionarySetHingeAngle(Double(angle)), 0, "Native hinge dispatch failed at \(angle)°")
        XCUIDevice.shared.orientation = angle == 0 ? .portrait : .landscapeLeft
        // Native dispatch confirms injection, not completion of the display handoff.
        // Require the selected display bounds before reading any UI.
        let displayChanged = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in
            UIReadiness.duoViewport(app.frame, angle: angle)
                && UIReadiness.duoWindow(app.windows.element(boundBy: 0).frame, angle: angle)
        }, object: nil)
        let result = XCTWaiter.wait(for: [displayChanged], timeout: 15)
        if result != .completed { captureFailure("Unsettled window at \(angle)°", in: app) }
        XCTAssertEqual(result, .completed, "Receiving window must finish the requested display rotation")
    }

    @MainActor private func capture(_ angle: Int, in app: XCUIApplication) {
        // The app-root capture can select the inactive cover display. A window
        // retains display affinity; use it through the existing XCTest session.
        let attachment = XCTAttachment(screenshot: app.windows.element(boundBy: 0).screenshot())
        attachment.name = "Duo-workspace-\(angle)"; attachment.lifetime = .keepAlways; add(attachment)
    }

    @MainActor private func captureFailure(_ title: String, in app: XCUIApplication) {
        let screen = XCTAttachment(screenshot: app.windows.element(boundBy: 0).screenshot())
        screen.name = title; screen.lifetime = .keepAlways; add(screen)
        let hierarchy = XCTAttachment(string: app.debugDescription)
        hierarchy.name = title + " hierarchy"; hierarchy.lifetime = .keepAlways; add(hierarchy)
    }

    @MainActor private func assertIngredient(_ expected: String, in app: XCUIApplication) {
        let query = UIReadiness.buttons("ingredient-1", in: app.windows.element(boundBy: 0))
        let committed = UIReadiness.waitForValue(expected, matching: query)
        if !committed { captureFailure("Ingredient did not become \(expected)", in: app) }
        XCTAssertTrue(committed)
        XCTAssertEqual(query.element.value as? String, expected)
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
        XCTAssertTrue(UIReadiness.duoWindow(CGRect(x: 0, y: 0, width: 466, height: 678), angle: 0))
        XCTAssertTrue(UIReadiness.duoWindow(CGRect(x: 0, y: 0, width: 951, height: 669), angle: 90))
        XCTAssertTrue(UIReadiness.duoWindow(CGRect(x: 0, y: 0, width: 951, height: 669), angle: 180))
        // Correct physical display, stale orientation: not ready for input.
        XCTAssertFalse(UIReadiness.duoWindow(CGRect(x: 0, y: 0, width: 678, height: 466), angle: 0))
        XCTAssertFalse(UIReadiness.duoWindow(CGRect(x: 0, y: 0, width: 669, height: 951), angle: 180))
        XCTAssertFalse(UIReadiness.duoWindow(.zero, angle: 90))
        XCTAssertFalse(UIReadiness.duoWindow(CGRect(x: 0, y: 0, width: 951, height: 669), angle: 45))
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

    @MainActor private func launchCookingFixture() throws -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        // Hinge state belongs to the device, not the app's reset fixture.
        // Every independent case establishes its own initial physical display.
        try pose(0, in: app)
        XCTAssertTrue(app.buttons["Choose a recipe"].waitForExistence(timeout: 10))
        return app
    }

    @MainActor private func startCooking(in app: XCUIApplication) throws {
        try tap("Recipes", in: app)
        try tap("recipe-1", in: app)
        try tap("preview-cook", in: app)
        try tap("portion-plus", in: app)
        try tap("ingredient-1", in: app)
        XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
        XCTAssertTrue(app.staticTexts["2× recipe"].exists)
    }

    @MainActor func testRecipePreviewAndChecklistSurviveFolds() throws {
        let app = try launchCookingFixture()
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
            try pose(angle, in: app)
            XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
            XCTAssertTrue(app.staticTexts["2× recipe"].exists)
            XCTAssertTrue(app.buttons["undo"].isEnabled)
            capture(angle, in: app)
        }
        try tap("undo", in: app)
        assertIngredient("Unchecked", in: app)
        try tap("redo", in: app)
        assertIngredient("Checked", in: app)
    }

    @MainActor func testRecipeDraftSurvivesFolds() throws {
        let app = try launchCookingFixture()
        try startCooking(in: app)
        try pose(180, in: app)
        try tap("Cooking options", in: app)
        try tap("Edit recipe", in: app)
        let name = app.textFields["Name"]
        XCTAssertTrue(name.waitForExistence(timeout: 5))
        let expected = try XCTUnwrap(name.value as? String) + " Duo draft"
        name.tap()
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForExistence(timeout: 5))
        name.typeText(" Duo draft")
        XCTAssertTrue(UIReadiness.waitForValue(expected, matching: app.textFields.matching(identifier: "Name")), "Complete draft input must commit before folding")
        XCTAssertEqual(name.value as? String, expected)
        for angle in [0, 90, 180] {
            try pose(angle, in: app)
            XCTAssertEqual(app.textFields["Name"].value as? String, expected)
        }
        try tap("Cancel", in: app)
        XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
        XCTAssertTrue(app.staticTexts["2× recipe"].exists)
    }

    @MainActor func testKitchenShoppingChecksSurviveFolds() throws {
        let app = try launchCookingFixture()
        try startCooking(in: app)
        try pose(180, in: app)
        try tap("Kitchen", in: app)
        try tap("Add meals", in: app)
        try tap("Lemon & cheese pasta", in: app)
        try tap("Add", in: app)
        XCTAssertTrue(app.buttons["Mark cooked"].waitForExistence(timeout: 5))
        try tap("Generate shopping list", in: app)
        XCTAssertTrue(app.buttons["shopping-cheese"].waitForExistence(timeout: 5))
        try tap("shopping-cheese", in: app)
        for angle in [0, 180] {
            try pose(angle, in: app)
            XCTAssertEqual(app.buttons["shopping-cheese"].value as? String, "Checked")
        }
        try tap("Refresh shopping list", in: app)
        XCTAssertEqual(app.buttons["shopping-cheese"].value as? String, "Checked")
    }

    @MainActor func testExpiredSessionKeepsAdaptiveNavigationReachable() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "--expired-session", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        XCTAssertTrue(app.buttons["Sign in with passkey"].waitForExistence(timeout: 10))
        for angle in [0, 180, 90] {
            try pose(angle, in: app)
            try tap("Settings", in: app)
            XCTAssertTrue(UIReadiness.button("Sign in with passkey", in: app).isHittable)
            try tap("Recipes", in: app)
            XCTAssertTrue(app.buttons["add-recipe"].exists)
        }
    }
}
