import XCTest

/// Runs on the dedicated Duo CI profile. Other profiles run the full compact suite.
final class OnionaryDuoTests: XCTestCase {
    override func setUp() { continueAfterFailure = false }

    @MainActor private func tap(_ title: String, in app: XCUIApplication) throws {
        let matches = app.buttons.matching(identifier: title).allElementsBoundByIndex
        let button = try XCTUnwrap(matches.first(where: { $0.isHittable }), "No visible control: \(title)")
        button.tap()
    }

    private func pose(_ angle: Int) async throws {
        let config = try XCTUnwrap(Bundle(for: Self.self).url(forResource: "duo-port", withExtension: "txt"))
        let port = try String(contentsOf: config, encoding: .utf8).trimmingCharacters(in: .whitespacesAndNewlines)
        let url = try XCTUnwrap(URL(string: "http://127.0.0.1:\(port)/pose/\(angle)"))
        var request = URLRequest(url: url, timeoutInterval: 30); request.httpMethod = "POST"
        let (_, response) = try await URLSession.shared.data(for: request)
        XCTAssertEqual((response as? HTTPURLResponse)?.statusCode, 204)
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
            try await pose(angle)
            XCUIDevice.shared.orientation = angle == 0 ? .portrait : .landscapeLeft
            XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
            XCTAssertTrue(app.staticTexts["2× recipe"].exists)
            XCTAssertTrue(app.buttons["undo"].isEnabled)
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
            try await pose(angle)
            XCUIDevice.shared.orientation = angle == 0 ? .portrait : .landscapeLeft
            XCTAssertEqual(app.textFields["Name"].value as? String, expected)
        }
        try tap("Cancel", in: app)
        XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
    }

    @MainActor func testExpiredSessionKeepsAdaptiveNavigationReachable() async throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "--expired-session", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        XCTAssertTrue(app.buttons["Sign in with passkey"].waitForExistence(timeout: 10))
        for angle in [0, 180, 90] {
            try await pose(angle)
            try tap("Settings", in: app)
            XCTAssertTrue(app.buttons["Sign in with passkey"].allElementsBoundByIndex.contains(where: { $0.isHittable }))
            try tap("Recipes", in: app)
            XCTAssertTrue(app.buttons["add-recipe"].exists)
        }
    }
}
