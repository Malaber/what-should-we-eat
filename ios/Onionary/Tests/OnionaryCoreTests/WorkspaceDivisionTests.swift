import CoreGraphics
import XCTest
@testable import OnionaryCore

final class WorkspaceDivisionTests: XCTestCase {
    func testKeyboardClipsHingeToAvailableViewport() {
        let clipped = WorkspaceDivision.visible(CGRect(x: 380, y: -20, width: 40, height: 900), in: CGSize(width: 400, height: 300))
        XCTAssertEqual(clipped, CGRect(x: 380, y: 0, width: 20, height: 300))
        XCTAssertEqual(clipped.map { 400 - $0.maxX }, 0)
    }

    func testOffscreenAndInvalidDivisionsDoNotSplit() {
        let size = CGSize(width: 400, height: 300)
        XCTAssertNil(WorkspaceDivision.visible(CGRect(x: 0, y: 350, width: 400, height: 20), in: size))
        XCTAssertNil(WorkspaceDivision.visible(CGRect(x: 0, y: 0, width: CGFloat.infinity, height: 20), in: size))
        XCTAssertNil(WorkspaceDivision.visible(CGRect(x: 0, y: 0, width: 20, height: 300), in: .zero))
    }
}
