import SwiftUI
import OnionaryCore

struct RecipeShareLink: Decodable, Identifiable {
    let id: String
    let url: URL
    let expiresAt: String
}
struct RecipeSharingView: View {
    @Bindable var store: AppStore
    let recipe: Recipe
    @State private var hours = 24
    @State private var link: RecipeShareLink?
    @State private var error: String?
    @State private var busy = false
    @Environment(\.dismiss) private var dismiss
    var body: some View {
        NavigationStack {
            Form {
                Text(recipe.name).font(.headline)
                Text("Anyone with the temporary link can read this recipe snapshot. Imports are independent copies.")
                if let link {
                    ShareLink(item: link.url) { Label("Share recipe copy", systemImage: "square.and.arrow.up") }
                    Text(link.url.absoluteString).font(.caption).textSelection(.enabled)
                    Button("Revoke link", role: .destructive) { Task {
                        do { try await store.revokeRecipeLink(link.id); dismiss() }
                        catch { self.error = error.localizedDescription }
                    } }
                } else {
                    Stepper("Expires in \(hours) hours", value: $hours, in: 1...168)
                    Button("Create link") { Task {
                        busy = true; defer { busy = false }
                        do { link = try await store.shareRecipe(recipe.id, hours: hours) }
                        catch { self.error = error.localizedDescription }
                    } }.disabled(busy)
                }
                if let error { Text(error).foregroundStyle(.red) }
            }.navigationTitle("Share recipe copy").toolbar { Button("Done") { dismiss() } }
        }
    }
}

struct SharedRecipeLinksView: View {
    @Bindable var store: AppStore
    struct Entry: Decodable, Identifiable { let id: String; let name: String; let expiresAt: String; let revoked: Bool }
    @State private var entries: [Entry] = []
    @State private var error: String?
    var body: some View {
        List {
            if let error { Text(error).foregroundStyle(.red) }
            ForEach(entries) { entry in
                VStack(alignment: .leading) {
                    Text(entry.name)
                    Text(entry.expiresAt).font(.caption).foregroundStyle(.secondary)
                    Button(LocalizedStringKey(entry.revoked ? "Revoked" : "Revoke link"), role: .destructive) { Task {
                        do { try await store.revokeRecipeLink(entry.id); await load() }
                        catch { self.error = error.localizedDescription }
                    } }.disabled(entry.revoked)
                }
            }
        }.navigationTitle("Shared recipe links").task { await load() }.refreshable { await load() }
    }
    private func load() async {
        guard let credential = store.credential else { return }
        do { entries = try OnionaryAPI.decoder.decode([Entry].self, from: await OnionaryAPI(server: credential.server, token: credential.token).data("recipe-shares")) }
        catch { self.error = error.localizedDescription }
    }
}
