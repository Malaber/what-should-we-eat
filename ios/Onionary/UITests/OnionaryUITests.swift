import XCTest
import notify

final class OnionaryUITests: OnionaryUITestCase {
    @MainActor
    private static func relaunchPreservingData(_ app: XCUIApplication) {
        app.launchArguments.removeAll { $0 == "--reset" }
        // XCTest's launch terminates the running instance and starts a clean
        // process. Let it own both sides of this transition instead of issuing
        // separate Home, terminate and launch requests to the simulator.
        app.launch()
    }

    @MainActor
    private func tapNavigation(_ title: String, in app: XCUIApplication) throws {
        let button = UIReadiness.button(title, in: app)
        XCTAssertTrue(button.waitForExistence(timeout: 5), "Missing tab: \(title)")
        button.tap()
    }

    @MainActor
    private func selectRecipe(_ id: Int = 1, in app: XCUIApplication) throws {
        let list = app.collectionViews["recipe-list"]
        // Cached rows remain usable during an expired/offline session. The exact
        // actionable row is the readiness condition, not a separate refresh RPC.
        let row = list.buttons.matching(identifier: "recipe-\(id)").element(boundBy: 0)
        XCTAssertTrue(row.waitForExistence(timeout: 5))
        row.tap()
    }

    @MainActor
    private func dismissIntelligence(in app: XCUIApplication) {
        let cancel = app.navigationBars["Create with Intelligence"].buttons
            .matching(identifier: "cancel-intelligence").element(boundBy: 0)
        XCTAssertTrue(cancel.waitForExistence(timeout: 5))
        cancel.tap()
        XCTAssertTrue(app.collectionViews["intelligence-form"].waitForNonExistence(timeout: 5))
        XCTAssertTrue(app.navigationBars["Recipe book"].waitForExistence(timeout: 5))
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
        app.buttons["clear-tag-filter"].tap()
        XCTAssertTrue(app.buttons["clear-tag-filter"].waitForNonExistence(timeout: 5))
        XCTAssertEqual(app.buttons["category-Vegetarian"].value as? String, "Not selected")
        XCTAssertEqual(app.buttons["category-Quick & easy"].value as? String, "Not selected")
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
        let pantryFields = app.descendants(matching: .any).matching(textRoles)
            .matching(identifier: "pantry-input")
        let pantry = pantryFields.element(boundBy: 0)
        XCTAssertTrue(pantry.waitForExistence(timeout: 5))
        pantry.tap()
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForExistence(timeout: 5))
        app.typeText("170 g Cheese")
        XCTAssertTrue(UIReadiness.waitForValue("170 g Cheese", matching: pantryFields))
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
        let form = app.collectionViews["intelligence-form"]
        XCTAssertTrue(form.waitForExistence(timeout: 5))
        XCTAssertTrue(form.staticTexts["Recipe mode"].waitForExistence(timeout: 5))
        XCTAssertTrue(form.staticTexts["Recipe language"].exists)
        dismissIntelligence(in: app)
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
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForExistence(timeout: 5), "Email entry requires keyboard focus")
        app.typeText("cook@example.org")
        XCTAssertTrue(UIReadiness.waitForValue("cook@example.org", matching: app.textFields.matching(identifier: "delete-account-email")))
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
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForExistence(timeout: 5), "Email entry requires keyboard focus")
        app.typeText("cook@example.org")
        XCTAssertTrue(UIReadiness.waitForValue("cook@example.org", matching: app.textFields.matching(identifier: "delete-account-email")))
        XCTAssertEqual(email.value as? String, "cook@example.org")
        app.buttons["confirm-delete-account"].tap()
        XCTAssertTrue(app.staticTexts["delete-account-error"].waitForExistence(timeout: 5))
        XCTAssertEqual(email.value as? String, "cook@example.org")
        app.buttons["Cancel"].tap()
        XCTAssertTrue(app.buttons["delete-account"].exists)
    }

    @MainActor
    func testManualRecipeKeepsDraftWhenServerUnavailable() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "--offline-save", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        app.buttons["add-recipe"].tap()
        app.buttons["New recipe"].tap()
        let name = app.textFields["Name"]
        XCTAssertTrue(name.waitForExistence(timeout: 5))
        name.tap()
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForExistence(timeout: 5))
        app.typeText("My offline soup")
        XCTAssertTrue(UIReadiness.waitForValue("My offline soup", matching: app.textFields.matching(identifier: "Name")))
        app.buttons["Save"].tap()
        XCTAssertTrue(app.staticTexts["recipe-save-error"].waitForExistence(timeout: 5))
        XCTAssertTrue(UIReadiness.waitForValue("My offline soup", matching: app.textFields.matching(identifier: "Name")), "Failed save must retain the complete draft name")
        XCTAssertTrue(app.buttons["Save"].isEnabled)
        app.buttons["Cancel"].tap()
        // Finish dismissal/persistence before the real cold restart.
        XCTAssertTrue(name.waitForNonExistence(timeout: 5))
        XCTAssertTrue(app.collectionViews["recipe-list"].buttons.matching(identifier: "saved-draft-My offline soup").element(boundBy: 0).waitForExistence(timeout: 5))
        Self.relaunchPreservingData(app)
        try tapNavigation("Recipes", in: app)
        let saved = app.collectionViews["recipe-list"].buttons.matching(identifier: "saved-draft-My offline soup").element(boundBy: 0)
        XCTAssertTrue(saved.waitForExistence(timeout: 5))
        saved.tap()
        // One native query checks both existence and exact restored text.
        XCTAssertTrue(UIReadiness.waitForValue("My offline soup", matching: app.textFields.matching(identifier: "Name")), "Cold restoration must retain the complete draft name")
    }

    @MainActor
    func testRecipeTagSuggestionsAndMultiwordChips() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "--marketing", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        app.buttons["add-recipe"].tap()
        app.buttons["New recipe"].tap()
        let editor = app.otherElements["recipe-editor"]
        let tag = app.textFields["recipe-tag-input"]
        XCTAssertTrue(tag.waitForExistence(timeout: 5))
        if !tag.isHittable { editor.swipeUp() }
        tag.tap()
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForExistence(timeout: 5))
        app.typeText("Quick")
        let suggestion = app.buttons["suggest-recipe-tag-Quick & easy"]
        XCTAssertTrue(suggestion.waitForExistence(timeout: 5))
        suggestion.tap()
        XCTAssertTrue(app.buttons["remove-tag-Quick & easy"].waitForExistence(timeout: 5))

        tag.tap()
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForExistence(timeout: 5))
        app.typeText("Weeknight meals")
        XCTAssertTrue(UIReadiness.waitForValue("Weeknight meals", matching: app.textFields.matching(identifier: "recipe-tag-input")))
        app.buttons["add-recipe-tag"].tap()
        let custom = app.buttons["remove-tag-Weeknight meals"]
        XCTAssertTrue(custom.waitForExistence(timeout: 5))
        custom.tap()
        XCTAssertTrue(custom.waitForNonExistence(timeout: 5))
        XCTAssertTrue(app.buttons["remove-tag-Quick & easy"].exists)
    }

    @MainActor
    func testSilentRenewalPreservesCookingProgress() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "--renew-session", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        app.buttons["Choose a recipe"].tap()
        try selectRecipe(in: app)
        XCTAssertTrue(app.buttons["preview-cook"].waitForExistence(timeout: 5))
        app.buttons["preview-cook"].tap()
        app.buttons["ingredient-1"].tap()
        XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
        // Expire access while the real app is backgrounded, then let its normal
        // foreground refresh renew it. Full cold restoration has its own case.
        UIAppLifecycle.background()
        app.activate()
        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))
        XCTAssertTrue(app.buttons["ingredient-1"].waitForExistence(timeout: 5))
        XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
        try tapNavigation("Settings", in: app)
        XCTAssertTrue(app.staticTexts["Access valid until"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["Account, Test Cook"].exists)
        XCTAssertTrue(app.staticTexts["Email, cook@example.org"].exists)
        XCTAssertFalse(app.buttons["Sign in with passkey"].exists)
        try tapNavigation("Cooking", in: app)
        XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
    }

    @MainActor
    func testExpiredSessionLeavesCookingAvailable() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "--expired-session", "--test-passkey-success", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        XCTAssertTrue(app.buttons["Sign in with passkey"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["c***@example.org"].exists)
        XCTAssertFalse(app.alerts.element(boundBy: 0).exists)
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
        XCTAssertTrue(UIReadiness.waitForValue("Recipes loaded", matching: app.collectionViews.matching(identifier: "recipe-list")))
        XCTAssertEqual(list.value as? String, "Recipes loaded")
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
        XCTAssertTrue(app.buttons["clear-tag-filter"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["recipe-1"].exists)
        app.buttons["clear-tag-filter"].tap()
        let search = app.searchFields.element(boundBy: 0)
        search.tap()
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForExistence(timeout: 5))
        app.typeText("Cheese")
        XCTAssertTrue(UIReadiness.waitForValue("Cheese", matching: app.searchFields))
        XCTAssertTrue(app.buttons["recipe-1"].waitForExistence(timeout: 5))
        app.typeText(" nonexistent")
        XCTAssertTrue(UIReadiness.waitForValue("Cheese nonexistent", matching: app.searchFields))
        XCTAssertTrue(app.staticTexts["No matching recipes"].waitForExistence(timeout: 5))
    }

    @MainActor
    func testLiveActivityStartAndStop() throws {
        try assertCookingModeCycle(systemActivityKit: true)
    }

    @MainActor
    func testCookingModeWithFixtureBackend() throws {
        try assertCookingModeCycle(systemActivityKit: false)
    }

    @MainActor
    private func assertCookingModeCycle(systemActivityKit: Bool) throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        if systemActivityKit { app.launchArguments.append("--system-live-activity") }
        app.launch()
        app.buttons["Choose a recipe"].tap()
        try selectRecipe(in: app)
        app.buttons["preview-cook"].tap()
        let modes = app.buttons.matching(identifier: "cooking-mode")
        let mode = modes.element(boundBy: 0)
        XCTAssertTrue(mode.waitForExistence(timeout: 5))
        app.buttons["portion-plus"].tap()
        XCTAssertTrue(app.staticTexts["2× recipe"].waitForExistence(timeout: 5), "The first portion tap must update the recipe before starting its activity")
        XCTAssertTrue(UIReadiness.waitForValue("On", matching: modes))
        XCTAssertEqual(mode.value as? String, "On")
        mode.tap()
        XCTAssertTrue(UIReadiness.waitForValue("Off", matching: modes))
        XCTAssertEqual(mode.value as? String, "Off")
        app.buttons["portion-plus"].tap()
        XCTAssertEqual(mode.value as? String, "Off")
        mode.tap()
        XCTAssertTrue(UIReadiness.waitForValue("On", matching: modes))
        XCTAssertEqual(mode.value as? String, "On")
        mode.tap()
        XCTAssertTrue(UIReadiness.waitForValue("Off", matching: modes))
        XCTAssertEqual(mode.value as? String, "Off")
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
        let matchingRecipe = app.collectionViews["tag-recipes-list"].buttons.matching(identifier: "tag-recipe-1").element(boundBy: 0)
        XCTAssertTrue(matchingRecipe.waitForExistence(timeout: 5))
        app.buttons["close-tag-recipes"].tap()
        XCTAssertTrue(app.collectionViews["tag-recipes-list"].waitForNonExistence(timeout: 5))
        // SwiftUI recreates controls across sheet presentations. Resolve each
        // presentation directly instead of keeping the old remote AX handle.
        let reopenedTag = app.buttons.matching(identifier: "recipe-tag-vegetarian").element(boundBy: 0)
        XCTAssertTrue(reopenedTag.waitForExistence(timeout: 5))
        reopenedTag.tap()
        let reopenedRecipe = app.collectionViews["tag-recipes-list"].buttons.matching(identifier: "tag-recipe-1").element(boundBy: 0)
        XCTAssertTrue(reopenedRecipe.waitForExistence(timeout: 5))
        reopenedRecipe.tap()
        XCTAssertTrue(app.collectionViews["tag-recipes-list"].waitForNonExistence(timeout: 5))
        XCTAssertTrue(app.buttons["Cooking options"].waitForExistence(timeout: 5))
    }

    @MainActor
    private func openStepEditor() throws -> XCUIApplication {
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
        return app
    }

    @MainActor
    func testStepAmountTools() throws {
        let app = try openStepEditor()
        let instruction = app.textFields.matching(NSPredicate(format: "identifier BEGINSWITH %@", "instruction-")).element(boundBy: 0)
        XCTAssertTrue(instruction.waitForExistence(timeout: 5))
        instruction.tap()
        let insert = app.buttons["insert-ingredient-amount"]
        XCTAssertTrue(insert.waitForExistence(timeout: 5))
        insert.tap()
        app.buttons["Cheese"].tap()
        XCTAssertTrue((instruction.value as? String ?? "").contains("{{Cheese|100%}}"))
        app.buttons["Done"].tap()
        XCTAssertFalse(insert.exists)
        app.buttons["Cancel"].tap()
        XCTAssertTrue(app.textFields["Name"].waitForNonExistence(timeout: 5))
    }

    @MainActor
    func testStepHelpWithoutKeyboard() throws {
        let app = try openStepEditor()
        let help = app.buttons["step-help"]
        XCTAssertTrue(help.waitForExistence(timeout: 5))
        help.tap()
        let alert = app.alerts["Ingredient amount help"]
        XCTAssertTrue(alert.waitForExistence(timeout: 5))
        alert.buttons["Done"].tap()
        XCTAssertTrue(alert.waitForNonExistence(timeout: 5))
        XCTAssertFalse(app.buttons["insert-ingredient-amount"].exists)
        app.buttons["Cancel"].tap()
        XCTAssertTrue(app.textFields["Name"].waitForNonExistence(timeout: 5))
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
        let oldName = try XCTUnwrap(name.value as? String)
        name.tap()
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForExistence(timeout: 5))
        // Focus was established by the real field tap above. Dispatch keys to
        // its containing app instead of resolving the field again while the
        // keyboard's remote accessibility process is transitioning.
        app.typeText(String(repeating: XCUIKeyboardKey.delete.rawValue, count: oldName.count) + "Edited pasta")
        XCTAssertTrue(UIReadiness.waitForValue("Edited pasta", matching: app.textFields.matching(identifier: "Name")))
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
    func testCookingOptionsSurviveActionFeedbackExpiry() throws {
        let clock = "de.malaber.onionary.uitest.feedback." + UUID().uuidString
        let app = try openCookingRecipe(environment: ["ONIONARY_TEST_FEEDBACK_CLOCK": clock])
        let ingredient = app.buttons["ingredient-1"]
        ingredient.tap()
        XCTAssertEqual(ingredient.value as? String, "Checked")
        let feedback = app.staticTexts["recent-action"]
        XCTAssertTrue(feedback.waitForExistence(timeout: 5))
        app.buttons["cooking-options"].tap()
        let edit = app.buttons["Edit recipe"]
        XCTAssertTrue(edit.waitForExistence(timeout: 5))
        // Expire the real feedback while the native menu is open. Accessibility
        // round trips must not race a four-second clock on a loaded CI host.
        XCTAssertEqual(notify_post(clock), UInt32(NOTIFY_STATUS_OK))
        XCTAssertTrue(feedback.waitForNonExistence(timeout: 8))
        XCTAssertTrue(edit.exists)
        edit.tap()
        let name = app.textFields["Name"]
        XCTAssertTrue(name.waitForExistence(timeout: 5))
        app.buttons["Cancel"].tap()
        XCTAssertTrue(name.waitForNonExistence(timeout: 5))
        XCTAssertTrue(app.buttons["cooking-options"].waitForExistence(timeout: 5))
        XCTAssertEqual(ingredient.value as? String, "Checked")
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
        createLink.tap()
        let revoke = app.buttons["revoke-recipe-share"]
        XCTAssertTrue(revoke.waitForExistence(timeout: 5))
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
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForExistence(timeout: 5))
        app.typeText("https://www.chefkoch.de/rezepte/123")
        XCTAssertTrue(UIReadiness.waitForValue("https://www.chefkoch.de/rezepte/123", matching: app.textFields.matching(identifier: "Chefkoch or Onionary URL")))
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
        let form = app.collectionViews["intelligence-form"]
        XCTAssertTrue(form.waitForExistence(timeout: 5))
        let create = form.buttons.matching(identifier: "Create recipe draft").element(boundBy: 0)
        // This button follows the mode, language and availability explanation.
        for _ in 0..<4 {
            if create.exists { break }
            form.swipeUp()
        }
        XCTAssertTrue(create.waitForExistence(timeout: 5))
        XCTAssertFalse(create.isEnabled)
        dismissIntelligence(in: app)
    }

    @MainActor
    func testNativeSettingsLanguageAndAppearance() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Settings", in: app)
        XCTAssertTrue(app.buttons["Switch backend"].exists)
        XCTAssertFalse(app.textFields["backend"].exists)
        app.buttons["accent-picker"].tap()
        let ocean = app.buttons["accent-Ocean"]
        XCTAssertTrue(ocean.waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["accent-Onion"].isSelected)
        ocean.tap()
        XCTAssertTrue(ocean.isSelected)
        XCTAssertFalse(app.buttons["accent-Onion"].isSelected)
        app.navigationBars["Accent color"].buttons["Settings"].tap()
        app.buttons["language-picker"].tap()
        app.buttons["Deutsch"].tap()
        XCTAssertTrue(app.navigationBars["Einstellungen"].waitForExistence(timeout: 5))
        let german = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        german.name = "validation-settings-german"; german.lifetime = .keepAlways; add(german)
        app.buttons["appearance-picker"].tap()
        app.buttons["Dunkel"].tap()
        XCTAssertTrue(UIReadiness.waitForValue("Dunkel", matching: app.buttons.matching(identifier: "appearance-picker")))
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
        XCTAssertTrue(app.staticTexts["recent-action"].waitForNonExistence(timeout: 8))
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
        XCTAssertFalse(app.keyboards.element(boundBy: 0).exists)
        app.buttons["portion-plus"].tap()
        XCTAssertTrue(app.staticTexts["2× recipe"].waitForExistence(timeout: 5))
        app.buttons["portion-minus"].tap()
        XCTAssertTrue(app.staticTexts["1× recipe"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["portion-minus"].isEnabled)
    }

    @MainActor
    private func openCookingRecipe(environment: [String: String] = [:]) throws -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launchEnvironment = environment
        app.launch()
        app.buttons["Choose a recipe"].tap()
        try selectRecipe(in: app)
        app.buttons["preview-cook"].tap()
        XCTAssertTrue(app.buttons["ingredient-1"].waitForExistence(timeout: 5))
        return app
    }

    @MainActor
    func testCookingChecklistUndoRedo() throws {
        let app = try openCookingRecipe()
        let cheese = app.buttons["ingredient-1"]
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
    }

    @MainActor
    private func enterFractionalPortions(in app: XCUIApplication) {
        app.buttons["Adjust portions"].tap()
        XCTAssertTrue(app.staticTexts["Your ingredients right now"].exists)
        let multiplier = app.textFields["portions"]
        multiplier.tap()
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForExistence(timeout: 5), "Portion field must open the keyboard before testing dismissal")
        // The field is already focused. Send native keyboard input through the
        // app instead of resolving that field again during keyboard relayout.
        app.typeText(XCUIKeyboardKey.delete.rawValue + "1.583945")
        XCTAssertTrue(UIReadiness.waitForValue("1.583945", matching: app.textFields.matching(identifier: "portions")))
        XCTAssertEqual(multiplier.value as? String, "1.583945")
    }

    @MainActor
    func testFractionalPortionsKeyboardAndSteppers() throws {
        let app = try openCookingRecipe()
        enterFractionalPortions(in: app)
        app.staticTexts["By portions"].tap()
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForNonExistence(timeout: 5), "Outside tap must dismiss the keyboard")
        app.buttons["apply-portions"].tap()
        XCTAssertTrue(app.staticTexts["1.58× recipe"].waitForExistence(timeout: 5), app.debugDescription)
        app.buttons["portion-plus"].tap()
        XCTAssertTrue(app.staticTexts["2.58× recipe"].waitForExistence(timeout: 5))
        app.buttons["portion-minus"].tap()
        XCTAssertTrue(app.staticTexts["1.58× recipe"].waitForExistence(timeout: 5), app.debugDescription)
    }

    @MainActor
    func testCookUndoScaleAndRestoreAfterTermination() throws {
        let app = try openCookingRecipe()
        let cheese = app.buttons["ingredient-1"]
        cheese.tap()
        cheese.tap()
        app.buttons["undo"].tap()
        XCTAssertEqual(cheese.value as? String, "Checked")
        enterFractionalPortions(in: app)
        // Confirm the sheet while the field is focused. Its stable identifier
        // distinguishes this commit action from the keyboard's Done button.
        app.buttons["apply-portions"].tap()
        XCTAssertTrue(app.staticTexts["1.58× recipe"].waitForExistence(timeout: 5))
        Self.relaunchPreservingData(app)
        XCTAssertTrue(app.buttons["ingredient-1"].waitForExistence(timeout: 5))
        XCTAssertEqual(app.buttons["ingredient-1"].value as? String, "Checked")
        XCTAssertTrue(app.staticTexts["1.58× recipe"].exists)
        app.buttons["History"].tap()
        XCTAssertTrue(app.staticTexts["Undo · Checked"].waitForExistence(timeout: 5))
    }
}
