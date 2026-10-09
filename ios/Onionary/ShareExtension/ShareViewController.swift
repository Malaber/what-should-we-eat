import UIKit
import UniformTypeIdentifiers
import OnionaryCore

/// A URL-only inbox: credentials never leave the main app's Keychain.
@MainActor final class ShareViewController: UIViewController {
    private let message = UILabel()
    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        message.numberOfLines = 0; message.textAlignment = .center
        message.text = "Preparing recipe…"
        let close = UIButton(type: .system)
        close.setTitle("Done", for: .normal); close.addTarget(self, action: #selector(done), for: .touchUpInside)
        let stack = UIStackView(arrangedSubviews: [message, close]); stack.axis = .vertical; stack.spacing = 20
        stack.translatesAutoresizingMaskIntoConstraints = false; view.addSubview(stack)
        NSLayoutConstraint.activate([stack.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 24), stack.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -24), stack.centerYAnchor.constraint(equalTo: view.centerYAnchor)])
        let providers = (extensionContext?.inputItems as? [NSExtensionItem] ?? []).flatMap { $0.attachments ?? [] }
        guard let provider = providers.first(where: { $0.hasItemConformingToTypeIdentifier(UTType.url.identifier) }) else {
            message.text = "Share a Chefkoch or Onionary recipe link from your browser."; return
        }
        provider.loadItem(forTypeIdentifier: UTType.url.identifier, options: nil) { [weak self] item, _ in
            let text = (item as? URL)?.absoluteString ?? item as? String
            Task { @MainActor [weak self] in
                do {
                    guard let text else { throw CookingError.response("No recipe link found.") }
                    let url = try RecipeImportLink.accepted(text)
                    guard let inbox = UserDefaults(suiteName: "group.de.malaber.onionary") else { throw CookingError.response("Could not open Onionary inbox.") }
                    inbox.set(url.absoluteString, forKey: "pendingRecipeURL")
                    self?.message.text = "Recipe link saved. Open Onionary to review and import it."
                } catch { self?.message.text = error.localizedDescription }
            }
        }
    }
    @objc private func done() { extensionContext?.completeRequest(returningItems: nil) }
}
