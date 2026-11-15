import CoreGraphics
import Foundation

/// A hinge can extend outside the viewport while the keyboard or a sheet resizes
/// it. Only the visible intersection may participate in pane sizing.
public enum WorkspaceDivision {
    public static func visible(_ division: CGRect, in size: CGSize) -> CGRect? {
        let values = [division.origin.x, division.origin.y, division.width, division.height, size.width, size.height]
        guard values.allSatisfy({ $0.isFinite }), size.width > 0, size.height > 0 else { return nil }
        let clipped = division.intersection(CGRect(origin: .zero, size: size))
        return clipped.isNull || clipped.isEmpty ? nil : clipped
    }
}
