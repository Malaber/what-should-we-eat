import XCTest

/// Inspect geometry before hittability: XCTest can record a failure merely
/// asking for the activation point of a hidden/stale element after a fold.
enum UIReadiness {
    static func validControlFrame(_ frame: CGRect, in viewport: CGRect) -> Bool {
        let values = [frame.minX, frame.minY, frame.width, frame.height,
                      viewport.minX, viewport.minY, viewport.width, viewport.height]
        guard values.allSatisfy(\.isFinite), !frame.isEmpty, !viewport.isEmpty else { return false }
        return viewport.contains(CGPoint(x: frame.midX, y: frame.midY))
    }

    @MainActor static func button(_ title: String, in app: XCUIApplication) -> XCUIElement {
        let recipeID = title.hasPrefix("recipe-") && !title.dropFirst(7).isEmpty && title.dropFirst(7).allSatisfy(\.isNumber)
        let query = recipeID ? app.collectionViews["recipe-list"].buttons.matching(identifier: title) : app.buttons.matching(identifier: title)
        return query.element(boundBy: 0)
    }

    @MainActor static func waitForValue(_ expected: String, in element: XCUIElement) -> Bool {
        let committed = XCTNSPredicateExpectation(predicate: NSPredicate(format: "value == %@", expected), object: element)
        return XCTWaiter.wait(for: [committed], timeout: 5) == .completed
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
