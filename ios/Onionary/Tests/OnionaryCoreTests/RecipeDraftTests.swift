import XCTest
@testable import OnionaryCore

final class RecipeDraftTests: XCTestCase {
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

}
