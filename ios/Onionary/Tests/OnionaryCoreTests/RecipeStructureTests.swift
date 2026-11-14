import XCTest
@testable import OnionaryCore
final class RecipeStructureTests: XCTestCase {
    func testDraftPreservesIconGroupsAndOrder() throws {
        let data = Data(#"{"name":"Cake","icon":"🥧","servings":2,"ingredients":[{"name":"Flour","group_name":"Dough"},{"name":"Milk","group_name":"Filling"}],"instruction_steps":[{"step_number":1,"description":"Mix","group_name":"Dough"}],"tags":[{"id":1,"name":"Baking"}]}"#.utf8)
        var draft = try RecipeDraft.fromRecipeResponse(data)
        XCTAssertEqual(draft.tags, ["Baking"])
        draft.ingredients.reverse()
        let json = try XCTUnwrap(JSONSerialization.jsonObject(with: draft.validatedData()) as? [String: Any])
        XCTAssertEqual(json["icon"] as? String, "🥧")
        let ingredients = try XCTUnwrap(json["ingredients"] as? [[String: Any]])
        XCTAssertEqual(ingredients[0]["name"] as? String, "Milk")
        XCTAssertEqual(ingredients[0]["group_name"] as? String, "Filling")
        XCTAssertEqual(FoodIcons.display("unsupported"), "🍽️")
    }

    func testFoodIconAcceptsOneEmojiOutsideTheFormerPicker() {
        for emoji in ["⚡", "🧑🏽‍🍳", "🇩🇪", "1️⃣", "♥️", "🥥"] {
            XCTAssertEqual(FoodIcons.emoji(" \(emoji) "), emoji)
            XCTAssertEqual(FoodIcons.display(emoji), emoji)
        }
        for invalid in ["", "1", "#", "👩🍳", "a🥥", "🇩", "♥\u{FE0E}"] {
            XCTAssertNil(FoodIcons.emoji(invalid))
        }
    }
}
