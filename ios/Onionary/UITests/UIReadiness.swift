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

    @MainActor static func visibleButtons(_ title: String, in app: XCUIApplication) -> [XCUIElement] {
        guard app.state == .runningForeground else { return [] }
        // Duo's application frame stays in display coordinates while window
        // and control frames follow interface orientation (669×951 vs 951×669).
        // Compare controls only with windows in the same coordinate space.
        let viewports = app.windows.allElementsBoundByIndex.map(\.frame)
        let recipeID = title.hasPrefix("recipe-") && !title.dropFirst(7).isEmpty && title.dropFirst(7).allSatisfy(\.isNumber)
        let query = recipeID ? app.collectionViews["recipe-list"].buttons.matching(identifier: title) : app.buttons.matching(identifier: title)
        return query.allElementsBoundByIndex.filter {
            let frame = $0.frame
            return viewports.contains { validControlFrame(frame, in: $0) } && $0.isHittable
        }
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
