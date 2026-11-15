import SwiftUI

@main
struct OnionaryApp: App {
    @AppStorage("accent") private var accent = "Onion"
    @AppStorage("appearance") private var appearance = "system"
    @AppStorage("language") private var language = "system"
    @State private var store = AppStore()
    var body: some Scene {
        WindowGroup {
            RootView(store: store)
                .dismissibleKeyboard()
                .tint(OnionaryTheme.color(accent))
                .preferredColorScheme(appearance == "system" ? nil : appearance == "dark" ? .dark : .light)
                .environment(\.locale, language == "system" ? Locale.current : Locale(identifier: language))
                .alert("Your kitchen", isPresented: Binding(get: { store.error != nil }, set: { if !$0 { store.error = nil } })) {
                    Button("OK") { store.error = nil }
                } message: { Text(store.error ?? "") }
        }
    }
}
