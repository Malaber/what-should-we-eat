import XCTest
@testable import OnionaryCore
final class RecipeLanguageTests: XCTestCase {
    func testFormattingAndGenerationHaveDistinctConstraints() {
        XCTAssertTrue(RecipeAIMode.format.instruction.contains("Do not invent"))
        XCTAssertTrue(RecipeAIMode.format.instruction.contains("null"))
        XCTAssertTrue(RecipeAIMode.generate.instruction.contains("may invent"))
    }
    func testLanguageDoesNotFollowDeviceLocale() {
        XCTAssertTrue(RecipeLanguage.automatic.instruction.contains("German input must remain German"))
        XCTAssertTrue(RecipeLanguage.german.instruction.contains("Deutsch"))
        XCTAssertTrue(RecipeLanguage.english.instruction.contains("regardless of input"))
    }
}
