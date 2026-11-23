import XCTest
@testable import OnionaryCore

final class CookingSnapshotTests: XCTestCase {
    func testSnapshotTracksCheckUndoScaleAndNextStep() throws {
        let recipe = try JSONDecoder().decode(Recipe.self, from: Data(#"{"id":1,"householdId":1,"name":"Milk soup","ingredients":[{"id":1,"name":"Milk","quantity":100,"unit":"ml"}],"instructionSteps":[{"id":1,"stepNumber":1,"description":"Use {{Milk|80%}}"},{"id":2,"stepNumber":2,"description":"Serve"}]}"#.utf8))
        var adventure = Adventure(recipe: recipe)
        let used = Adventure.ingredientUseKey(stepID: 1, part: 1)
        adventure.toggle(key: used, label: "Use milk")
        XCTAssertFalse(adventure.checked.contains("ingredient-1"))
        XCTAssertEqual(CookingSnapshot(adventure).checked, 0)
        let restored = try JSONDecoder().decode(Adventure.self, from: JSONEncoder().encode(adventure))
        XCTAssertTrue(restored.checked.contains(used))
        XCTAssertNotEqual(used, Adventure.ingredientUseKey(stepID: 1, part: 3))
        XCTAssertNotEqual(used, Adventure.ingredientUseKey(stepID: 2, part: 1))
        adventure.undo()
        XCTAssertFalse(adventure.checked.contains(used))
        try adventure.scale(multiplier: 2)
        XCTAssertEqual(CookingSnapshot(adventure, locale: Locale(identifier: "en")).nextStep, "Use 160 ml Milk")
        adventure.toggle(key: "step-1", label: "Use milk")
        XCTAssertEqual(CookingSnapshot(adventure).nextStep, "Serve")
        XCTAssertEqual(CookingSnapshot(adventure).checked, 1)
        adventure.undo()
        XCTAssertEqual(CookingSnapshot(adventure).checked, 0)
        adventure.redo()
        adventure.toggle(key: "ingredient-1", label: "Milk")
        adventure.toggle(key: "step-2", label: "Serve")
        XCTAssertTrue(CookingSnapshot(adventure).complete)
        let data = try JSONEncoder().encode(CookingSnapshot(adventure))
        XCTAssertLessThan(data.count, 4096)
        XCTAssertEqual(try JSONDecoder().decode(CookingSnapshot.self, from: data), CookingSnapshot(adventure))
    }
}
