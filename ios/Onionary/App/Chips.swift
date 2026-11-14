import SwiftUI

struct RemovableChip: View {
    let title: String
    let removeLabel: String
    let remove: () -> Void

    var body: some View {
        Button(action: remove) {
            HStack(spacing: 6) {
                Text(title)
                Image(systemName: "xmark").font(.caption.weight(.semibold)).accessibilityHidden(true)
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 4)
            .background(OnionaryTheme.accent.opacity(0.15), in: Capsule())
            .overlay { Capsule().strokeBorder(OnionaryTheme.accent.opacity(0.45)) }
            .frame(minHeight: 44)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityLabel(Text(removeLabel))
    }
}

struct ChipFlow: Layout {
    let spacing: CGFloat

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        arrange(width: proposal.width ?? .infinity, subviews: subviews) { _, _, _ in }
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        _ = arrange(width: bounds.width, subviews: subviews) { view, origin, size in
            view.place(at: CGPoint(x: bounds.minX + origin.x, y: bounds.minY + origin.y),
                       anchor: .topLeading, proposal: ProposedViewSize(size))
        }
    }

    private func arrange(width: CGFloat, subviews: Subviews, place: (LayoutSubview, CGPoint, CGSize) -> Void) -> CGSize {
        var x: CGFloat = 0
        var y: CGFloat = 0
        var rowHeight: CGFloat = 0
        var usedWidth: CGFloat = 0
        for view in subviews {
            let proposedWidth = min(view.sizeThatFits(.unspecified).width, width)
            let size = view.sizeThatFits(ProposedViewSize(width: proposedWidth, height: nil))
            if x > 0, x + size.width > width {
                x = 0
                y += rowHeight + spacing
                rowHeight = 0
            }
            place(view, CGPoint(x: x, y: y), size)
            usedWidth = max(usedWidth, x + size.width)
            x += size.width + spacing
            rowHeight = max(rowHeight, size.height)
        }
        return CGSize(width: usedWidth, height: y + rowHeight)
    }
}
