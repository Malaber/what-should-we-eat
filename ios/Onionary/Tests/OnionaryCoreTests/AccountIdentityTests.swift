import XCTest
@testable import OnionaryCore

final class AccountIdentityTests: XCTestCase {
    func testEmailHintHidesLocalPart() {
        XCTAssertEqual(AccountIdentity.maskedEmail("cook@example.org"), "c***@example.org")
        XCTAssertEqual(AccountIdentity.maskedEmail("a@example.org"), "a***@example.org")
        XCTAssertEqual(AccountIdentity.maskedEmail(""), "***")
        XCTAssertEqual(AccountIdentity.maskedEmail("not-an-address"), "***")
    }
}
