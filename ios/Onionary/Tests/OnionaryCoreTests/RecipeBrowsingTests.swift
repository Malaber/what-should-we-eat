import XCTest
@testable import OnionaryCore

final class RecipeBrowsingTests: XCTestCase {
    func testSearchIncludesTagsIngredientsAndCategoryIntersection() throws {
        let decoder = JSONDecoder(); decoder.keyDecodingStrategy = .convertFromSnakeCase
        let recipes = try decoder.decode([Recipe].self, from: Data(#"[{"id":1,"household_id":1,"name":"Pasta","tags":[{"id":1,"name":"Vegetarian"}],"ingredients":[{"id":1,"name":"Milk","quantity":100,"unit":"ml"}],"instruction_steps":[]},{"id":2,"household_id":1,"name":"Soup","tags":[{"id":2,"name":"Quick"}],"total_time_min":10,"ingredients":[],"instruction_steps":[]}]"#.utf8))
        XCTAssertTrue(RecipeBrowsing.recipes(recipes, categories: ["Vegetarian", "Quick"]).isEmpty)
        XCTAssertEqual(RecipeBrowsing.recipes(recipes, categories: ["vegetarian"]).map(\.id), [1])
        XCTAssertEqual(RecipeBrowsing.recipes(recipes, query: "vegetarian milk").map(\.id), [1])
        XCTAssertTrue(RecipeBrowsing.recipes(recipes, query: "milk", category: "Quick").isEmpty)
        XCTAssertEqual(RecipeBrowsing.categories(recipes, query: "VEG"), ["Vegetarian"])
        XCTAssertEqual(RecipeBrowsing.recipes(recipes, sort: .quickest).map(\.id), [2, 1])
        XCTAssertEqual(RecipeBrowsing.recipes(recipes, sort: .ingredients).map(\.id), [2, 1])
        XCTAssertEqual(RecipeBrowsing.recipes(recipes, sort: .ingredients, reversed: true).map(\.id), [1, 2])
        XCTAssertEqual(RecipeBrowsing.recipes(recipes, reversed: true).map(\.id), [2, 1])
    }
    func testNewestUsesCreationDateBeforeLegacyIDOrder() throws {
        let source = #"[{"id":1,"householdId":1,"name":"Soup","createdAt":"2026-11-15T13:00:00.123+01:00","ingredients":[],"instructionSteps":[]},{"id":30,"householdId":1,"name":"Bread","createdAt":"2026-11-15T11:30:00Z","ingredients":[],"instructionSteps":[]},{"id":40,"householdId":1,"name":"Older cache","ingredients":[],"instructionSteps":[]}]"#
        let recipes = try JSONDecoder().decode([Recipe].self, from: Data(source.utf8))
        XCTAssertEqual(RecipeBrowsing.recipes(recipes, sort: .newest).map(\.id), [1, 30, 40])
        XCTAssertEqual(RecipeBrowsing.recipes(recipes, sort: .newest, reversed: true).map(\.id), [40, 30, 1])
    }
    func testOldSavedRecipeWithoutTagsStillDecodes() throws {
        let recipe = try JSONDecoder().decode(Recipe.self, from: Data(#"{"id":1,"householdId":1,"name":"Old","ingredients":[],"instructionSteps":[]}"#.utf8))
        XCTAssertTrue(RecipeBrowsing.categories([recipe]).isEmpty)
    }
}
