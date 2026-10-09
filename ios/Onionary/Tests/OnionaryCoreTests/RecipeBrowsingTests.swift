import XCTest
@testable import OnionaryCore

final class RecipeBrowsingTests: XCTestCase {
    func testSearchIncludesTagsIngredientsAndCategoryIntersection() throws {
        let decoder = JSONDecoder(); decoder.keyDecodingStrategy = .convertFromSnakeCase
        let recipes = try decoder.decode([Recipe].self, from: Data(#"[{"id":1,"household_id":1,"name":"Pasta","tags":[{"id":1,"name":"Vegetarian"}],"ingredients":[{"id":1,"name":"Milk","quantity":100,"unit":"ml"}],"instruction_steps":[]},{"id":2,"household_id":1,"name":"Soup","tags":[{"id":2,"name":"Quick"}],"total_time_min":10,"ingredients":[],"instruction_steps":[]}]"#.utf8))
        XCTAssertEqual(RecipeBrowsing.recipes(recipes, query: "vegetarian milk").map(\.id), [1])
        XCTAssertTrue(RecipeBrowsing.recipes(recipes, query: "milk", category: "Quick").isEmpty)
        XCTAssertEqual(RecipeBrowsing.categories(recipes, query: "VEG"), ["Vegetarian"])
        XCTAssertEqual(RecipeBrowsing.recipes(recipes, quickestFirst: true).map(\.id), [2, 1])
    }
    func testOldSavedRecipeWithoutTagsStillDecodes() throws {
        let recipe = try JSONDecoder().decode(Recipe.self, from: Data(#"{"id":1,"householdId":1,"name":"Old","ingredients":[],"instructionSteps":[]}"#.utf8))
        XCTAssertTrue(RecipeBrowsing.categories([recipe]).isEmpty)
    }
}
