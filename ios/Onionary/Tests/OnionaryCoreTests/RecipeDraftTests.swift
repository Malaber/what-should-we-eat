import XCTest
@testable import OnionaryCore

final class RecipeDraftTests: XCTestCase {
    func testEquipmentFollowsKitchenAcrossRecipesAndPersistence() throws {
        var kitchen = try JSONDecoder().decode(Kitchen.self, from: Data(#"{"recipes":[],"adventures":[]}"#.utf8))
        XCTAssertFalse(kitchen.hasEquipment("Springform pan"))
        kitchen.toggleEquipment("Springform pan")
        let restored = try JSONDecoder().decode(Kitchen.self, from: JSONEncoder().encode(kitchen))
        XCTAssertTrue(restored.hasEquipment(" SPRINGFORM  PAN "))
        XCTAssertFalse(Kitchen().hasEquipment("Springform pan"))

        var draft = RecipeDraft()
        draft.name = "Cake"
        draft.equipment = ["Knife", " knife ", "Springform pan", ""]
        let encoded = try JSONSerialization.jsonObject(with: draft.validatedData()) as? [String: Any]
        XCTAssertEqual(encoded?["equipment"] as? [String], ["Knife", "Springform pan"])
        var edited = draft
        edited.equipment = []
        XCTAssertEqual(edited.changes(from: draft).map(\.field), ["Equipment"])
        let cleared = try JSONSerialization.jsonObject(with: edited.validatedData()) as? [String: Any]
        XCTAssertEqual(cleared?["equipment"] as? [String], [])
    }
    func testEquipmentReconcilesLegacyAndChangesMadeDuringSync() throws {
        let fixture = Data(#"{"recipes":[],"adventures":[],"ownedEquipment":["springform pan"]}"#.utf8)
        var kitchen = try JSONDecoder().decode(Kitchen.self, from: fixture)
        XCTAssertEqual(kitchen.equipmentUpdate.legacyOwned, ["springform pan"])
        XCTAssertTrue(kitchen.hasEquipment("SPRINGFORM PAN"))
        kitchen.toggleEquipment("Kitchen scale")
        let sent = kitchen.equipmentUpdate
        kitchen.toggleEquipment("Kitchen scale")
        kitchen.toggleEquipment("Chef knife")
        kitchen.reconcileEquipment(["springform pan", "kitchen scale"], sent: sent)
        XCTAssertFalse(kitchen.hasEquipment("Kitchen scale"))
        XCTAssertTrue(kitchen.hasEquipment("Chef knife"))
        XCTAssertEqual(kitchen.equipmentUpdate.legacyOwned, [])
        XCTAssertEqual(kitchen.equipmentUpdate.changes, ["kitchen scale": false, "chef knife": true])
        let confirmed = kitchen.equipmentUpdate
        kitchen.reconcileEquipment(["springform pan", "chef knife"], sent: confirmed)
        XCTAssertFalse(kitchen.hasPendingEquipment)
        kitchen.reconcileEquipment(["thermomix"], sent: kitchen.equipmentUpdate)
        XCTAssertTrue(kitchen.hasEquipment("Thermomix"))
        XCTAssertFalse(kitchen.hasEquipment("Chef knife"))
    }

    func testInsertPlaceholderReplacesSelectionWithUnicodeBeforeCaret() {
        let text = "🥣 Add flour, then bake."
        let range = (text as NSString).range(of: "flour")
        let result = IngredientPlaceholders.inserting("{{Flour|50%}}", in: text, selection: range)
        XCTAssertEqual(result.text, "🥣 Add {{Flour|50%}}, then bake.")
        XCTAssertEqual(result.caret.location, "🥣 Add {{Flour|50%}}".utf16.count)
        let timer = IngredientPlaceholders.inserting("{{time|90s}}", in: "stir", selection: NSRange(location: 0, length: 0))
        XCTAssertEqual(timer.text, "{{time|90s}} stir")
    }

    func testPartialIngredientReferenceHintOnlyAfterFirstValidReference() {
        var draft = RecipeDraft()
        for name in ["Flour", "Milk"] {
            var item = RecipeDraft.Item()
            item.name = name
            item.quantity = 100
            item.unit = "g"
            draft.ingredients.append(item)
        }
        draft.instructionSteps = [RecipeDraft.Step()]
        draft.instructionSteps[0].description = "Mix the flour and milk."
        XCTAssertFalse(draft.hasUnreferencedIngredientAmounts)
        draft.instructionSteps[0].description = "Mix {{Flour|50%}} with milk."
        XCTAssertTrue(draft.hasUnreferencedIngredientAmounts)
        draft.instructionSteps[0].description = "Mix {{Flour|50%}} with {{Milk|100%}}."
        XCTAssertFalse(draft.hasUnreferencedIngredientAmounts)
    }

    func testImportSourceDispatchAndCrossDomainCopies() throws {
        let token = String(repeating: "a", count: 43)
        let share = try XCTUnwrap(URL(string: "https://kitchen.example/share.html#" + token))
        XCTAssertEqual(try RecipeImportLink.source(share.absoluteString), .onionary(share))
        let chefkoch = try XCTUnwrap(URL(string: "https://www.chefkoch.de/rezepte/123"))
        XCTAssertEqual(try RecipeImportLink.source(chefkoch.absoluteString), .chefkoch(chefkoch))
        let other = try XCTUnwrap(URL(string: "https://chefkoch.de.example/recipe"))
        XCTAssertEqual(try RecipeImportLink.source(other.absoluteString + "#part"), .website(other))
    }

    func testStructuredWebsiteDraftPreservesAmountsGroupsAndLanguageWithoutModel() throws {
        let html = #"""
            <script type="application/ld+json">{"@graph":[{"@type":"WebPage"},
              {"@type":"Recipe","name":"Birnenkuchen &amp; Creme","recipeYield":["4 Portionen"],
               "totalTime":"PT1H5M","recipeIngredient":["80 g Butter","1 1/2 EL Öl","½ Birne","2–3 Eier","Salz nach Bedarf"],
               "recipeInstructions":[{"@type":"HowToSection","name":"Füllung","itemListElement":[
                {"@type":"HowToStep","text":"40 g Butter schmelzen.","performTime":"PT2M"},
                {"@type":"HowToStep","text":"Birne schneiden."}]}]}]}</script>
            """#
        let draft = try XCTUnwrap(ExternalRecipePage.structuredDraft(from: html))
        XCTAssertEqual(draft.name, "Birnenkuchen & Creme")
        XCTAssertEqual(draft.servings, 4)
        XCTAssertEqual(draft.totalTimeMin, 65)
        XCTAssertEqual(draft.ingredients.map(\.name), ["Butter", "Öl", "Birne", "2–3 Eier", "Salz nach Bedarf"])
        XCTAssertEqual(draft.ingredients.map(\.quantity), [80, 1.5, 0.5, nil, nil])
        XCTAssertEqual(draft.ingredients[1].unit, "EL")
        XCTAssertEqual(draft.instructionSteps.map(\.groupName), ["Füllung", "Füllung"])
        XCTAssertEqual(draft.instructionSteps.map(\.stepNumber), [1, 2])
        XCTAssertEqual(draft.instructionSteps.first?.description, "{{Butter|50%}} schmelzen.")
        XCTAssertEqual(draft.instructionSteps.first?.durationMin, 2)
        XCTAssertNoThrow(try draft.validatedData())
    }

    func testIncompleteStructuredDataFallsBackToPageText() throws {
        let html = #"<script type="application/ld+json">{"@type":"Recipe","name":"Suppe","recipeIngredient":["Zwiebeln"]}</script><main><h1>Suppe</h1></main>"#
        XCTAssertNil(ExternalRecipePage.structuredDraft(from: html))
        XCTAssertTrue(try ExternalRecipePage.recipeText(from: html).contains("Zwiebeln"))
    }
    func testChefkochSharedTextAndTracking() throws {
        let link = "https://www.chefkoch.de/rezepte/4376441747840412/Unsichtbarer-Apfelkuchen.html?utm_source=com.apple.UIKit.activity.CopyToPasteboard&utm_medium=Social"
        XCTAssertEqual(try RecipeImportLink.sharedText("Try this recipe: " + link).absoluteString, link)
        XCTAssertThrowsError(try RecipeImportLink.accepted("https://chefkoch.de.evil.test/recipe"))
    }
    func testHTTPSWebRecipeIsSharedWithoutFragmentsOrCredentials() throws {
        let url = try RecipeImportLink.sharedText("Try https://food.example/cake#method")
        XCTAssertEqual(url.absoluteString, "https://food.example/cake")
        for link in ["http://food.example/cake", "https://user:pass@food.example/cake",
                     "https://10.0.0.1/cake", "https://food.local/cake", "https://food.example:8000/cake"] {
            XCTAssertThrowsError(try RecipeImportLink.webRecipe(link))
        }
    }
    func testRecipePagePrefersTheRecipeSchemaAndHandlesPlainHTML() throws {
        let structured = """
          <nav>Ignore this</nav>
          <script type="application/ld+json">
          {"@graph":[{"@type":"WebPage"},{"@type":"Recipe","name":"Apfelkuchen",
          "recipeIngredient":["40 g Äpfel"],"recipeInstructions":[{"text":"Schneiden."}],"image":"banner.png"}]}
          </script>
          """
        let extracted = try ExternalRecipePage.recipeText(from: structured)
        XCTAssertTrue(extracted.contains("40 g Äpfel"))
        XCTAssertTrue(extracted.contains("Schneiden."))
        XCTAssertFalse(extracted.contains("Ignore this"))
        XCTAssertFalse(extracted.contains("banner.png"))
        let plain = "<header><nav>Navigation</nav></header><main><h2>F&uuml;llung</h2><p>&frac12; Apfel&#44; geschnitten.</p></main>"
        XCTAssertEqual(try ExternalRecipePage.recipeText(from: plain), "Füllung\n½ Apfel, geschnitten.")
        XCTAssertThrowsError(try ExternalRecipePage.recipeText(from: String(repeating: "a", count: 12_001)))
    }
    func testBaseServingsInitializeCookingRatio() throws {
        let decoder = JSONDecoder(); decoder.keyDecodingStrategy = .convertFromSnakeCase
        let recipe = try decoder.decode(Recipe.self, from: Data(#"{"id":1,"household_id":1,"name":"Soup","servings":4,"ingredients":[],"instruction_steps":[]}"#.utf8))
        var adventure = Adventure(recipe: recipe)
        XCTAssertEqual(adventure.portions, 4)
        try adventure.scale(baseServings: 4, portions: Decimal(string: "1.53")!)
        XCTAssertEqual(adventure.portions, Decimal(string: "1.53")!)
        XCTAssertEqual(adventure.multiplier, Decimal(string: "0.3825")!)
    }

    func testStartingAtPreviewPortionsPreservesExistingProgress() throws {
        let recipe = try JSONDecoder().decode(Recipe.self, from: Data(#"{"id":1,"householdId":1,"name":"Soup","servings":4,"ingredients":[],"instructionSteps":[]}"#.utf8))
        var kitchen = Kitchen()
        XCTAssertThrowsError(try kitchen.visit(recipe, portions: 0))
        XCTAssertNil(kitchen.currentID)
        XCTAssertTrue(kitchen.adventures.isEmpty)
        try kitchen.visit(recipe, portions: 2)
        kitchen.adventures[0].toggle(key: "ingredient-1", label: "Cheese")
        try kitchen.visit(recipe, portions: Decimal(string: "1.53")!)
        let adventure = try XCTUnwrap(kitchen.adventures.first)
        XCTAssertEqual(adventure.portions, Decimal(string: "1.53"))
        XCTAssertEqual(adventure.checked, ["ingredient-1"])
        XCTAssertEqual(adventure.history.count, 1)
    }
    func testChefkochURLBoundary() throws {
        XCTAssertNoThrow(try RecipeImportLink.chefkoch("https://www.chefkoch.de/rezepte/123"))
        for url in ["http://chefkoch.de/123", "https://chefkoch.de.evil.org/123", "https://chefkoch.de@evil.org/123", "https://chefkoch.de:8443/123", "file:///tmp/test"] {
            XCTAssertThrowsError(try RecipeImportLink.chefkoch(url))
        }
    }
    func testDraftValidationAndWireFormat() throws {
        var draft = RecipeDraft()
        XCTAssertThrowsError(try draft.validatedData())
        draft.name = "Soup"
        var step = RecipeDraft.Step(); step.description = "Stir"; step.stepNumber = 9
        draft.instructionSteps = [step]
        let data = try draft.validatedData()
        let json = try XCTUnwrap(JSONSerialization.jsonObject(with: data) as? [String: Any])
        let steps = try XCTUnwrap(json["instruction_steps"] as? [[String: Any]])
        XCTAssertEqual(steps[0]["step_number"] as? Int, 1)
        XCTAssertNil(steps[0]["id"])
        var item = RecipeDraft.Item(); item.name = "Salt"; item.quantity = -1
        draft.ingredients = [item]
        XCTAssertThrowsError(try draft.validatedData())
    }
    func testEditingPreservesMetadataAndConvertsTags() throws {
        let data = Data(#"{"name":"Soup","notes":"Note","total_time_min":20,"active_cooking_time_min":10,"kcal_per_serving":123.5,"tags":[{"id":1,"name":"vegan"}],"ingredients":[],"instruction_steps":[]}"#.utf8)
        let draft = try RecipeDraft.fromRecipeResponse(data)
        XCTAssertEqual(draft.tags, ["vegan"])
        XCTAssertEqual(draft.activeCookingTimeMin, 10)
        XCTAssertEqual(draft.kcalPerServing, Decimal(string: "123.5"))
        let output = try XCTUnwrap(JSONSerialization.jsonObject(with: draft.validatedData()) as? [String: Any])
        XCTAssertEqual(output["tags"] as? [String], ["vegan"])
    }

    func testClearingMetadataEncodesExplicitNullForPartialUpdate() throws {
        var draft = RecipeDraft(); draft.name = "Soup"
        let payload = try XCTUnwrap(JSONSerialization.jsonObject(with: draft.validatedData()) as? [String: Any])
        XCTAssertTrue(payload["total_time_min"] is NSNull)
        XCTAssertTrue(payload["active_cooking_time_min"] is NSNull)
        XCTAssertTrue(payload["kcal_per_serving"] is NSNull)
    }
    func testSharedLinkShape() throws {
        let token = String(repeating: "a", count: 43)
        XCTAssertNoThrow(try RecipeImportLink.accepted("https://recipes.example/share.html#" + token))
        for url in ["https://recipes.example/other#" + token, "https://recipes.example/share.html#short", "https://recipes.example/share.html?x=1#" + token] {
            XCTAssertThrowsError(try RecipeImportLink.sharedRecipe(url))
        }
    }

}
