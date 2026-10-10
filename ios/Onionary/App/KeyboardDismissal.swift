import SwiftUI
import UIKit

/// Each window owns its recognizer and handler for its full lifetime. SwiftUI
/// may replace the zero-size attachment view when a sheet or tab changes.
@MainActor
private final class OutsideFieldTap: UITapGestureRecognizer, UIGestureRecognizerDelegate {
    init() {
        super.init(target: nil, action: nil)
        addTarget(self, action: #selector(dismissKeyboard))
        cancelsTouchesInView = false
        delegate = self
    }

    @objc private func dismissKeyboard() { view?.endEditing(true) }

    func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer, shouldReceive touch: UITouch) -> Bool {
        var candidate = touch.view
        while let current = candidate {
            if current is UITextField || current is UITextView || current is UIToolbar { return false }
            candidate = current.superview
        }
        return true
    }

    func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer,
                           shouldRecognizeSimultaneouslyWith other: UIGestureRecognizer) -> Bool { true }
}

private struct KeyboardDismissal: UIViewRepresentable {
    final class AttachmentView: UIView {
        override func didMoveToWindow() {
            super.didMoveToWindow()
            guard let window,
                  window.gestureRecognizers?.contains(where: { $0 is OutsideFieldTap }) != true else { return }
            window.addGestureRecognizer(OutsideFieldTap())
        }
    }

    func makeUIView(context: Context) -> AttachmentView { AttachmentView(frame: .zero) }
    func updateUIView(_ uiView: AttachmentView, context: Context) {}
}

extension View {
    func dismissibleKeyboard() -> some View {
        background(KeyboardDismissal().frame(width: 0, height: 0))
            .scrollDismissesKeyboard(.interactively)
            .toolbar {
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    Button("Done") { UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil) }
                }
            }
    }
}
