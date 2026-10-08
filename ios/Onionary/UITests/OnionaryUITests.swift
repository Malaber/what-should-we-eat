import XCTest

final class OnionaryUITests: XCTestCase {
    @MainActor
    func testMarketingScreenshots() {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        app.buttons["Choose a recipe"].tap()
        capture("01-recipe-book")
        app.buttons["recipe-1"].firstMatch.tap()
        XCTAssertTrue(app.buttons["ingredient-1"].waitForExistence(timeout: 5))
        capture("02-cooking-companion")
        app.buttons["ingredient-1"].tap()
        app.buttons["Adjust portions"].tap()
        XCTAssertTrue(app.textFields["multiplier"].waitForExistence(timeout: 5))
        capture("03-flexible-portions")
        app.buttons["Done"].tap()
        app.buttons["History"].tap()
        XCTAssertTrue(app.staticTexts["Tap history"].waitForExistence(timeout: 5))
        capture("04-every-tap-remembered")
    }

    @MainActor
    private func capture(_ name: String) {
        let attachment = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        attachment.name = "marketing-" + name
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    @MainActor
    func testCookUndoScaleAndRestoreAfterTermination() {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset"]
        app.launch()
        app.buttons["Choose a recipe"].tap()
        app.buttons["recipe-1"].firstMatch.tap()
        let cheese = app.buttons["ingredient-1"]
        XCTAssertTrue(cheese.waitForExistence(timeout: 5))
        cheese.tap()
        XCTAssertEqual(cheese.value as? String, "Checked")
        cheese.tap()
        XCTAssertEqual(cheese.value as? String, "Unchecked")
        app.buttons["undo"].tap()
        XCTAssertEqual(cheese.value as? String, "Checked")
        app.buttons["Adjust portions"].tap()
        let multiplier = app.textFields["multiplier"]
        multiplier.tap()
        multiplier.typeText(XCUIKeyboardKey.delete.rawValue + "1.583945")
        app.buttons["Apply multiplier"].tap()
        XCTAssertTrue(app.staticTexts["1.583945× recipe"].waitForExistence(timeout: 5))
        app.buttons["portion-plus"].tap()
        XCTAssertTrue(app.staticTexts["2.583945× recipe"].waitForExistence(timeout: 5))
        app.buttons["portion-minus"].tap()
        XCTAssertTrue(app.staticTexts["1.583945× recipe"].waitForExistence(timeout: 5))
        app.terminate()
        app.launchArguments = ["--ui-testing"]
        app.launch()
        XCTAssertTrue(app.buttons["ingredient-1"].waitForExistence(timeout: 5))
        XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
        XCTAssertTrue(app.staticTexts["1.583945× recipe"].exists)
        app.buttons["History"].tap()
        XCTAssertTrue(app.staticTexts["Undo · Checked"].waitForExistence(timeout: 5))
    }
}
