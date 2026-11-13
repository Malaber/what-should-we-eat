import XCTest

/// Validate geometry, then let the native tap compute its synchronized hit point.
/// A separate hit-test read can error on a stale snapshot after a fold.
enum UIReadiness {
    static func validControlFrame(_ frame: CGRect, in viewport: CGRect) -> Bool {
        let values = [frame.minX, frame.minY, frame.width, frame.height,
                      viewport.minX, viewport.minY, viewport.width, viewport.height]
        guard values.allSatisfy(\.isFinite), !frame.isEmpty, !viewport.isEmpty else { return false }
        return viewport.contains(CGPoint(x: frame.midX, y: frame.midY))
    }

    @MainActor static func button(_ title: String, in app: XCUIApplication) -> XCUIElement {
        let recipeID = title.hasPrefix("recipe-") && !title.dropFirst(7).isEmpty && title.dropFirst(7).allSatisfy(\.isNumber)
        let shopping = title == "Generate shopping list" || title == "Refresh shopping list" || title.hasPrefix("shopping-")
        let query: XCUIElementQuery
        if recipeID { query = app.collectionViews["recipe-list"].buttons.matching(identifier: title) }
        else if shopping { query = app.collectionViews["shopping-list"].buttons.matching(identifier: title) }
        else { query = app.buttons.matching(identifier: title) }
        return query.element(boundBy: 0)
    }

    @MainActor static func waitForValue(_ expected: String, matching query: XCUIElementQuery) -> Bool {
        // Match the committed value in the native AX query. An outer predicate
        // expectation can expire while a nested element.value RPC is in flight,
        // even when the field already contains the exact expected text.
        query.matching(NSPredicate(format: "value == %@", expected))
            .element(boundBy: 0).waitForExistence(timeout: 5)
    }

    static func duoViewport(_ frame: CGRect, angle: Int) -> Bool {
        guard [0, 90, 180].contains(angle) else { return false }
        let expected = angle == 0 ? CGSize(width: 466, height: 678) : CGSize(width: 669, height: 951)
        // XCTest can normalize display coordinates independently of the requested
        // orientation. Check both edge lengths, rather than area or axis order.
        return abs(min(frame.width, frame.height) - expected.width) < 1
            && abs(max(frame.width, frame.height) - expected.height) < 1
    }
}
