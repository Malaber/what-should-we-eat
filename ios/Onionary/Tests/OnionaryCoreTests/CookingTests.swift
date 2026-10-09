import Foundation
import Testing
@testable import OnionaryCore

private func recipe(_ id: Int = 1) throws -> Recipe {
    let data = Data("""
    {"id":\(id),"household_id":1,"name":"Pasta","ingredients":[
    {"id":1,"name":"Cheese","quantity":200,"unit":"g"},
    {"id":2,"name":"Pasta","quantity":250,"unit":"g"},
    {"id":3,"name":"Salt","quantity":null,"unit":null}],
    "instruction_steps":[{"id":1,"step_number":1,"description":"Cook","duration_min":10}]}
    """.utf8)
    let decoder = JSONDecoder(); decoder.keyDecodingStrategy = .convertFromSnakeCase
    return try decoder.decode(Recipe.self, from: data)
}

@Test func exactScalingAndAvailableIngredient() throws {
    let recipe = try recipe()
    var adventure = Adventure(recipe: recipe)
    try adventure.scale(multiplier: Numbers.parse("1.583945"))
    #expect(adventure.quantity(recipe.ingredients[0]) == Decimal(string: "316.789"))
    try adventure.scale(ingredient: recipe.ingredients[0], available: 170)
    #expect(adventure.multiplier == Decimal(string: "0.85"))
    #expect(adventure.quantity(recipe.ingredients[0]) == 170)
    #expect(adventure.quantity(recipe.ingredients[1]) == Decimal(string: "212.5"))
    #expect(adventure.quantity(recipe.ingredients[2]) == nil)
    #expect(adventure.recipe.instructionSteps[0].durationMin == 10)
    // Repeated changes always use the original recipe, never compound prior scaling.
    try adventure.scale(ingredient: recipe.ingredients[0], available: 170)
    #expect(adventure.multiplier == Decimal(string: "0.85"))
    try adventure.scale(baseServings: 4, portions: Numbers.parse("1,583945"))
    #expect(adventure.portions == Decimal(string: "1.583945"))
}

@Test func invalidQuantitiesCannotDamageSession() throws {
    for text in ["", "0", "-1", "NaN", "1x", "1.2.3", "1000000001", "1e99"] {
        #expect(throws: CookingError.self) { try Numbers.parse(text) }
    }
    var adventure = Adventure(recipe: try recipe())
    #expect(throws: CookingError.self) { try adventure.scale(multiplier: .nan) }
    #expect(throws: CookingError.self) { try adventure.scale(baseServings: 0, portions: 1) }
    #expect(throws: CookingError.self) { try adventure.scale(ingredient: adventure.recipe.ingredients[2], available: 170) }
    #expect(adventure.multiplier == 1)
}

@Test func checksUnchecksAndUndoKeepTimestampedHistory() throws {
    var adventure = Adventure(recipe: try recipe())
    let t = Date(timeIntervalSince1970: 100)
    adventure.toggle(key: "ingredient-1", label: "Cheese", now: t)
    adventure.toggle(key: "ingredient-1", label: "Cheese", now: t.addingTimeInterval(1))
    #expect(!adventure.checked.contains("ingredient-1"))
    adventure.undo(now: t.addingTimeInterval(2))
    #expect(adventure.checked.contains("ingredient-1"))
    adventure.undo(now: t.addingTimeInterval(3))
    #expect(adventure.checked.isEmpty)
    #expect(!adventure.canUndo)
    #expect(adventure.history.count == 4)
    #expect(adventure.history[2].undoes == adventure.history[1].id)
    #expect(adventure.history[3].timestamp == t.addingTimeInterval(3))
    adventure.undo()
    #expect(adventure.history.count == 4)
}

@Test func restoreCurrentRecipeScalingHistoryAndUndoFromDisk() throws {
    let folder = FileManager.default.temporaryDirectory.appending(path: UUID().uuidString)
    defer { try? FileManager.default.removeItem(at: folder) }
    let file = folder.appending(path: "kitchen.json")
    var kitchen = Kitchen()
    kitchen.visit(try recipe(), now: Date(timeIntervalSince1970: 100))
    kitchen.adventures[0].toggle(key: "step-1", label: "Cook")
    try kitchen.adventures[0].scale(multiplier: Numbers.parse("1.583945"))
    kitchen.visit(try recipe(2), now: Date(timeIntervalSince1970: 200))
    kitchen.visit(try recipe(), now: Date(timeIntervalSince1970: 300))
    try KitchenFile.write(kitchen, to: file)
    var restored = try KitchenFile.read(file)
    #expect(restored == kitchen)
    #expect(restored.currentID == 1)
    #expect(restored.recent.map(\.id) == [1, 2])
    restored.adventures[0].undo()
    #expect(restored.adventures[0].checked.isEmpty)
}

@Test func corruptFileIsReportedAndNeverSilentlyReplaced() throws {
    let file = FileManager.default.temporaryDirectory.appending(path: UUID().uuidString)
    defer { try? FileManager.default.removeItem(at: file) }
    try Data("broken".utf8).write(to: file)
    #expect(throws: (any Error).self) { try KitchenFile.read(file) }
    #expect(try String(contentsOf: file, encoding: .utf8) == "broken")
}

@Test func customBackendValidation() throws {
    #expect(try Backend.url(" https://Kitchen.Example:8443/ ").absoluteString == "https://kitchen.example:8443")
    for value in ["http://example.com", "https://user:pass@example.com", "https://example.com/api", "https://example.com?token=1", "https://example.com#foo", "file:///tmp/a"] {
        #expect(throws: CookingError.self) { try Backend.url(value) }
    }
}

@Test func presentationRoundingPreservesPrecision() throws {
    let number = try Numbers.parse("193552.666666666666666")
    #expect(Numbers.display(number, locale: Locale(identifier: "de_DE")) == "193552,67")
    #expect(Numbers.display(1, locale: Locale(identifier: "en_US")) == "1")
    #expect(Numbers.text(number) == "193552.666666666666666")
}

@Test func redoSurvivesRestoreAndNewActionsDiscardRedo() throws {
    var adventure = Adventure(recipe: try recipe())
    adventure.toggle(key: "ingredient-1", label: "Cheese")
    adventure.undo()
    adventure = try JSONDecoder().decode(Adventure.self, from: JSONEncoder().encode(adventure))
    #expect(adventure.canRedo)
    adventure.redo()
    #expect(adventure.checked.contains("ingredient-1"))
    #expect(adventure.history.last?.redoes == adventure.history.first?.id)
    adventure.undo()
    adventure.toggle(key: "step-1", label: "Cook")
    #expect(!adventure.canRedo)
    #expect(adventure.checked == ["step-1"])
    var legacy = try JSONSerialization.jsonObject(with: JSONEncoder().encode(adventure)) as! [String: Any]
    legacy.removeValue(forKey: "redoStack")
    let decoded = try JSONDecoder().decode(Adventure.self, from: JSONSerialization.data(withJSONObject: legacy))
    #expect(!decoded.canRedo)
    #expect(decoded.checked == adventure.checked)
}
