import SwiftUI
import OnionaryCore

struct RecipeInboxView: View {
    struct Entry: Identifiable, Decodable, Equatable {
        enum Kind: String, Decodable { case url, text }
        let id: Int
        let kind: Kind
        let content: String
    }

    @Bindable var store: AppStore
    @State private var entries: [Entry] = []
    @State private var reviewing: Entry?
    @State private var removing: Entry?
    @State private var error: String?
    @State private var loading = true
    @State private var copied: Entry?
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            List {
                if let error {
                    Text(error).foregroundStyle(.red)
                    Button("Retry") { Task { await load() } }
                }
                if loading && entries.isEmpty { ProgressView() }
                if entries.isEmpty && !loading && error == nil {
                    ContentUnavailableView("No saved imports", systemImage: "tray",
                        description: Text("Save a recipe link or text on the Onionary website using this account."))
                }
                ForEach(entries) { entry in
                    HStack {
                        Button { reviewing = entry } label: {
                            VStack(alignment: .leading) {
                                Text(entry.content).lineLimit(2)
                                Text(entry.kind == .url ? "Recipe link" : "Recipe text")
                                    .font(.caption).foregroundStyle(.secondary)
                            }.frame(maxWidth: .infinity, alignment: .leading).contentShape(Rectangle())
                        }.accessibilityIdentifier("review-saved-import-\(entry.id)")
                        Button {
                            UIPasteboard.general.string = entry.content
                            copied = entry
                        } label: {
                            Label(entry.kind == .url ? "Copy link" : "Copy text",
                                  systemImage: copied == entry ? "checkmark" : "doc.on.doc")
                                .labelStyle(.iconOnly).frame(minWidth: 44, minHeight: 44)
                        }.accessibilityValue(copied == entry ? Text("Copied") : Text(""))
                          .accessibilityIdentifier("copy-saved-import-\(entry.id)")
                        Button(role: .destructive) { removing = entry } label: {
                            Label("Remove saved import", systemImage: "trash")
                                .labelStyle(.iconOnly).frame(minWidth: 44, minHeight: 44)
                        }.accessibilityIdentifier("remove-saved-import-\(entry.id)")
                    }.buttonStyle(.borderless)
                }
            }.accessibilityIdentifier("saved-imports").navigationTitle("Saved imports")
                .toolbar { Button("Done") { dismiss() } }
                .refreshable { await load() }
                .sheet(item: $reviewing) { entry in
                    ImportRecipeView(store: store, link: entry.kind == .url ? entry.content : "",
                                     text: entry.kind == .text ? entry.content : nil)
                }
                .confirmationDialog("Remove saved import?", isPresented: Binding(
                    get: { removing != nil }, set: { if !$0 { removing = nil } })) {
                    Button("Remove saved import", role: .destructive) {
                        guard let removing else { return }
                        Task { await remove(removing) }
                    }
                }
        }.connectionRecovery(store)
            .task(id: store.scope) {
                entries = []
                reviewing = nil
                removing = nil
                copied = nil
                await load()
            }
    }

    private func load() async {
        let scope = store.scope
        error = nil
        loading = true
        defer { if store.scope == scope { loading = false } }
        do {
            let data = try await store.request("recipe-inbox")
            guard !Task.isCancelled, store.scope == scope else { return }
            entries = try OnionaryAPI.decoder.decode([Entry].self, from: data)
        } catch {
            if !Task.isCancelled, store.scope == scope { self.error = L10n.text(error.localizedDescription) }
        }
    }

    private func remove(_ entry: Entry) async {
        do {
            _ = try await store.request("recipe-inbox/\(entry.id)", method: "DELETE")
            entries.removeAll { $0.id == entry.id }
        } catch { self.error = L10n.text(error.localizedDescription) }
    }
}
