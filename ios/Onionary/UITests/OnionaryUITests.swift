import XCTest
import notify
import UIKit

final class OnionaryUITests: OnionaryUITestCase {
    @MainActor
    func testNewStepFocusStaysAboveKeyboard() throws {
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        app.buttons["add-recipe"].tap()
        app.buttons["New recipe"].tap()
        let add = app.buttons["Add step"]
        if !add.isHittable { app.swipeUp() }
        XCTAssertTrue(add.isHittable)
        add.tap()
        let keyboard = app.keyboards.element(boundBy: 0)
        XCTAssertTrue(keyboard.waitForExistence(timeout: 5))
        let quickPath = keyboard.buttons["Continue"]
        if quickPath.exists { quickPath.tap() }
        let fields = app.descendants(matching: .any).matching(NSPredicate(format: "identifier BEGINSWITH %@", "instruction-"))
            .matching(NSPredicate(format: "elementType IN %@", [XCUIElement.ElementType.textField.rawValue, XCUIElement.ElementType.textView.rawValue]))
        app.typeText("Add lemon zest.")
        XCTAssertTrue(UIReadiness.waitForValue("Add lemon zest.", matching: fields))
        let field = fields.element(boundBy: 0)
        XCTAssertEqual(field.value as? String, "Add lemon zest.")
        XCTAssertLessThanOrEqual(field.frame.maxY, keyboard.frame.minY)
    }
    @MainActor
    func testSavedImportCanBeCopiedAndReviewed() throws {
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        app.buttons["add-recipe"].tap()
        app.buttons["Saved imports"].tap()
        let copy = app.buttons["copy-saved-import-1"]
        XCTAssertTrue(copy.waitForExistence(timeout: 5))
        copy.tap()
        XCTAssertEqual(copy.value as? String, "Copied")
        app.buttons["review-saved-import-1"].tap()
        let field = app.textFields["recipe-import-url"]
        XCTAssertTrue(field.waitForExistence(timeout: 5))
        XCTAssertEqual(field.value as? String, "https://chefkoch.de/rezepte/123")
        app.buttons["review-recipe-import"].tap()
        XCTAssertTrue(app.descendants(matching: .any).matching(identifier: "recipe-editor").firstMatch.waitForExistence(timeout: 5))
        XCTAssertTrue(app.textFields["Name"].exists)
    }
    @MainActor
    func testEquipmentStaysCheckedAfterRelaunch() throws {
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "--equipment-fixture", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        try selectRecipe(in: app)
        app.buttons["preview-cook"].tap()
        let tool = app.switches["equipment-Springform pan"]
        if !tool.isHittable { app.swipeUp() }
        XCTAssertTrue(tool.waitForExistence(timeout: 5))
        XCTAssertEqual(tool.value as? String, "0")
        tool.tap()
        XCTAssertEqual(tool.value as? String, "1")
        XCTAssertTrue(app.staticTexts["Equipment changes waiting to sync."].waitForNonExistence(timeout: 5))
        app.launchArguments += ["--fresh-equipment-cache", "--active-recipe"]
        Self.relaunchPreservingData(app)
        let restored = app.switches["equipment-Springform pan"]
        if !restored.isHittable { app.swipeUp() }
        XCTAssertTrue(restored.waitForExistence(timeout: 5))
        XCTAssertTrue(UIReadiness.waitForValue("1", matching: app.switches.matching(identifier: "equipment-Springform pan")))
        XCTAssertEqual(restored.value as? String, "1")
    }

    @MainActor
    func testEquipmentEditorAddsAndRemovesRows() throws {
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "--equipment-fixture", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        try selectRecipe(in: app)
        app.buttons["Edit recipe"].tap()
        let editor = app.scrollViews["recipe-editor"]
        XCTAssertTrue(editor.waitForExistence(timeout: 5))
        let add = app.buttons["Add tool"]
        for _ in 0..<3 where !add.isHittable { editor.swipeUp(velocity: .slow) }
        XCTAssertTrue(add.isHittable)
        add.tap()
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForExistence(timeout: 5))
        app.typeText("Cookie sheet")
        let fields = app.textFields.matching(identifier: "recipe-equipment-name")
        XCTAssertEqual(fields.element(boundBy: 1).value as? String, "Cookie sheet")
        app.buttons["Done"].tap()
        let remove = app.buttons.matching(identifier: "Remove tool").element(boundBy: 0)
        if !remove.isHittable { editor.swipeDown(velocity: .slow) }
        remove.tap()
        XCTAssertEqual(fields.element(boundBy: 0).value as? String, "Cookie sheet")
        app.buttons["Save"].tap()
        XCTAssertTrue(app.staticTexts["Cookie sheet"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.staticTexts["Springform pan"].exists)
    }

    @MainActor
    func testStepTimerStartsAndCanBeCancelled() throws {
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "--timer-fixture", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        try selectRecipe(in: app)
        app.buttons["preview-cook"].tap()
        let start = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "start-timer-1-1-")).element(boundBy: 0)
        XCTAssertTrue(start.waitForExistence(timeout: 5))
        let history = app.buttons["History"]
        if start.frame.maxY >= history.frame.minY { app.swipeUp() }
        XCTAssertLessThan(start.frame.maxY, history.frame.minY)
        XCTAssertTrue(start.isHittable)
        start.tap()
        let timer = app.staticTexts["active-cooking-timer"]
        XCTAssertTrue(timer.waitForExistence(timeout: 5))
        XCTAssertFalse(start.isEnabled)
        app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "remove-timer-1-1-")).element(boundBy: 0).tap()
        XCTAssertTrue(timer.waitForNonExistence(timeout: 5))
        XCTAssertTrue(start.isEnabled)
    }
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
        app.buttons["cancel-intelligence"].tap()
        XCTAssertTrue(app.collectionViews["intelligence-form"].waitForNonExistence(timeout: 5))
        // The list is the returning screen on both split and compact layouts.
        XCTAssertTrue(app.collectionViews["recipe-list"].buttons["recipe-1"].exists)
    }

    @MainActor
    func testMultipleTagFilters() throws {
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "--marketing", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        let vegetarian = app.buttons["category-Vegetarian"]
        let quick = app.buttons["category-Quick & easy"]
        let comfort = app.buttons["category-Comfort food"]
        XCTAssertTrue(vegetarian.label.contains("6 recipes"))
        XCTAssertTrue(comfort.label.contains("3 recipes"))
        vegetarian.tap()
        quick.tap()
        XCTAssertEqual(vegetarian.value as? String, "Selected")
        XCTAssertEqual(quick.value as? String, "Selected")
        XCTAssertTrue(vegetarian.label.contains("3 recipes"))
        XCTAssertTrue(comfort.label.contains("0 recipes"))
        app.buttons["clear-tag-filter"].tap()
        XCTAssertTrue(app.buttons["clear-tag-filter"].waitForNonExistence(timeout: 5))
        XCTAssertEqual(vegetarian.value as? String, "Not selected")
        XCTAssertEqual(quick.value as? String, "Not selected")
        XCTAssertTrue(vegetarian.label.contains("6 recipes"))
        XCTAssertTrue(comfort.label.contains("3 recipes"))
    }

    @MainActor
    func testPantryMatchingQuantities() throws {
        let app = makeOnionaryApp()
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
        app.buttons["pantry-add"].tap()
        let cheese = app.buttons["pantry-remove-170 g Cheese-0"]
        XCTAssertTrue(cheese.waitForExistence(timeout: 5))
        XCTAssertEqual(cheese.label, "Remove ingredient 170 g Cheese")

        pantry.tap()
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForExistence(timeout: 5))
        app.typeText("250 g Pasta")
        XCTAssertTrue(UIReadiness.waitForValue("250 g Pasta", matching: pantryFields))
        app.buttons["close-pantry"].tap()
        XCTAssertTrue(app.buttons["close-pantry"].waitForNonExistence(timeout: 5))

        app.buttons["Cook with what you have"].tap()
        let pasta = app.buttons["pantry-remove-250 g Pasta-0"]
        XCTAssertTrue(pasta.waitForExistence(timeout: 5))
        XCTAssertEqual(pasta.label, "Remove ingredient 250 g Pasta")
        XCTAssertTrue(cheese.exists)
        XCTAssertTrue((match.value as? String ?? "").contains("Available: Cheese, Pasta"))
        cheese.tap()
        XCTAssertTrue(cheese.waitForNonExistence(timeout: 5))
        XCTAssertTrue(pasta.exists)
        XCTAssertTrue((match.value as? String ?? "").contains("Missing: Cheese"))

        app.buttons["pantry-reset"].tap()
        XCTAssertTrue(match.waitForNonExistence(timeout: 5))
        app.buttons["close-pantry"].tap()
        XCTAssertTrue(app.buttons["close-pantry"].waitForNonExistence(timeout: 5))
        app.buttons["Cook with what you have"].tap()
        XCTAssertTrue(app.buttons["close-pantry"].waitForExistence(timeout: 5))
        XCTAssertFalse(pasta.exists)
        XCTAssertFalse(app.buttons["pantry-reset"].exists)
    }

    @MainActor
    func testIntelligenceModeAndLanguageOptions() throws {
        let app = makeOnionaryApp()
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
        let app = makeOnionaryApp()
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
        let app = makeOnionaryApp()
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
        let app = try newRecipeWithName("My offline soup")
        let editor = app.navigationBars["New recipe"]
        editor.buttons["Save"].tap()
        XCTAssertTrue(app.staticTexts["recipe-save-error"].waitForExistence(timeout: 5))
        XCTAssertTrue(UIReadiness.waitForValue("My offline soup", matching: app.textFields.matching(identifier: "Name")), "Failed save must retain the complete draft name")
        XCTAssertTrue(editor.buttons["Save"].isEnabled)
        editor.buttons["Cancel"].tap()
        XCTAssertTrue(editor.waitForNonExistence(timeout: 5))
        XCTAssertTrue(savedDraft("My offline soup", in: app).waitForExistence(timeout: 5))

        Self.relaunchPreservingData(app)
        try tapNavigation("Recipes", in: app)
        let restoredDraft = savedDraft("My offline soup", in: app)
        XCTAssertTrue(restoredDraft.waitForExistence(timeout: 5))
        restoredDraft.tap()
        XCTAssertTrue(UIReadiness.waitForValue("My offline soup", matching: app.textFields.matching(identifier: "Name")), "Cold restoration must retain the complete draft name")
    }

    @MainActor
    func testSavedDraftShowsChanges() throws {
        let app = try newRecipeWithName("My offline soup")
        app.navigationBars["New recipe"].buttons["Cancel"].tap()
        let library = app.collectionViews["recipe-list"]
        let viewChanges = library.buttons["View draft changes"]
        XCTAssertTrue(viewChanges.waitForExistence(timeout: 5))
        viewChanges.tap()
        let changes = app.collectionViews["recipe-draft-changes"]
        XCTAssertTrue(changes.staticTexts["My offline soup"].waitForExistence(timeout: 5))
        XCTAssertTrue(changes.staticTexts["Name"].exists)
        XCTAssertFalse(changes.staticTexts["No recipe changes"].exists)
        app.navigationBars["Draft changes"].buttons["Done"].tap()
        XCTAssertTrue(changes.waitForNonExistence(timeout: 5))
        XCTAssertTrue(savedDraft("My offline soup", in: app).exists)
    }

    @MainActor
    private func newRecipeWithName(_ title: String) throws -> XCUIApplication {
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "--offline-save", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        app.buttons["add-recipe"].tap()
        app.buttons["New recipe"].tap()
        let name = app.textFields["Name"]
        XCTAssertTrue(name.waitForExistence(timeout: 5))
        name.tap()
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForExistence(timeout: 5))
        app.typeText(title)
        return app
    }

    @MainActor
    private func savedDraft(_ title: String, in app: XCUIApplication) -> XCUIElement {
        app.collectionViews["recipe-list"].buttons.matching(identifier: "saved-draft-\(title)").element(boundBy: 0)
    }

    @MainActor
    func testIngredientOrderCanBeMovedAndSaved() throws {
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "--ordering-fixture", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        try selectRecipe(in: app)
        app.buttons["Edit recipe"].tap()
        let ingredients = app.buttons["Reorder ingredients"]
        XCTAssertTrue(ingredients.waitForExistence(timeout: 5))
        ingredients.tap()
        let sheet = app.navigationBars["Reorder ingredients"]
        let list = app.collectionViews["recipe-order-list"]
        XCTAssertTrue(list.waitForExistence(timeout: 5))
        XCTAssertEqual(list.textFields.count, 0)
        let cheese = list.staticTexts["Cheese"]
        let pasta = list.staticTexts["Pasta"]
        let lemon = list.staticTexts["Lemon"]
        XCTAssertTrue(list.buttons["Reorder Cheese"].exists)
        XCTAssertLessThan(cheese.frame.minY, pasta.frame.minY)
        XCTAssertLessThan(pasta.frame.minY, lemon.frame.minY)
        XCTAssertFalse(list.buttons["Move Cheese up"].isEnabled)
        XCTAssertFalse(list.buttons["Move Lemon down"].isEnabled)
        list.buttons["Move Pasta up"].tap()
        XCTAssertLessThan(pasta.frame.minY, cheese.frame.minY)
        list.buttons["Move Cheese down"].tap()
        XCTAssertLessThan(lemon.frame.minY, cheese.frame.minY)
        sheet.buttons["Done"].tap()
        XCTAssertTrue(sheet.waitForNonExistence(timeout: 5))
        app.buttons["Save"].tap()
        XCTAssertTrue(app.navigationBars["Edit recipe"].waitForNonExistence(timeout: 5))
        let preview = app.collectionViews["recipe-preview"]
        let savedRows = ["Pasta", "Lemon", "Cheese"].map { preview.staticTexts[$0] }
        XCTAssertTrue(savedRows.allSatisfy(\.exists))
        let savedOrder = savedRows.map { $0.frame.minY }
        XCTAssertLessThan(savedOrder[0], savedOrder[1])
        XCTAssertLessThan(savedOrder[1], savedOrder[2])
    }

    @MainActor
    func testCancellingUnchangedEditDoesNotSaveDraft() throws {
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        try selectRecipe(in: app)
        app.buttons["Edit recipe"].tap()
        let editor = app.navigationBars["Edit recipe"]
        XCTAssertTrue(editor.buttons["Cancel"].waitForExistence(timeout: 5))
        editor.buttons["Cancel"].tap()
        XCTAssertTrue(editor.waitForNonExistence(timeout: 5))
        let back = app.navigationBars["Recipe preview"].buttons["Recipe book"]
        if back.exists { back.tap() }
        let book = app.collectionViews["recipe-list"]
        XCTAssertTrue(book.buttons["recipe-1"].waitForExistence(timeout: 5))
        XCTAssertFalse(book.buttons["saved-draft-Lemon & cheese pasta"].exists)
        XCTAssertFalse(book.staticTexts["Saved drafts"].exists)
    }

    @MainActor
    func testIngredientGroupPersistsAfterSaving() throws {
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        try selectRecipe(in: app)
        app.buttons["Edit recipe"].tap()
        let reorder = app.buttons["Reorder ingredients"]
        XCTAssertTrue(reorder.waitForExistence(timeout: 5))
        reorder.tap()
        let sheet = app.navigationBars["Reorder ingredients"]
        let orderList = app.collectionViews["recipe-order-list"]
        let addGroup = orderList.buttons["Add group"]
        XCTAssertTrue(addGroup.waitForExistence(timeout: 5))
        addGroup.tap()
        let groupName = orderList.textFields["new-recipe-group-name"]
        XCTAssertTrue(groupName.waitForExistence(timeout: 5))
        groupName.tap()
        app.typeText("Sauce")
        orderList.buttons["confirm-recipe-group"].tap()
        let cheeseGroup = orderList.buttons["recipe-group-Cheese"]
        XCTAssertTrue(cheeseGroup.waitForExistence(timeout: 5))
        cheeseGroup.tap()
        app.buttons["Sauce"].tap()
        XCTAssertTrue(orderList.staticTexts["Sauce"].waitForExistence(timeout: 5))
        sheet.buttons["Done"].tap()
        XCTAssertTrue(sheet.waitForNonExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["Sauce"].exists)
        app.buttons["Save"].tap()
        let preview = app.collectionViews["recipe-preview"]
        XCTAssertTrue(preview.staticTexts["Sauce"].waitForExistence(timeout: 5))
        XCTAssertFalse(reorder.exists)
    }

    @MainActor
    func testRecipeTagSuggestionsAndMultiwordChips() throws {
        let app = makeOnionaryApp()
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
        let app = makeOnionaryApp()
        // The recipe preview has its own coverage. Start cooking so that
        // this test's first navigation action exercises the session lifecycle.
        app.launchArguments = ["--ui-testing", "--reset", "--active-recipe", "--renew-session", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        let ingredient = app.buttons["ingredient-1"]
        XCTAssertTrue(ingredient.waitForExistence(timeout: 5))
        ingredient.tap()
        XCTAssertEqual(ingredient.value as? String, "Checked")
        // Expire access while the real app is backgrounded, then let its normal
        // foreground refresh renew it. Full cold restoration has its own case.
        UIAppLifecycle.background()
        app.activate()
        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))
        // One native query observes both existence and the restored value.
        // A plain existence wait can request several slow snapshots after Home.
        XCTAssertTrue(UIReadiness.waitForValue("Checked", matching: app.buttons.matching(identifier: "ingredient-1")))
        try tapNavigation("Settings", in: app)
        XCTAssertTrue(app.staticTexts["Access valid until"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["Account, Test Cook"].exists)
        XCTAssertTrue(app.staticTexts["Email, cook@example.org"].exists)
        XCTAssertFalse(app.buttons["Sign in with passkey"].exists)
        try tapNavigation("Cooking", in: app)
        XCTAssertEqual(ingredient.value as? String, "Checked")
    }

    @MainActor
    func testExpiredSessionLeavesCookingAvailable() throws {
        let app = makeOnionaryApp()
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
        let app = makeOnionaryApp()
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
        let app = makeOnionaryApp()
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
    func testLiveActivityStartAndStop() {
        assertCookingModeCycle(systemActivityKit: true)
    }

    @MainActor
    func testCookingModeWithFixtureBackend() {
        assertCookingModeCycle(systemActivityKit: false)
    }

    @MainActor
    private func assertCookingModeCycle(systemActivityKit: Bool) {
        let app = launchCookingControlsFixture(systemActivityKit: systemActivityKit)
        let modes = app.buttons.matching(identifier: "cooking-mode")
        let mode = modes.element(boundBy: 0)
        XCTAssertTrue(mode.waitForExistence(timeout: 5))
        XCTAssertEqual(mode.value as? String, "Off")
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
        let app = try openCookingTag()
        let matches = app.collectionViews["tag-recipes-list"]
        let chickpeas = matches.buttons["tag-recipe-3"]
        XCTAssertTrue(chickpeas.waitForExistence(timeout: 5))
        XCTAssertFalse(matches.buttons["tag-recipe-2"].exists)
        chickpeas.tap()
        XCTAssertTrue(matches.waitForNonExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["Crispy chickpea bowls"].waitForExistence(timeout: 5))
    }

    @MainActor
    func testRecipeTagDismissalKeepsCurrentRecipe() throws {
        let app = try openCookingTag()
        let matches = app.collectionViews["tag-recipes-list"]
        XCTAssertTrue(matches.waitForExistence(timeout: 5))
        app.buttons["close-tag-recipes"].tap()
        XCTAssertTrue(matches.waitForNonExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["Creamy lemon pasta"].exists)
    }

    @MainActor
    private func openCookingTag() throws -> XCUIApplication {
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "--marketing", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        app.buttons["Choose a recipe"].tap()
        try selectRecipe(in: app)
        app.buttons["preview-cook"].tap()
        app.buttons["recipe-tag-Quick & easy"].tap()
        return app
    }

    @MainActor
    private func openStepEditor() throws -> XCUIApplication {
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        try selectRecipe(in: app)
        app.buttons["Edit recipe"].tap()
        XCTAssertTrue(app.textFields["Name"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["insert-placeholder"].exists)
        app.swipeUp()
        app.swipeUp()
        return app
    }

    @MainActor
    func testStepAmountTools() throws {
        // Allow the same native menu transition waits as the cooking-menu case.
        executionTimeAllowance = 240
        let app = try openStepEditor()
        let instructions = app.textFields.matching(NSPredicate(format: "identifier BEGINSWITH %@", "instruction-"))
        let first = instructions.element(boundBy: 0)
        XCTAssertTrue(first.waitForExistence(timeout: 5))
        // Tap before the first word with the software keyboard. Hardware shortcuts
        // cause the keyboard and its floating menu to reposition during automation.
        let leadingText = CGVector(dx: 0.002, dy: 0.5)
        first.coordinate(withNormalizedOffset: leadingText).tap()
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForExistence(timeout: 5),
                      "The instruction field must open the keyboard")
        let insert = app.buttons["insert-placeholder"]
        XCTAssertTrue(insert.waitForExistence(timeout: 5))
        insert.tap()
        app.buttons["Cheese"].tap()
        let firstWithIngredient = "{{Cheese|100%}} Boil the pasta in salted water."
        XCTAssertEqual(first.value as? String, firstWithIngredient)
        if insert.exists { app.buttons["Done"].tap() }
        XCTAssertTrue(insert.waitForNonExistence(timeout: 5))
        let keyboard = app.keyboards.element(boundBy: 0)
        XCTAssertTrue(keyboard.waitForNonExistence(timeout: 5))

        let secondText = "Fold in {{Cheese|20%}} and lemon zest."
        let second = instructions.matching(NSPredicate(format: "value == %@", secondText)).firstMatch
        XCTAssertTrue(second.waitForExistence(timeout: 5))
        if !second.isHittable { app.swipeUp() }
        XCTAssertTrue(second.wait(for: \.isHittable, toEqual: true, timeout: 5),
                      "The second instruction must be reachable after closing the keyboard")
        // Use a stable identity once found so we can read its updated text.
        let secondInstruction = app.textFields[second.identifier]
        secondInstruction.coordinate(withNormalizedOffset: leadingText).tap()
        XCTAssertTrue(keyboard.waitForExistence(timeout: 5), "The second instruction must open the keyboard")
        XCTAssertTrue(insert.waitForExistence(timeout: 5))
        insert.tap()
        let insertTimer = app.buttons["insert-time-placeholder"]
        XCTAssertTrue(insertTimer.wait(for: \.isHittable, toEqual: true, timeout: 5))
        insertTimer.tap()
        let timer = app.collectionViews["recipe-timer-editor"]
        XCTAssertTrue(timer.waitForExistence(timeout: 5))
        let minutes = timer.textFields["timer-minutes"]
        let seconds = timer.textFields["timer-seconds"]
        minutes.tap()
        app.typeText("1")
        seconds.tap()
        app.typeText("30")
        XCTAssertEqual(minutes.value as? String, "1")
        XCTAssertEqual(seconds.value as? String, "30")
        let confirm = app.buttons["confirm-recipe-timer"]
        XCTAssertTrue(confirm.wait(for: \.isHittable, toEqual: true, timeout: 5))
        XCTAssertTrue(confirm.isEnabled)
        confirm.tap()
        XCTAssertTrue(timer.waitForNonExistence(timeout: 5))
        XCTAssertEqual(secondInstruction.value as? String, "{{time|90s}} " + secondText)
        XCTAssertEqual(first.value as? String, firstWithIngredient)
        if app.keyboards.element(boundBy: 0).exists { app.buttons["Done"].tap() }
        XCTAssertFalse(insert.exists)
    }

    @MainActor
    func testStepPlaceholderHelpInEmptyRecipe() throws {
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        app.buttons["add-recipe"].tap()
        app.buttons["New recipe"].tap()
        let add = app.buttons["Add step"]
        if !add.isHittable { app.swipeUp() }
        add.tap()
        let insert = app.buttons["insert-placeholder"]
        XCTAssertTrue(insert.waitForExistence(timeout: 5))
        insert.tap()
        XCTAssertTrue(app.buttons["No ingredients added yet"].exists)
        XCTAssertTrue(app.buttons["insert-time-placeholder"].isEnabled)
        app.buttons["What is this?"].tap()
        let alert = app.alerts["Recipe placeholders"]
        XCTAssertTrue(alert.waitForExistence(timeout: 5))
        XCTAssertTrue(alert.staticTexts.containing(NSPredicate(format: "label CONTAINS %@ AND label CONTAINS %@",
            "{{Flour|50%}}", "{{time|2m30s}}")).firstMatch.exists)
        alert.buttons["Done"].tap()
        XCTAssertTrue(alert.waitForNonExistence(timeout: 5))
    }

    @MainActor
    func testKitchenPlanAndOpenRecipe() throws {
        let app = makeOnionaryApp()
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
        // A hosted iPad passed the save and progress checks before its
        // three-minute timer expired during XCTest's finalization.
        executionTimeAllowance = 240
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "--editing-active-recipe", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        // Starting a recipe and toggling a check are covered by the checklist
        // tests. Begin from an active adventure to focus on the save decision.
        let checkedIngredient = app.buttons["ingredient-1"]
        XCTAssertTrue(UIReadiness.waitForValue("Checked", matching: app.buttons.matching(identifier: "ingredient-1")))
        // Editing from the preview still updates the active recipe's saved
        // copy. The feedback test separately covers the native cooking menu.
        try tapNavigation("Recipes", in: app)
        try selectRecipe(in: app)
        let edit = app.navigationBars["Recipe preview"].buttons["Edit recipe"]
        XCTAssertTrue(edit.waitForExistence(timeout: 5))
        edit.tap()
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
        // Verify the exact name in the saved recipe preview. Reading the text
        // field again here makes XCTest query the transient keyboard hierarchy.
        app.navigationBars["Edit recipe"].buttons["Save"].tap()
        // Resolve the actual presented alert, not an app-wide button during
        // the editor/keyboard presentation transition.
        let reloadAlert = app.alerts["Reload cooking recipe?"]
        let keepProgress = reloadAlert.buttons["Keep cooking progress"]
        XCTAssertTrue(keepProgress.waitForExistence(timeout: 5))
        keepProgress.tap()
        XCTAssertTrue(reloadAlert.waitForNonExistence(timeout: 5))
        XCTAssertTrue(app.collectionViews["recipe-preview"].staticTexts["Edited pasta"].waitForExistence(timeout: 5))
        try tapNavigation("Cooking", in: app)
        XCTAssertTrue(app.staticTexts["Lemon & cheese pasta"].waitForExistence(timeout: 5))
        XCTAssertEqual(checkedIngredient.value as? String, "Checked")
    }

    @MainActor
    func testCookingOptionsSurviveActionFeedbackExpiry() {
        // XCTest can wait 60 seconds for each of the native menu transitions.
        executionTimeAllowance = 240
        let clock = "de.malaber.onionary.uitest.feedback." + UUID().uuidString
        let app = makeOnionaryApp()
        // Start at the active adventure. The independent cooking tests cover
        // starting it from Preview, while this test exercises the native menu.
        app.launchArguments = ["--ui-testing", "--reset", "--active-recipe", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launchEnvironment = ["ONIONARY_TEST_FEEDBACK_CLOCK": clock]
        app.launch()
        let ingredient = app.buttons["ingredient-1"]
        XCTAssertTrue(ingredient.waitForExistence(timeout: 5))
        ingredient.tap()
        XCTAssertEqual(ingredient.value as? String, "Checked")
        let feedback = app.staticTexts["recent-action"]
        XCTAssertTrue(feedback.waitForExistence(timeout: 5))
        let cookingOptions = app.buttons["cooking-options"]
        cookingOptions.tap()
        let edit = app.buttons["Edit recipe"]
        XCTAssertTrue(edit.waitForExistence(timeout: 5))
        XCTAssertTrue(edit.isHittable)
        // Retain the visible menu row's position across the feedback update.
        // Resolving the native menu's AX snapshot again can stall on CI.
        let editFrame = edit.frame
        let appFrame = app.frame
        let editTarget = app.coordinate(withNormalizedOffset: .zero).withOffset(
            CGVector(dx: editFrame.midX - appFrame.minX, dy: editFrame.midY - appFrame.minY)
        )
        // Expire the real feedback while the native menu is open. Accessibility
        // round trips must not race a four-second clock on a loaded CI host.
        XCTAssertEqual(notify_post(clock), UInt32(NOTIFY_STATUS_OK))
        XCTAssertTrue(feedback.waitForNonExistence(timeout: 8))
        editTarget.tap()
        let name = app.textFields["Name"]
        XCTAssertTrue(name.waitForExistence(timeout: 5))
        let editor = app.navigationBars["Edit recipe"]
        editor.buttons["Cancel"].tap()
        // The cooking control must be actionable again after cancellation.
        // Resolving the dismissed bar can block on its retired AX hierarchy.
        XCTAssertTrue(cookingOptions.waitForExistence(timeout: 5))
        XCTAssertTrue(cookingOptions.isHittable)
        XCTAssertEqual(ingredient.value as? String, "Checked")
    }

    @MainActor
    func testShareRecipeCopyAndRevokeLink() throws {
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        try selectRecipe(in: app)
        // Preview offers the same sharing sheet without changing the active
        // recipe or depending on a native menu animation.
        let share = app.buttons["Share recipe copy"]
        XCTAssertTrue(share.waitForExistence(timeout: 5))
        share.tap()
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
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        app.buttons["add-recipe"].tap()
        app.buttons["Import recipe"].tap()
        let form = app.collectionViews["recipe-import-form"]
        let url = form.textFields.matching(identifier: "recipe-import-url")
        url.element.tap()
        XCTAssertTrue(app.keyboards.element(boundBy: 0).waitForExistence(timeout: 5))
        app.typeText("https://www.chefkoch.de/rezepte/123")
        XCTAssertTrue(UIReadiness.waitForValue("https://www.chefkoch.de/rezepte/123", matching: url))
        form.buttons["review-recipe-import"].tap()
        XCTAssertTrue(UIReadiness.waitForValue("Lemon & cheese pasta", matching: app.textFields.matching(identifier: "Name")))
    }

    @MainActor
    func testIntelligenceDraftRequiresUserInput() throws {
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Recipes", in: app)
        app.buttons["add-recipe"].tap()
        app.buttons["Create with Intelligence"].tap()
        let form = app.collectionViews["intelligence-form"]
        XCTAssertTrue(form.waitForExistence(timeout: 5))
        XCTAssertTrue(form.textViews["Describe your recipe"].exists)
        let create = form.buttons.matching(identifier: "Create recipe draft").element(boundBy: 0)
        // This button follows the mode, language and availability explanation.
        for _ in 0..<4 {
            if create.exists { break }
            form.swipeUp()
        }
        let disabledCreate = form.buttons.matching(identifier: "Create recipe draft")
            .matching(NSPredicate(format: "enabled == NO")).element(boundBy: 0)
        XCTAssertTrue(disabledCreate.exists, "An empty prompt must show a disabled create action")
        dismissIntelligence(in: app)
    }

    @MainActor
    func testNativeSettingsLanguageAndAppearance() throws {
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        try tapNavigation("Settings", in: app)
        XCTAssertTrue(app.buttons["Switch backend"].exists)
        XCTAssertFalse(app.textFields["backend"].exists)
        app.buttons["accent-picker"].tap()
        let blueberry = app.buttons["accent-Blueberry"]
        XCTAssertTrue(blueberry.waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["accent-Onion"].isSelected)
        blueberry.tap()
        XCTAssertTrue(blueberry.isSelected)
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
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "--marketing", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        let captureLockScreen = UIDevice.current.userInterfaceIdiom == .phone
        if captureLockScreen { app.launchArguments += ["--system-live-activity", "--marketing-lock-screen"] }
        app.launch()
        // The marketing fixture already sets light appearance. Start with the
        // same capture flow as Duo; appearance settings have their own test.
        try captureMarketingScenes(in: app) { identifier in
            if identifier == "recipe-1" { try selectRecipe(in: app) }
            else { app.buttons[identifier].tap() }
        } capture: { name in
            attachMarketingScreenshot(XCUIScreen.main.screenshot(), name: name)
        }
        if captureLockScreen {
            app.buttons["Done"].tap()
            let modes = app.buttons.matching(identifier: "cooking-mode")
            XCTAssertTrue(UIReadiness.waitForValue("Off", matching: modes))
            modes.firstMatch.tap()
            XCTAssertTrue(UIReadiness.waitForValue("On", matching: modes))
            captureLiveActivity(in: app)
        }
    }

    @MainActor
    private func captureLiveActivity(in app: XCUIApplication) {
        // iOS presents its real Lock Screen (Cover Sheet) when pulled down
        // from the leading status-bar edge. WidgetKit owns all visible pixels.
        let springboard = XCUIApplication(bundleIdentifier: "com.apple.springboard")
        XCUIDevice.shared.press(.home)
        XCTAssertTrue(springboard.wait(for: .runningForeground, timeout: 5))
        let top = springboard.coordinate(withNormalizedOffset: CGVector(dx: 0.15, dy: 0.005))
        let bottom = springboard.coordinate(withNormalizedOffset: CGVector(dx: 0.15, dy: 0.8))
        top.press(forDuration: 0.02, thenDragTo: bottom)
        let activity = springboard.descendants(matching: .any).matching(NSPredicate(
            format: "identifier == %@ OR label == %@", "onionary-cooking-live-activity", "Creamy lemon pasta")).firstMatch
        // ActivityKit can report On while iOS 27.2 is still launching the first
        // WidgetKit renderer. Start the capture only after SpringBoard has it.
        guard activity.waitForExistence(timeout: 35) else {
            let screenshot = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
            screenshot.name = "lock-screen-activity-missing"
            screenshot.lifetime = .keepAlways
            add(screenshot)
            XCTFail("The system Live Activity must be visible on the Lock Screen")
            return
        }
        let allow = springboard.buttons.matching(NSPredicate(format: "label IN %@", ["Allow", "Erlauben"])).firstMatch
        if allow.waitForExistence(timeout: 2) {
            allow.tap()
            XCTAssertTrue(allow.waitForNonExistence(timeout: 5))
        }
        XCTAssertTrue(activity.waitForExistence(timeout: 5), "The capture must show cooking progress without the permission prompt")
        attachMarketingScreenshot(XCUIScreen.main.screenshot(), name: "08-live-activity-lock-screen")
        // Close the Cover Sheet and remove the actual system activity.
        let handle = springboard.coordinate(withNormalizedOffset: CGVector(dx: 0.50, dy: 0.995))
        handle.press(forDuration: 0.02, thenDragTo: springboard.coordinate(withNormalizedOffset: CGVector(dx: 0.50, dy: 0.25)))
        app.activate()
        let modes = app.buttons.matching(identifier: "cooking-mode")
        XCTAssertTrue(UIReadiness.waitForValue("On", matching: modes))
        modes.firstMatch.tap()
        XCTAssertTrue(UIReadiness.waitForValue("Off", matching: modes))
    }

    @MainActor
    func testPortionButtonsWithoutKeyboard() throws {
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        app.buttons["Choose a recipe"].tap()
        try selectRecipe(in: app)
        let previewPlus = app.buttons["preview-portion-plus"]
        XCTAssertTrue(previewPlus.waitForExistence(timeout: 5))
        previewPlus.tap()
        XCTAssertEqual(app.textFields["preview-portion-count"].value as? String, "2")
        app.buttons["preview-cook"].tap()
        XCTAssertTrue(app.buttons["portion-plus"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["2× recipe"].exists)
        XCTAssertFalse(app.keyboards.element(boundBy: 0).exists)
        app.buttons["portion-plus"].tap()
        XCTAssertTrue(app.staticTexts["3× recipe"].waitForExistence(timeout: 5))
        app.buttons["portion-minus"].tap()
        XCTAssertTrue(app.staticTexts["2× recipe"].waitForExistence(timeout: 5))
        app.buttons["portion-minus"].tap()
        XCTAssertTrue(app.staticTexts["1× recipe"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["portion-minus"].isEnabled)
    }

    @MainActor
    private func launchCookingControlsFixture(systemActivityKit: Bool = false) -> XCUIApplication {
        // Cover the full recipe selection separately in the cold-restoration
        // test. Start these control tests with the same recipe already active.
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "--active-recipe", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        if systemActivityKit { app.launchArguments.append("--system-live-activity") }
        app.launch()
        XCTAssertTrue(app.buttons["ingredient-1"].waitForExistence(timeout: 5))
        return app
    }

    @MainActor
    func testCookingChecklistUndoRedo() {
        let app = launchCookingControlsFixture()
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
    func testScaledStepIngredientUseIsSeparateFromPreparation() {
        let app = launchCookingControlsFixture()
        let cheese = app.buttons["ingredient-1"]
        let badge = app.buttons["step-use-2-1"]
        XCTAssertTrue(badge.waitForExistence(timeout: 5))
        XCTAssertEqual(badge.label, "40 g Cheese")
        app.buttons["portion-plus"].tap()
        XCTAssertEqual(badge.label, "80 g Cheese")
        // The compact layout can place this badge beneath the fixed history bar.
        app.swipeUp()
        XCTAssertTrue(badge.isHittable)
        badge.tap()
        XCTAssertEqual(badge.value as? String, "Used")
        XCTAssertEqual(cheese.value as? String, "Unchecked")
        XCTAssertEqual(app.buttons["step-2"].value as? String, "Unchecked")
        app.buttons["undo"].tap()
        XCTAssertEqual(badge.value as? String, "Not used")
        XCTAssertEqual(cheese.value as? String, "Unchecked")
        XCTAssertEqual(badge.label, "80 g Cheese")
        if !cheese.isHittable { app.swipeDown() }
        cheese.tap()
        XCTAssertEqual(cheese.value as? String, "Checked")
        XCTAssertEqual(badge.value as? String, "Not used")
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
    func testFractionalPortionsKeyboardAndSteppers() {
        let app = launchCookingControlsFixture()
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
        let app = makeOnionaryApp()
        app.launchArguments = ["--ui-testing", "--reset", "-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        app.launch()
        app.buttons["Choose a recipe"].tap()
        try selectRecipe(in: app)
        app.buttons["preview-cook"].tap()
        let cheese = app.buttons["ingredient-1"]
        XCTAssertTrue(cheese.waitForExistence(timeout: 5))
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
