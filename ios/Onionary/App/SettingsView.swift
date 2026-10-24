import SwiftUI
import OnionaryCore

struct SettingsView: View {
    @Bindable var store: AppStore
    @AppStorage("appearance") private var appearance = "system"
    @AppStorage("language") private var language = "system"
    @State private var deleting = false
    @State private var switching = false
    @State private var confirmSwitch = false
    var body: some View {
        Form {
            Section("Backend") {
                LabeledContent("Connected to", value: store.credential?.server.host() ?? "")
                if let name = store.credential?.name { LabeledContent("Account", value: name) }
                if let email = store.credential?.email { LabeledContent("Email", value: email) }
                Button("Switch backend") { confirmSwitch = true }.disabled(store.busy)
                Text("One backend is active. Saved cooking progress stays separate for each account.").font(.footnote).foregroundStyle(.secondary)
            }
            Section("Appearance and language") {
                Picker("Appearance", selection: $appearance) {
                    Text("System").tag("system"); Text("Light").tag("light"); Text("Dark").tag("dark")
                }.accessibilityIdentifier("appearance-picker")
                Picker("Language", selection: $language) {
                    Text("System").tag("system"); Text("English").tag("en"); Text("Deutsch").tag("de")
                }.accessibilityIdentifier("language-picker")
            }
            Section("Session") {
                Text("Access lasts 14 days, with 28 further days for automatic renewal. Then sign in with a passkey.")
                    .font(.footnote).foregroundStyle(.secondary)
                if store.credential?.refreshToken == nil {
                    Text("Sign in once to enable automatic renewal.").font(.footnote).foregroundStyle(.secondary)
                }
                if let expires = store.credential?.accessExpiresAt {
                    LabeledContent("Access valid until") { Text(Date(timeIntervalSince1970: expires), format: .dateTime.day().month().year().hour().minute()) }
                }
                if let expires = store.credential?.sessionExpiresAt {
                    LabeledContent("Passkey required by") { Text(Date(timeIntervalSince1970: expires), format: .dateTime.day().month().year().hour().minute()) }
                }
                Button("Refresh sign-in with passkey") { Task { await store.reauthenticate() } }.disabled(store.busy)
                if let error = store.reauthenticationError { Text(error).foregroundStyle(.red) }
            }
            Section("Account security") {
                if let server = store.credential?.server {
                    Link("Manage passkeys", destination: server.appending(path: "auth/security"))
                }
                Text("Opens your backend’s secure browser page.").font(.footnote).foregroundStyle(.secondary)
                Button("Sign out", role: .destructive) { Task { await store.disconnect() } }.disabled(store.busy)
            }
            Section("Danger zone") {
                Button("Permanently delete account", role: .destructive) { deleting = true }
                    .disabled(store.busy).accessibilityIdentifier("delete-account")
            }
            Section("Onionary") {
                NavigationLink("Shared recipe links") { SharedRecipeLinksView(store: store) }
                Link("Support", destination: URL(string: "https://app.onionary.malaber.de/support/")!)
                Link("Privacy", destination: URL(string: "https://app.onionary.malaber.de/privacy/")!)
            }
        }.dismissibleKeyboard().navigationTitle("Settings")
            .confirmationDialog("Switch backend? Your saved cooking progress will be kept.", isPresented: $confirmSwitch, titleVisibility: .visible) {
                Button("Switch backend") { switching = true }
            }
            .sheet(isPresented: $deleting) { DeleteAccountView(store: store) }
            .sheet(isPresented: $switching) {
                NavigationStack {
                    ConnectionView(store: store)
                        .toolbar { Button("Cancel") { switching = false } }
                        .onChange(of: store.credential?.server) { switching = false }
                }
            }
    }
}


struct DeleteAccountView: View {
    @Bindable var store: AppStore
    @Environment(\.dismiss) private var dismiss
    @State private var email = ""
    @State private var error: String?
    @State private var submitting = false
    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Text("Deleting your account permanently removes passkeys, sessions and kitchens without other members, including recipes and shared links. Shared kitchens remain for their other members. This cannot be undone.")
                    if let expected = store.credential?.email { Text(expected).textSelection(.enabled) }
                    TextField("Type your account email to confirm", text: $email)
                        .keyboardType(.emailAddress).textInputAutocapitalization(.never).autocorrectionDisabled()
                        .accessibilityIdentifier("delete-account-email")
                    if let error { Text(error).foregroundStyle(.red).accessibilityIdentifier("delete-account-error") }
                    Button("Permanently delete account", role: .destructive) {
                        submitting = true; error = nil
                        Task {
                            do { try await store.deleteAccount(email: email); dismiss() }
                            catch { self.error = error.localizedDescription }
                            submitting = false
                        }
                    }.disabled(submitting || email.trimmingCharacters(in: .whitespacesAndNewlines).lowercased() != store.credential?.email?.lowercased())
                        .accessibilityIdentifier("confirm-delete-account")
                    if submitting { ProgressView() }
                }
            }.navigationTitle("Delete account").dismissibleKeyboard()
                .toolbar { Button("Cancel") { dismiss() }.disabled(submitting) }
                .interactiveDismissDisabled(submitting)
        }
    }
}
