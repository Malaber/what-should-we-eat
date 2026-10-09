import SwiftUI
import UIKit

/// A non-cancelling recognizer dismisses only taps outside editable controls.
private struct KeyboardDismissal: UIViewRepresentable {
    func makeUIView(context: Context) -> UIView {
        let view = UIView(frame: .zero)
        DispatchQueue.main.async {
            guard let window = view.window else { return }
            if window.gestureRecognizers?.contains(where: { $0 is OutsideFieldTap }) == true { return }
            let tap = OutsideFieldTap(target: context.coordinator, action: #selector(Coordinator.dismissKeyboard))
            tap.cancelsTouchesInView = false
            tap.delegate = context.coordinator
            window.addGestureRecognizer(tap)
        }
        return view
    }
    func updateUIView(_ uiView: UIView, context: Context) {}
    func makeCoordinator() -> Coordinator { Coordinator() }
    private final class OutsideFieldTap: UITapGestureRecognizer {}
    final class Coordinator: NSObject, UIGestureRecognizerDelegate {
        @objc func dismissKeyboard(_ sender: UITapGestureRecognizer) { sender.view?.endEditing(true) }
        func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer, shouldReceive touch: UITouch) -> Bool {
            var view = touch.view
            while let current = view {
                if current is UITextField || current is UITextView { return false }
                view = current.superview
            }
            return true
        }
        func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer, shouldRecognizeSimultaneouslyWith other: UIGestureRecognizer) -> Bool { true }
    }
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
