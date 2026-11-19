import XCTest
@testable import OnionaryCore

final class RecipeTimeTests: XCTestCase {
    func testTimeTokensAndLegacyDurations() throws {
        let time = try XCTUnwrap(RecipeTime("1h2m30s"))
        XCTAssertEqual(time.seconds, 3750)
        XCTAssertEqual(time.placeholder, "{{time|3750s}}")
        XCTAssertEqual(RecipeTime.stepMinutes(8)?.seconds, 480)
        XCTAssertNil(RecipeTime.stepMinutes(Int.max))
        for value in ["", "0s", "25h", "-2m", "2m\n", "9s5m"] {
            XCTAssertNil(RecipeTime(value), value)
        }
    }

    func testTimersKeepTheirDurationWhenPortionsChange() throws {
        let ingredient = Ingredient(id: 1, name: "Cheese", quantity: 40, unit: "g")
        let source = "Cook {{Cheese|100%}} for {{time|10m}}; leave {{time|grace}} as written."
        let original = IngredientPlaceholders.parts(source, ingredients: [ingredient], multiplier: 1)
        let scaled = IngredientPlaceholders.parts(source, ingredients: [ingredient], multiplier: 2)
        XCTAssertEqual(original[3], scaled[3])
        guard case .time(let time, _) = scaled[3] else { return XCTFail("Expected a time reference") }
        XCTAssertEqual(time.seconds, 600)
        XCTAssertTrue(scaled.map(\.text).joined().contains("80 g Cheese"))
        XCTAssertTrue(scaled.map(\.text).joined().contains("{{time|grace}}"))
    }

    func testCountdownPersistsDeadlineAndDoesNotRestartOnRepeatedTap() throws {
        let start = Date(timeIntervalSince1970: 100)
        let time = try XCTUnwrap(RecipeTime("20s"))
        var kitchen = Kitchen()
        XCTAssertTrue(kitchen.startTimer(id: "cake-oven", title: "Cake", time: time, now: start))
        XCTAssertFalse(kitchen.startTimer(id: "cake-oven", title: "Cake", time: time, now: start + 10))
        var restored = try JSONDecoder().decode(Kitchen.self, from: JSONEncoder().encode(kitchen))
        let timer = try XCTUnwrap(restored.cookingTimers.first)
        XCTAssertEqual(timer.remaining(at: start + 10), 10)
        XCTAssertEqual(timer.remaining(at: start + 21), 0)
        restored.removeTimer(timer.id)
        XCTAssertTrue(restored.cookingTimers.isEmpty)
    }
}
