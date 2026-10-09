import SwiftUI

struct SettingsView: View {
    @Bindable var store: AppStore
    @AppStorage("appearance") private var appearance = "system"
    @AppStorage("language") private var language = "system"
    @State private var switching = false
    @State private var confirmSwitch = false
    var body: some View {
        Form {
            Section("Backend") {
                LabeledContent("Connected to", value: store.credential?.server.host() ?? "")
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
            Section("Account security") {
                if let server = store.credential?.server {
                    Link("Manage passkeys", destination: server.appending(path: "auth/security"))
                }
                Text("Opens your backend’s secure browser page.").font(.footnote).foregroundStyle(.secondary)
                Button("Sign out", role: .destructive) { Task { await store.disconnect() } }.disabled(store.busy)
            }
            Section("Onionary") {
                Link("Support", destination: URL(string: "https://onionary.malaber.de/support/")!)
                Link("Privacy", destination: URL(string: "https://onionary.malaber.de/privacy/")!)
            }
        }.navigationTitle("Settings")
            .confirmationDialog("Switch backend? Your saved cooking progress will be kept.", isPresented: $confirmSwitch, titleVisibility: .visible) {
                Button("Switch backend") { switching = true }
            }
            .sheet(isPresented: $switching) {
                NavigationStack {
                    ConnectionView(store: store)
                        .toolbar { Button("Cancel") { switching = false } }
                        .onChange(of: store.credential?.server) { switching = false }
                }
            }
    }
}
