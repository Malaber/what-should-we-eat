import XCTest
@testable import OnionaryCore

final class KitchenWidgetTests: XCTestCase {
    func testWeekExpiryAndAccountScopedLinks() throws {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(secondsFromGMT: 0)!
        let sunday = ISO8601DateFormatter().date(from: "2026-10-11T23:00:00Z")!
        let snapshot = KitchenWidgetSnapshot(scope: "account-a", meals: [.init(id: 7, name: "Soup", cooked: false)], now: sunday, calendar: calendar)
        XCTAssertTrue(snapshot.isCurrent(at: sunday))
        XCTAssertFalse(snapshot.isCurrent(at: sunday.addingTimeInterval(3600)))
        XCTAssertEqual(KitchenDeepLink.destination(snapshot.link(recipeID: 7), scope: "account-a"), .recipe(7))
        XCTAssertNil(KitchenDeepLink.destination(snapshot.link(recipeID: 7), scope: "account-b"))
        XCTAssertNil(KitchenDeepLink.destination(URL(string: "https://example.com/kitchen?scope=account-a")!, scope: "account-a"))
        XCTAssertEqual(try JSONDecoder().decode(KitchenWidgetSnapshot.self, from: JSONEncoder().encode(snapshot)), snapshot)
    }
}
