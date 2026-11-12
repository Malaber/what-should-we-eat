import XCTest

final class OnionaryUITests: OnionaryUITestCase {
    @MainActor
    private static func relaunchPreservingData(_ app: XCUIApplication) -> XCUIApplication {
        let arguments = app.launchArguments.filter { $0 != "--reset" }
        let environment = app.launchEnvironment
        UIAppLifecycle.terminate()
        // XCUIApplication owns an automation connection/PID. A new object must
        // represent the new process; only the on-device data is reused.
        let relaunched = XCUIApplication()
        relaunched.launchArguments = arguments
        relaunched.launchEnvironment = environment
        relaunched.launch()
        XCTAssertTrue(relaunched.wait(for: .runningForeground, timeout: 10))
        return relaunched
    }

    @MainActor
    private func tapNavigation(_ title: String, in app: XCUIApplication) throws {
        let button = UIReadiness.button(title, in: app)
        XCTAssertTrue(button.waitForExistence(timeout: 5), "Missing tab: \(title)")
        XCTAssertTrue(button.isHittable, "Tab is not reachable: \(title)")
        button.tap()
    }

    @MainActor
    private func selectRecipe(_ id: Int = 1, in app: XCUIApplication) throws {
        let list = app.collectionViews["recipe-list"]
        // Cached rows remain usable during an expired/offline session. The exact
        // actionable row is the readiness condition, not a separate refresh RPC.
        let row = list.buttons.matching(identifier: "recipe-\(id)").element(boundBy: 0)
        XCTAssertTrue(row.waitForExistence(timeout: 5))
        XCTAssertTrue(row.isHittable, "Recipe row is not reachable: \(id)")
        row.tap()
    }

    @MainActor
    func testMultipleTagFilters() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "--marketing", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        app.buttons["category-Vegetarian"].tap()
        app.buttons["category-Quick & easy"].tap()
        XCTAssertEqual(app.buttons["category-Vegetarian"].value as? String, "Selected")
        XCTAssertEqual(app.buttons["category-Quick & easy"].value as? String, "Selected")
        app.buttons["All recipes"].tap()
        XCTAssertTrue(app.buttons["All recipes"].waitForNonExistence(timeout: 5))
    }

    @MainActor
    func testPantryMatchingQuantities() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "--marketing", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        app.buttons["Cook with what you have"].tap()
        // A multiline SwiftUI input may expose either text role. Resolve its
        // identifier directly instead of retaining an index from the sheet's
        // transient field list while it is still being presented.
        let textRoles = NSPredicate(format: "elementType IN %@", [XCUIElement.ElementType.textField.rawValue, XCUIElement.ElementType.textView.rawValue])
        let pantry = app.descendants(matching: .any).matching(textRoles)
            .matching(identifier: "pantry-input").element(boundBy: 0)
        XCTAssertTrue(pantry.waitForExistence(timeout: 5))
        pantry.tap()
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForExistence(timeout: 5))
        pantry.typeText("170 g Cheese")
        XCTAssertTrue(UIReadiness.waitForValue("170 g Cheese", in: pantry))
        XCTAssertEqual(pantry.value as? String, "170 g Cheese")
        let match = app.buttons["pantry-match-1"]
        XCTAssertTrue(match.waitForExistence(timeout: 5))
        XCTAssertTrue((match.value as? String ?? "").contains("Not enough: Cheese"))
        XCTAssertTrue((match.value as? String ?? "").contains("Missing: Pasta"))
        app.buttons["close-pantry"].tap()
        XCTAssertTrue(app.buttons["close-pantry"].waitForNonExistence(timeout: 5))
    }

    @MainActor
    func testIntelligenceModeAndLanguageOptions() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "--marketing", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        app.buttons["add-recipe"].tap()
        app.buttons["Create with Intelligence"].tap()
        XCTAssertTrue(app.staticTexts["Recipe mode"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["Recipe language"].exists)
        app.buttons["Cancel"].tap()
    }

    @MainActor
    func testAccountDeletionConfirmationAndSuccess() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Settings", in: app)
        app.swipeUp()
        app.buttons["delete-account"].tap()
        let confirm = app.buttons["confirm-delete-account"]
        XCTAssertFalse(confirm.isEnabled)
        let email = app.textFields["delete-account-email"]
        XCTAssertTrue(email.waitForExistence(timeout: 5))
        email.tap()
        XCTAssertTrue(app.keyboards.firstMatch.waitForExistence(timeout: 5), "Email entry requires keyboard focus")
        email.typeText("cook@example.org")
        XCTAssertEqual(email.value as? String, "cook@example.org")
        XCTAssertTrue(confirm.isEnabled)
        confirm.tap()
        XCTAssertTrue(app.alerts["Account deleted"].waitForExistence(timeout: 5))
        app.alerts.buttons["OK"].tap()
        XCTAssertTrue(app.textFields["backend"].waitForExistence(timeout: 5))
    }

    @MainActor
    func testAccountDeletionOfflineKeepsAccount() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "--offline-delete", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Settings", in: app)
        app.swipeUp()
        app.buttons["delete-account"].tap()
        let email = app.textFields["delete-account-email"]
        XCTAssertTrue(email.waitForExistence(timeout: 5))
        email.tap()
        XCTAssertTrue(app.keyboards.firstMatch.waitForExistence(timeout: 5), "Email entry requires keyboard focus")
        email.typeText("cook@example.org")
        XCTAssertEqual(email.value as? String, "cook@example.org")
        app.buttons["confirm-delete-account"].tap()
        XCTAssertTrue(app.staticTexts["delete-account-error"].waitForExistence(timeout: 5))
        XCTAssertEqual(email.value as? String, "cook@example.org")
        app.buttons["Cancel"].tap()
        XCTAssertTrue(app.buttons["delete-account"].exists)
    }

    @MainActor
    func testManualRecipeKeepsDraftWhenServerUnavailable() throws {
        var app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "--offline-save", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        app.buttons["add-recipe"].tap()
        app.buttons["New recipe"].tap()
        let name = app.textFields["Name"]
        XCTAssertTrue(name.waitForExistence(timeout: 5))
        name.tap(); name.typeText("My offline soup")
        app.buttons["Save"].tap()
        XCTAssertTrue(app.otherElements["recipe-save-error"].waitForExistence(timeout: 5) || app.staticTexts["recipe-save-error"].exists)
        XCTAssertEqual(name.value as? String, "My offline soup")
        XCTAssertTrue(app.buttons["Save"].isEnabled)
        app.buttons["Cancel"].tap()
        app = Self.relaunchPreservingData(app)
        try tapNavigation("Recipes", in: app)
        app.buttons["saved-draft-My offline soup"].firstMatch.tap()
        XCTAssertTrue(app.textFields["Name"].waitForExistence(timeout: 5))
        XCTAssertEqual(app.textFields["Name"].value as? String, "My offline soup")
    }

    @MainActor
    func testSilentRenewalPreservesCookingProgress() throws {
        var app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "--renew-session", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        app.buttons["Choose a recipe"].tap()
        try selectRecipe(in: app)
        XCTAssertTrue(app.buttons["preview-cook"].waitForExistence(timeout: 5))
        app.buttons["preview-cook"].tap()
        app.buttons["ingredient-1"].tap()
        app = Self.relaunchPreservingData(app)
        XCTAssertTrue(app.buttons["ingredient-1"].waitForExistence(timeout: 5))
        XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
        try tapNavigation("Settings", in: app)
        XCTAssertTrue(app.staticTexts["Access valid until"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["Account, Test Cook"].exists)
        XCTAssertTrue(app.staticTexts["Email, cook@example.org"].exists)
        XCTAssertFalse(app.buttons["Sign in with passkey"].exists)
    }

    @MainActor
    func testExpiredSessionLeavesCookingAvailable() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "--expired-session", "--test-passkey-success", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        XCTAssertTrue(app.buttons["Sign in with passkey"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["c***@example.org"].exists)
        XCTAssertFalse(app.alerts.firstMatch.exists)
        app.buttons["Choose a recipe"].tap()
        try selectRecipe(in: app)
        app.buttons["preview-cook"].tap()
        app.buttons["ingredient-1"].tap()
        XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
        XCTAssertTrue(app.buttons["Sign in with passkey"].exists)
        app.buttons["Sign in with passkey"].tap()
        XCTAssertTrue(app.buttons["Sign in with passkey"].waitForNonExistence(timeout: 5))
        XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
    }

    @MainActor
    func testReauthenticationRejectsDifferentAccount() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "--expired-session", "--test-passkey-wrong-account", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        XCTAssertTrue(app.buttons["Sign in with passkey"].waitForExistence(timeout: 5))
        app.buttons["Sign in with passkey"].tap()
        XCTAssertTrue(app.staticTexts["Use the same account to reconnect. Your current kitchen has not changed."].waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["Choose a recipe"].exists)
    }

    @MainActor
    private func pullToRefresh(_ app: XCUIApplication) {
        let list = app.collectionViews["recipe-list"]
        XCTAssertTrue(list.waitForExistence(timeout: 5))
        // Gesture belongs to the list; pressing a row can select/drag the recipe
        // and leave the split-view preview transitioning during the next query.
        list.swipeDown(velocity: .slow)
        let settled = XCTNSPredicateExpectation(predicate: NSPredicate(format: "value == %@", "Recipes loaded"), object: list)
        XCTAssertEqual(XCTWaiter.wait(for: [settled], timeout: 5), .completed)
    }

    @MainActor
    func testCategoryBrowsingAndIngredientSearch() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        pullToRefresh(app)
        let category = app.buttons["category-vegetarian"]
        XCTAssertTrue(category.waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["browse-tags"].exists)
        XCTAssertFalse(app.buttons["Refresh"].exists)
        XCTAssertTrue(app.buttons["sort-recipes"].exists)
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
    func testLiveActivityStartAndStop() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        app.buttons["Choose a recipe"].tap()
        try selectRecipe(in: app)
        app.buttons["preview-cook"].tap()
        let mode = app.buttons["cooking-mode"]
        XCTAssertTrue(mode.waitForExistence(timeout: 5))
        app.buttons["portion-plus"].tap()
        XCTAssertTrue(app.staticTexts["2× recipe"].waitForExistence(timeout: 5), "The first portion tap must update the recipe before starting its activity")
        let on = NSPredicate(format: "value == %@", "On")
        let off = NSPredicate(format: "value == %@", "Off")
        expectation(for: on, evaluatedWith: mode)
        waitForExpectations(timeout: 5)
        mode.tap()
        expectation(for: off, evaluatedWith: mode)
        waitForExpectations(timeout: 5)
        app.buttons["portion-plus"].tap()
        XCTAssertEqual(mode.value as? String, "Off")
        mode.tap()
        expectation(for: on, evaluatedWith: mode)
        waitForExpectations(timeout: 5)
        mode.tap()
        expectation(for: off, evaluatedWith: mode)
        waitForExpectations(timeout: 5)
    }

    @MainActor
    func testRecipeTagsOpenMatchingRecipes() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        pullToRefresh(app)
        try selectRecipe(in: app)
        app.buttons["preview-cook"].tap()
        let tag = app.buttons["recipe-tag-vegetarian"]
        XCTAssertTrue(tag.waitForExistence(timeout: 5))
        tag.tap()
        let matchingRecipe = app.buttons["tag-recipe-1"]
        XCTAssertTrue(matchingRecipe.waitForExistence(timeout: 5))
        app.buttons["Done"].tap()
        XCTAssertTrue(tag.waitForExistence(timeout: 5))
        tag.tap()
        XCTAssertTrue(matchingRecipe.waitForExistence(timeout: 5))
        matchingRecipe.tap()
        XCTAssertTrue(app.buttons["Cooking options"].waitForExistence(timeout: 5))
    }

    @MainActor
    func testStepAmountTools() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        try selectRecipe(in: app)
        app.buttons["preview-cook"].tap()
        XCTAssertTrue(app.buttons["Cooking options"].waitForExistence(timeout: 5))
        app.buttons["Cooking options"].tap()
        app.buttons["Edit recipe"].tap()
        XCTAssertTrue(app.textFields["Name"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["insert-ingredient-amount"].exists)
        app.swipeUp()
        app.swipeUp()
        let instruction = app.textFields.matching(NSPredicate(format: "identifier BEGINSWITH %@", "instruction-")).firstMatch
        XCTAssertTrue(instruction.waitForExistence(timeout: 5))
        instruction.tap()
        let insert = app.buttons["insert-ingredient-amount"]
        XCTAssertTrue(insert.waitForExistence(timeout: 5))
        insert.tap()
        app.buttons["Cheese"].tap()
        XCTAssertTrue((instruction.value as? String ?? "").contains("{{Cheese|100%}}"))
        app.buttons["Done"].tap()
        XCTAssertFalse(insert.exists)
        app.buttons["step-help"].tap()
        XCTAssertTrue(app.alerts["Ingredient amount help"].waitForExistence(timeout: 5))
        app.alerts.buttons["Done"].tap()
        app.buttons["Cancel"].tap()
    }

    @MainActor
    func testKitchenPlanAndOpenRecipe() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Kitchen", in: app)
        app.buttons["Add meals"].tap()
        app.buttons["Lemon & cheese pasta"].tap()
        app.buttons["Add"].tap()
        XCTAssertTrue(app.buttons["Mark cooked"].waitForExistence(timeout: 5))
        app.buttons["Mark cooked"].tap()
        XCTAssertTrue(app.buttons["Mark uncooked"].waitForExistence(timeout: 5))
        app.buttons["Lemon & cheese pasta"].tap()
        XCTAssertTrue(app.buttons["Cooking options"].waitForExistence(timeout: 5))
    }

    @MainActor
    func testEditRecipeKeepsCookingProgress() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        app.buttons["Choose a recipe"].tap()
        try selectRecipe(in: app)
        app.buttons["preview-cook"].tap()
        let checkedIngredient = app.buttons["ingredient-1"]
        XCTAssertTrue(checkedIngredient.waitForExistence(timeout: 5))
        checkedIngredient.tap()
        XCTAssertEqual(checkedIngredient.value as? String, "Checked")
        XCTAssertTrue(app.buttons["Cooking options"].waitForExistence(timeout: 5))
        app.buttons["Cooking options"].tap()
        app.buttons["Edit recipe"].tap()
        let name = app.textFields["Name"]
        XCTAssertTrue(name.waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["Total minutes"].exists)
        XCTAssertTrue(app.staticTexts["Active minutes"].exists)
        XCTAssertTrue(app.staticTexts["Calories per serving"].exists)
        name.tap()
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForExistence(timeout: 5))
        let oldName = name.value as? String ?? ""
        name.typeText(String(repeating: XCUIKeyboardKey.delete.rawValue, count: oldName.count) + "Edited pasta")
        XCTAssertTrue(UIReadiness.waitForValue("Edited pasta", in: name))
        XCTAssertEqual(name.value as? String, "Edited pasta")
        app.buttons["Save"].tap()
        // Resolve the actual presented alert, not an app-wide button during
        // the editor/keyboard presentation transition.
        let reloadAlert = app.alerts["Reload cooking recipe?"]
        let keepProgress = reloadAlert.buttons["Keep cooking progress"]
        XCTAssertTrue(keepProgress.waitForExistence(timeout: 5))
        keepProgress.tap()
        XCTAssertTrue(reloadAlert.waitForNonExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["Lemon & cheese pasta"].waitForExistence(timeout: 5))
        XCTAssertEqual(checkedIngredient.value as? String, "Checked")
        try tapNavigation("Recipes", in: app)
        XCTAssertTrue(app.staticTexts["Edited pasta"].waitForExistence(timeout: 5))
    }

    @MainActor
    func testShareRecipeCopyAndRevokeLink() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        app.buttons["Choose a recipe"].tap()
        try selectRecipe(in: app)
        app.buttons["preview-cook"].tap()
        XCTAssertTrue(app.buttons["Cooking options"].waitForExistence(timeout: 5))
        app.buttons["Cooking options"].tap()
        app.buttons["Share recipe copy"].tap()
        let createLink = app.buttons["create-recipe-share"]
        XCTAssertTrue(createLink.waitForExistence(timeout: 5))
        XCTAssertTrue(createLink.isHittable)
        createLink.tap()
        let revoke = app.buttons["revoke-recipe-share"]
        XCTAssertTrue(revoke.waitForExistence(timeout: 5))
        XCTAssertTrue(revoke.isHittable)
        revoke.tap()
        XCTAssertTrue(revoke.waitForNonExistence(timeout: 5), "Successful revocation dismisses the sheet")
    }

    @MainActor
    func testImportRecipePreview() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        app.buttons["add-recipe"].tap()
        app.buttons["Import recipe"].tap()
        XCTAssertTrue(app.textFields["Chefkoch or Onionary URL"].waitForExistence(timeout: 5))
        app.textFields["Chefkoch or Onionary URL"].tap()
        app.textFields["Chefkoch or Onionary URL"].typeText("https://www.chefkoch.de/rezepte/123")
        app.buttons["Review recipe"].tap()
        XCTAssertTrue(app.textFields["Name"].waitForExistence(timeout: 5))
        app.buttons["Cancel"].tap()
    }

    @MainActor
    func testIntelligenceDraftRequiresUserInput() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        app.buttons["add-recipe"].tap()
        app.buttons["Create with Intelligence"].tap()
        XCTAssertTrue(app.textViews["Describe your recipe"].waitForExistence(timeout: 5))
        let create = app.buttons["Create recipe draft"]
        let form = app.collectionViews.firstMatch
        // This button follows the mode, language and availability explanation.
        for _ in 0..<4 {
            if create.exists && create.isHittable { break }
            form.swipeUp()
        }
        XCTAssertTrue(create.exists)
        XCTAssertFalse(create.isEnabled)
        app.buttons["Cancel"].tap()
        XCTAssertTrue(app.navigationBars["Recipe book"].exists)
    }

    @MainActor
    func testNativeSettingsLanguageAndAppearance() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Settings", in: app)
        XCTAssertTrue(app.buttons["Switch backend"].exists)
        XCTAssertFalse(app.textFields["backend"].exists)
        app.buttons["language-picker"].tap()
        app.buttons["Deutsch"].tap()
        XCTAssertTrue(app.navigationBars["Einstellungen"].waitForExistence(timeout: 5))
        let german = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        german.name = "validation-settings-german"; german.lifetime = .keepAlways; add(german)
        app.buttons["appearance-picker"].tap()
        app.buttons["Dunkel"].tap()
        XCTAssertEqual(app.buttons["appearance-picker"].value as? String, "Dunkel")
        app.buttons["language-picker"].tap()
        app.buttons["Englisch"].tap()
        XCTAssertTrue(app.navigationBars["Settings"].waitForExistence(timeout: 5))
    }

    @MainActor
    func testMarketingScreenshots() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "--marketing", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Settings", in: app)
        XCTAssertEqual(app.buttons["appearance-picker"].value as? String, "Light")
        try tapNavigation("Cooking", in: app)
        app.buttons["Choose a recipe"].tap()
        capture("01-recipe-book")
        try selectRecipe(in: app)
        app.buttons["preview-cook"].tap()
        XCTAssertTrue(app.buttons["ingredient-1"].waitForExistence(timeout: 5))
        app.buttons["ingredient-1"].tap()
        app.buttons["ingredient-2"].tap()
        app.buttons["undo"].tap()
        app.buttons["redo"].tap()
        app.buttons["ingredient-1"].tap()
        app.buttons["ingredient-1"].tap()
        XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
        // Capture stable content after the transient action banner has dismissed.
        expectation(for: NSPredicate(format: "exists == false"), evaluatedWith: app.staticTexts["recent-action"])
        waitForExpectations(timeout: 8)
        capture("02-cooking-companion")
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
    func testPortionButtonsWithoutKeyboard() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        app.buttons["Choose a recipe"].tap()
        try selectRecipe(in: app)
        app.buttons["preview-cook"].tap()
        XCTAssertTrue(app.buttons["portion-plus"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.keyboards.firstMatch.exists)
        app.buttons["portion-plus"].tap()
        XCTAssertTrue(app.staticTexts["2× recipe"].waitForExistence(timeout: 5))
        app.buttons["portion-minus"].tap()
        XCTAssertTrue(app.staticTexts["1× recipe"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["portion-minus"].isEnabled)
    }

    @MainActor
    func testCookUndoScaleAndRestoreAfterTermination() throws {
        var app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        app.buttons["Choose a recipe"].tap()
        try selectRecipe(in: app)
        app.buttons["preview-cook"].tap()
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
        app = Self.relaunchPreservingData(app)
        XCTAssertTrue(app.buttons["ingredient-1"].waitForExistence(timeout: 5))
        XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
        XCTAssertTrue(app.staticTexts["1.58× recipe"].exists)
        app.buttons["History"].tap()
        XCTAssertTrue(app.staticTexts["Undo · Checked"].waitForExistence(timeout: 5))
    }
}
