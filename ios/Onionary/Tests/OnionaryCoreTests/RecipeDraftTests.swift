import XCTest
@testable import OnionaryCore

final class RecipeDraftTests: XCTestCase {
    func testChefkochSharedTextAndTracking() throws {
        let link = "https://www.chefkoch.de/rezepte/4376441747840412/Unsichtbarer-Apfelkuchen.html?utm_source=com.apple.UIKit.activity.CopyToPasteboard&utm_medium=Social"
        XCTAssertEqual(try RecipeImportLink.sharedText("Try this recipe: " + link).absoluteString, link)
        XCTAssertThrowsError(try RecipeImportLink.sharedText("https://chefkoch.de.evil.test/recipe"))
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
