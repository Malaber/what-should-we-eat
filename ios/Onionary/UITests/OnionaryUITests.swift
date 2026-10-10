import XCTest

final class OnionaryUITests: XCTestCase {
    @MainActor
    func testCategoryBrowsingAndIngredientSearch() {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        app.tabBars.buttons["Recipes"].tap()
        app.buttons["Refresh"].tap()
        let category = app.buttons["category-vegetarian"]
        XCTAssertTrue(category.waitForExistence(timeout: 5))
        category.tap()
        XCTAssertTrue(app.buttons["All recipes"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["recipe-1"].exists)
        app.buttons["All recipes"].tap()
        let search = app.searchFields.firstMatch
        search.tap()
        search.typeText("Cheese")
        XCTAssertTrue(app.buttons["recipe-1"].waitForExistence(timeout: 5))
        search.typeText(" nonexistent")
        XCTAssertTrue(app.staticTexts["No matching recipes"].waitForExistence(timeout: 5))
    }

    @MainActor
    func testLiveActivityStartAndStop() {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        app.buttons["Choose a recipe"].tap()
        app.buttons["recipe-1"].firstMatch.tap()
        app.buttons["Cooking options"].tap()
        app.buttons["Start Live Activity"].tap()
        app.buttons["Cooking options"].tap()
        XCTAssertTrue(app.buttons["Stop Live Activity"].waitForExistence(timeout: 5))
        app.buttons["Stop Live Activity"].tap()
        app.buttons["Cooking options"].tap()
        XCTAssertTrue(app.buttons["Start Live Activity"].waitForExistence(timeout: 5))
    }

    @MainActor
    func testKitchenEditAndImport() {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        app.tabBars.buttons["Kitchen"].tap()
        app.buttons["Add meals"].tap()
        app.buttons["Lemon & cheese pasta"].tap()
        app.buttons["Add"].tap()
        XCTAssertTrue(app.buttons["Mark cooked"].waitForExistence(timeout: 5))
        app.buttons["Mark cooked"].tap()
        XCTAssertTrue(app.buttons["Mark uncooked"].waitForExistence(timeout: 5))
        app.buttons["Lemon & cheese pasta"].tap()
        app.buttons["Cooking options"].tap()
        app.buttons["Edit recipe"].tap()
        let name = app.textFields["Name"]
        XCTAssertTrue(name.waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["Total minutes"].exists)
        XCTAssertTrue(app.staticTexts["Active minutes"].exists)
        XCTAssertTrue(app.staticTexts["Calories per serving"].exists)
        name.tap()
        let oldName = name.value as? String ?? ""
        name.typeText(String(repeating: XCUIKeyboardKey.delete.rawValue, count: oldName.count) + "Edited pasta")
        app.buttons["Save"].tap()
        XCTAssertTrue(app.staticTexts["Lemon & cheese pasta"].waitForExistence(timeout: 5))
        app.buttons["Cooking options"].tap()
        app.buttons["Share recipe copy"].tap()
        app.buttons["Create link"].tap()
        XCTAssertTrue(app.buttons["Revoke link"].waitForExistence(timeout: 5))
        app.buttons["Revoke link"].tap()
        app.tabBars.buttons["Recipes"].tap()
        XCTAssertTrue(app.staticTexts["Edited pasta"].waitForExistence(timeout: 5))
        app.buttons["Import recipe"].tap()
        app.textFields["Chefkoch or Onionary URL"].tap()
        app.textFields["Chefkoch or Onionary URL"].typeText("https://www.chefkoch.de/rezepte/123")
        app.buttons["Review recipe"].tap()
        XCTAssertTrue(app.textFields["Name"].waitForExistence(timeout: 5))
        app.buttons["Cancel"].tap()
    }

    @MainActor
    func testIntelligenceDraftRequiresUserInput() {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        app.tabBars.buttons["Recipes"].tap()
        app.buttons["Create with Intelligence"].tap()
        XCTAssertTrue(app.textViews["Describe your recipe"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["Create recipe draft"].isEnabled)
        app.buttons["Cancel"].tap()
        XCTAssertTrue(app.navigationBars["Recipe book"].exists)
    }

    @MainActor
    func testNativeSettingsLanguageAndAppearance() {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        app.tabBars.buttons["Settings"].tap()
        XCTAssertTrue(app.buttons["Switch backend"].exists)
        XCTAssertFalse(app.textFields["backend"].exists)
        app.buttons["language-picker"].tap()
        app.buttons["Deutsch"].tap()
        XCTAssertTrue(app.navigationBars["Einstellungen"].waitForExistence(timeout: 5))
        let german = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        german.name = "validation-settings-german"; german.lifetime = .keepAlways; add(german)
        app.buttons["appearance-picker"].tap()
        app.buttons["Dunkel"].tap()
        app.buttons["language-picker"].tap()
        app.buttons["Englisch"].tap()
        XCTAssertTrue(app.navigationBars["Settings"].waitForExistence(timeout: 5))
    }

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
        XCTAssertTrue(app.textFields["portions"].waitForExistence(timeout: 5))
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
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
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
        app.buttons["redo"].tap()
        XCTAssertEqual(cheese.value as? String, "Unchecked")
        app.buttons["undo"].tap()
        XCTAssertEqual(cheese.value as? String, "Checked")
        app.buttons["Adjust portions"].tap()
        XCTAssertTrue(app.staticTexts["Your ingredients right now"].exists)
        let multiplier = app.textFields["portions"]
        multiplier.tap()
        XCTAssertTrue(app.keyboards.firstMatch.waitForExistence(timeout: 5), "Portion field must open the keyboard before testing dismissal")
        multiplier.typeText(XCUIKeyboardKey.delete.rawValue + "1.583945")
        app.staticTexts["By portions"].tap()
        XCTAssertTrue(app.keyboards.firstMatch.waitForNonExistence(timeout: 5), "Outside tap must dismiss the keyboard")
        app.buttons["Done"].firstMatch.tap()
        XCTAssertTrue(app.staticTexts["1.58× recipe"].waitForExistence(timeout: 5), app.debugDescription)
        app.buttons["portion-plus"].tap()
        XCTAssertTrue(app.staticTexts["2.58× recipe"].waitForExistence(timeout: 5))
        app.buttons["portion-minus"].tap()
        XCTAssertTrue(app.staticTexts["1.58× recipe"].waitForExistence(timeout: 5), app.debugDescription)
        app.terminate()
        app.launchArguments = ["--ui-testing", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        XCTAssertTrue(app.buttons["ingredient-1"].waitForExistence(timeout: 5))
        XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
        XCTAssertTrue(app.staticTexts["1.58× recipe"].exists)
        app.buttons["History"].tap()
        XCTAssertTrue(app.staticTexts["Undo · Checked"].waitForExistence(timeout: 5))
    }
}
