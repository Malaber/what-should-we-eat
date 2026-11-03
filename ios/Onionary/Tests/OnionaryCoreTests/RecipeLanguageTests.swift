import XCTest
@testable import OnionaryCore
final class RecipeLanguageTests: XCTestCase {
    func testLanguageDoesNotFollowDeviceLocale() {
        XCTAssertTrue(RecipeLanguage.automatic.instruction.contains("German input must remain German"))
        XCTAssertTrue(RecipeLanguage.german.instruction.contains("Deutsch"))
        XCTAssertTrue(RecipeLanguage.english.instruction.contains("regardless of input"))
    }
}
