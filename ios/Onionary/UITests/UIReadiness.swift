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
        buttons(title, in: app).element(boundBy: 0)
    }

    @MainActor static func buttons(_ title: String, in root: XCUIElement) -> XCUIElementQuery {
        let recipeID = title.hasPrefix("recipe-") && !title.dropFirst(7).isEmpty && title.dropFirst(7).allSatisfy(\.isNumber)
        let shopping = title == "Generate shopping list" || title == "Refresh shopping list" || title.hasPrefix("shopping-")
        if recipeID { return root.collectionViews["recipe-list"].buttons.matching(identifier: title) }
        if shopping { return root.collectionViews["shopping-list"].buttons.matching(identifier: title) }
        return root.buttons.matching(identifier: title)
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

    static func duoWindow(_ frame: CGRect, angle: Int) -> Bool {
        guard duoViewport(frame, angle: angle) else { return false }
        // The app root uses natural display coordinates. Its shape alone does
        // not establish the orientation of the window that receives touches.
        return angle == 0 ? frame.height > frame.width : frame.width > frame.height
    }
}
