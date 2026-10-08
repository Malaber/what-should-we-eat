import SwiftUI

@main
struct OnionaryApp: App {
    @State private var store = AppStore()
    var body: some Scene {
        WindowGroup {
            RootView(store: store)
                .tint(Color(red: 0.48, green: 0.19, blue: 0.34))
                .alert("Your kitchen", isPresented: Binding(get: { store.error != nil }, set: { if !$0 { store.error = nil } })) {
                    Button("OK") { store.error = nil }
                } message: { Text(store.error ?? "") }
        }
    }
}
