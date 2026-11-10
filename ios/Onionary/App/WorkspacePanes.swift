import SwiftUI
import OnionaryCore

/// Two persistent subtrees: changing the layout never recreates their state.
struct WorkspacePanes<Primary: View, Secondary: View>: View {
    var focus: String? = nil
    @ViewBuilder let primary: () -> Primary
    @ViewBuilder let secondary: () -> Secondary
    @Environment(\.dynamicTypeSize) private var typeSize
    var body: some View {
        GeometryReader { geometry in
            let division = activeDivision(in: geometry)
            let horizontal = division.map { $0.height > $0.width } ?? (geometry.size.width >= 760 && !typeSize.isAccessibilitySize)
            let split = horizontal || division != nil
            let gap = division.map { horizontal ? $0.width : $0.height } ?? 16
            let firstExtent = division.map { horizontal ? $0.minX : $0.minY }
            let secondExtent = division.map { horizontal ? geometry.size.width - $0.maxX : geometry.size.height - $0.maxY }
            let layout = horizontal ? AnyLayout(HStackLayout(alignment: .top, spacing: max(16, gap))) : AnyLayout(VStackLayout(spacing: max(16, gap)))
            ScrollViewReader { outer in
                ScrollView {
                    layout {
                        pane(split: split, height: horizontal ? geometry.size.height : firstExtent) { primary() }
                            .frame(width: horizontal ? firstExtent : nil)
                        pane(split: split, height: horizontal ? geometry.size.height : secondExtent) { secondary() }
                            .frame(width: horizontal ? secondExtent : nil)
                    }
                }.scrollDisabled(split)
                    .onChange(of: split) { _, _ in if let focus { outer.scrollTo(focus, anchor: .center) } }
            }
        }
    }
    private func pane<Content: View>(split: Bool, height: CGFloat?, @ViewBuilder content: @escaping () -> Content) -> some View {
        ScrollViewReader { proxy in
            ScrollView {
                VStack(alignment: .leading, spacing: 16) { content() }
                    .padding(16).frame(maxWidth: 760, alignment: .leading).frame(maxWidth: .infinity)
            // Override the disabled outer scroller for each split pane. Calling
            // scrollDisabled(false) cannot undo an ancestor's disabled value.
            }.environment(\.isScrollEnabled, split)
                .fixedSize(horizontal: false, vertical: !split)
                .frame(height: split ? max(120, height ?? 300) : nil)
                .onChange(of: split) { _, _ in if let focus { proxy.scrollTo(focus, anchor: .center) } }
        }
    }
    private func activeDivision(in geometry: GeometryProxy) -> CGRect? {
        if #available(iOS 27.1, *) {
            return geometry.reservedRegions(kind: .division).first(where: { $0.isActive }).flatMap { region in
                let frame = region.frame
                return WorkspaceDivision.visible(CGRect(x: frame.minX - region.margins.leading,
                              y: frame.minY - region.margins.top,
                              width: frame.width + region.margins.leading + region.margins.trailing,
                              height: frame.height + region.margins.top + region.margins.bottom), in: geometry.size)
            }
        }
        return nil
    }
}
