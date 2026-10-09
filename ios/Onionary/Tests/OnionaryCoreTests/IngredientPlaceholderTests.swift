import XCTest
@testable import OnionaryCore

final class IngredientPlaceholderTests: XCTestCase {
    func testPercentagesTrackPortionsAndRoundOnlyDisplay() throws {
        let ingredients = try JSONDecoder().decode([Ingredient].self, from: Data(#"[{"id":1,"name":"Milk","quantity":100,"unit":"ml"}]"#.utf8))
        let render: (String, Decimal) -> String = { IngredientPlaceholders.resolve($0, ingredients: ingredients, multiplier: $1, locale: Locale(identifier: "en_US")) }
        XCTAssertEqual(render("Use {{Milk|80%}}, then {{Milk|20%}}.", 1), "Use 80 ml Milk, then 20 ml Milk.")
        XCTAssertEqual(render("{{milk|80%}}", Decimal(string: "1.583945")!), "126.72 ml Milk")
        XCTAssertEqual(render("{{Milk|12,5%}}", 2), "25 ml Milk")
        XCTAssertEqual(render("{{Milk|101%}} {{missing|80%}}", 1), "{{Milk|101%}} {{missing|80%}}")
        XCTAssertEqual(IngredientPlaceholders.resolve("{{Milk|80%}}", ingredients: ingredients + ingredients), "{{Milk|80%}}")
        XCTAssertEqual(render("Heat for 80 minutes", 2), "Heat for 80 minutes")
    }
}
