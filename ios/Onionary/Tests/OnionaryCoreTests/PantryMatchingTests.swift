import XCTest
@testable import OnionaryCore
final class PantryMatchingTests: XCTestCase {
    func testGermanInputAndMissingQuantities() {
        let input = PantryMatching.parse("Habe 3 Bananen und 2 Eier\n150 ml Milch\nMehl")
        XCTAssertEqual(input.count, 4)
        XCTAssertEqual(input[0].quantity, 3)
        XCTAssertEqual(input[2].unit, "ml")
        XCTAssertNil(input[3].quantity)
    }
    func testGroupsAggregateAndUnitsAreNotGuessed() throws {
        let recipe = try JSONDecoder().decode(Recipe.self, from: Data(#"{"id":1,"householdId":1,"name":"Cake","ingredients":[{"id":1,"name":"Milch","quantity":100,"unit":"ml"},{"id":2,"name":"Milch","quantity":100,"unit":"ml"},{"id":3,"name":"Mehl","quantity":50,"unit":"g"}],"instructionSteps":[]}"#.utf8))
        let short = PantryMatching.matches([recipe], supplies: PantryMatching.parse("150 ml Milch"))[0]
        XCTAssertEqual(short.short, ["Milch"])
        XCTAssertEqual(short.missing, ["Mehl"])
        let unknown = PantryMatching.matches([recipe], supplies: PantryMatching.parse("1 l Milch"))[0]
        XCTAssertEqual(unknown.unchecked, ["Milch"])
        XCTAssertTrue(unknown.short.isEmpty)
    }
}
