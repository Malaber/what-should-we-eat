import SwiftUI
import UIKit

private extension UIView {
    var focusedTextEditor: UIView? {
        if isFirstResponder && (self is UITextField || self is UITextView) { return self }
        for child in subviews {
            if let editor = child.focusedTextEditor { return editor }
        }
        return nil
    }
}

/// Each window owns its recognizer and handler for its full lifetime. SwiftUI
/// may replace the zero-size attachment view when a sheet or tab changes.
@MainActor
private final class OutsideFieldTap: UITapGestureRecognizer, UIGestureRecognizerDelegate {
    init() {
        super.init(target: nil, action: nil)
        addTarget(self, action: #selector(dismissKeyboard))
        cancelsTouchesInView = false
        delaysTouchesBegan = false
        delaysTouchesEnded = false
        delegate = self
    }

    @objc private func dismissKeyboard() {
        // Complete the original touch before keyboard-driven sheet relayout.
        // Otherwise a form button can move between touch-down and touch-up.
        DispatchQueue.main.async { [weak self] in self?.view?.endEditing(true) }
    }

    func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer, shouldReceive touch: UITouch) -> Bool {
        // Do not compete with cooking controls when there is nothing to dismiss.
        guard let window = view, window.focusedTextEditor != nil else { return false }
        var candidate = touch.view
        while let current = candidate {
            if current is UIControl || current is UITextView || current is UIToolbar || current.accessibilityTraits.contains(.button) { return false }
            candidate = current.superview
        }
        return true
    }

    func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer,
                           shouldRecognizeSimultaneouslyWith other: UIGestureRecognizer) -> Bool { true }
}

/// The editor uses nested scroll views for Duo. A scroll proxy outside a pane
/// can't find the focused text view inside it, so use its actual scroll ancestors.
struct KeyboardFocusScroll: UIViewRepresentable {
    let focus: String?

    final class AttachmentView: UIView {
        var focus: String? {
            didSet { if focus != oldValue { scheduleReveal() } }
        }
        private var keyboardFrame: CGRect?

        init() {
            super.init(frame: .zero)
            NotificationCenter.default.addObserver(self, selector: #selector(keyboardChanged(_:)),
                name: UIResponder.keyboardDidChangeFrameNotification, object: nil)
        }

        required init?(coder: NSCoder) { nil }

        @objc private func keyboardChanged(_ notification: Notification) {
            keyboardFrame = (notification.userInfo?[UIResponder.keyboardFrameEndUserInfoKey] as? NSValue)?.cgRectValue
            scheduleReveal()
        }

        private func scheduleReveal() {
            DispatchQueue.main.async { [weak self] in self?.revealEditor() }
        }

        private func revealEditor() {
            guard focus != nil, let window, let editor = window.focusedTextEditor else { return }
            let keyboard = keyboardFrame.map { window.convert($0, from: nil) }
            var candidate = editor.superview
            while let view = candidate {
                if let scroll = view as? UIScrollView, scroll.isScrollEnabled {
                    reveal(editor, in: scroll, window: window, keyboard: keyboard)
                }
                candidate = view.superview
            }
        }

        private func reveal(_ editor: UIView, in scroll: UIScrollView, window: UIWindow, keyboard: CGRect?) {
            let viewport = scroll.convert(scroll.bounds, to: window).intersection(window.bounds)
            let field = editor.convert(editor.bounds, to: window)
            let keyboardTop = keyboard.flatMap { frame in
                field.minX < frame.maxX && field.maxX > frame.minX ? frame.minY : nil
            }
            let bottom = min(viewport.maxY, keyboardTop ?? viewport.maxY) - 12
            let top = viewport.minY + 12
            guard bottom > top else { return }
            guard field.maxY > bottom || field.minY < top else { return }
            let delta = field.midY - (top + bottom) / 2
            let minY = -scroll.adjustedContentInset.top
            let maxY = max(minY, scroll.contentSize.height - scroll.bounds.height + scroll.adjustedContentInset.bottom)
            let target = min(maxY, max(minY, scroll.contentOffset.y + delta))
            if abs(target - scroll.contentOffset.y) > 1 {
                scroll.setContentOffset(CGPoint(x: scroll.contentOffset.x, y: target), animated: false)
            }
        }
    }

    func makeUIView(context: Context) -> AttachmentView { AttachmentView() }
    func updateUIView(_ uiView: AttachmentView, context: Context) { uiView.focus = focus }
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
