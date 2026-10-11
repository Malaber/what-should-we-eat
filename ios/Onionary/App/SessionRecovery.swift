import SwiftUI
import OnionaryCore

private struct SessionRecovery: ViewModifier {
    @Bindable var store: AppStore
    func body(content: Content) -> some View {
        content.safeAreaInset(edge: .top, spacing: 0) {
            if store.needsReauthentication {
                VStack(alignment: .leading, spacing: 8) {
                    Label("Sign in again to sync. Your progress and draft are safe.", systemImage: "key.fill")
                        .font(.subheadline)
                    if let email = store.credential?.email {
                        Text(AccountIdentity.maskedEmail(email)).font(.caption).foregroundStyle(.secondary)
                    }
                    if let error = store.reauthenticationError { Text(error).font(.caption).foregroundStyle(.red) }
                    HStack {
                        Button("Sign in with passkey") { Task { await store.reauthenticate() } }
                            .buttonStyle(.borderedProminent).disabled(store.busy)
                        if store.busy { ProgressView() }
                    }
                }.padding().frame(maxWidth: .infinity, alignment: .leading)
                    .background(.regularMaterial).accessibilityIdentifier("session-recovery")
            }
        }
    }
}
extension View {
    func connectionRecovery(_ store: AppStore) -> some View { modifier(SessionRecovery(store: store)) }
}
