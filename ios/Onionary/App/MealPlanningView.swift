import SwiftUI
import OnionaryCore

struct MealPlan: Decodable {
    struct Item: Decodable, Identifiable {
        let id: Int
        let recipeId: Int
        let isCooked: Bool
        let recipe: Recipe
    }
    let items: [Item]
}
struct ShoppingList: Decodable {
    struct Item: Decodable {
        let name: String
        let totalQuantity: Decimal?
        let unit: String?
    }
    let items: [Item]
}

struct MealPlanningView: View {
    @Bindable var store: AppStore
    var cook: () -> Void
    @State private var items: [MealPlan.Item] = []
    @State private var shopping: [ShoppingList.Item] = []
    @State private var picked: Set<Int> = []
    @State private var checked: Set<Int> = []
    @State private var adding = false
    @State private var clearing = false
    @State private var busy = false
    @State private var showShopping = false
    @State private var error: String?
    var body: some View {
        List {
            if let error { Text(error).foregroundStyle(.red) }
            if items.isEmpty { ContentUnavailableView("Plan your meals", systemImage: "calendar", description: Text("Add recipes to your kitchen plan.")) }
            ForEach(items) { item in
                HStack {
                    Button { run { try await request("meal-plan/\(item.recipeId)/cooked", method: item.isCooked ? "DELETE" : "POST"); try await load() } } label: {
                        Image(systemName: item.isCooked ? "checkmark.circle.fill" : "circle").frame(minWidth: 44, minHeight: 44)
                    }.buttonStyle(.borderless).accessibilityLabel(item.isCooked ? "Mark uncooked" : "Mark cooked")
                    Button { store.visit(item.recipe); cook() } label: {
                        Text(item.recipe.name).foregroundStyle(.primary).strikethrough(item.isCooked)
                    }.buttonStyle(.plain)
                }.swipeActions {
                    Button("Remove", role: .destructive) { run { try await request("meal-plan/\(item.recipeId)", method: "DELETE"); try await load() } }
                }
            }
        }.disabled(busy).navigationTitle("Kitchen")
            .refreshable { await reload() }.task { await reload() }
            .toolbar {
                Button("Add meals", systemImage: "plus") { picked = []; adding = true }
                Menu {
                    Button("Shopping list") { run {
                        guard let credential = store.credential else { return }
                        let data = try await OnionaryAPI(server: credential.server, token: credential.token).data("shopping-list", method: "POST", body: JSONEncoder().encode(items.filter { !$0.isCooked }.map(\.recipeId)))
                        shopping = try OnionaryAPI.decoder.decode(ShoppingList.self, from: data).items
                        checked = []; showShopping = true
                    } }
                    Button("Clear plan", role: .destructive) { clearing = true }
                } label: { Image(systemName: "ellipsis.circle") }.disabled(items.isEmpty)
            }
            .confirmationDialog("Clear the household meal plan?", isPresented: $clearing, titleVisibility: .visible) {
                Button("Clear plan", role: .destructive) { run { try await request("meal-plan", method: "DELETE"); try await load() } }
            }
            .sheet(isPresented: $adding) {
                NavigationStack {
                    List(store.kitchen.recipes) { recipe in
                        Button { if !picked.insert(recipe.id).inserted { picked.remove(recipe.id) } } label: {
                            Label(recipe.name, systemImage: picked.contains(recipe.id) ? "checkmark.circle.fill" : "circle")
                        }
                    }.navigationTitle("Add meals").task { await store.refresh() }.toolbar {
                        Button("Cancel") { adding = false }
                        Button("Add") { adding = false; run {
                            try await request("meal-plan/add", method: "POST", body: JSONEncoder().encode(["recipe_ids": Array(picked)])); try await load()
                        } }.disabled(picked.isEmpty)
                    }
                }
            }
            .sheet(isPresented: $showShopping) {
                NavigationStack {
                    List(shopping.indices, id: \.self) { index in
                        let item = shopping[index]
                        Button { if !checked.insert(index).inserted { checked.remove(index) } } label: {
                            HStack {
                                Image(systemName: checked.contains(index) ? "checkmark.circle.fill" : "circle")
                                Text(item.name).strikethrough(checked.contains(index))
                                Spacer()
                                Text([item.totalQuantity.map { Numbers.display($0, locale: L10n.locale) } ?? "", item.unit ?? ""].filter { !$0.isEmpty }.joined(separator: " "))
                            }
                        }
                    }.navigationTitle("Shopping list").toolbar { Button("Done") { showShopping = false } }
                }
            }
    }
    private func request(_ path: String, method: String, body: Data? = nil) async throws {
        guard let credential = store.credential else { throw CookingError.response("Sign in to your kitchen.") }
        _ = try await OnionaryAPI(server: credential.server, token: credential.token).data(path, method: method, body: body)
    }
    private func load() async throws {
        guard let credential = store.credential else { return }
        let data = try await OnionaryAPI(server: credential.server, token: credential.token).data("meal-plan")
        items = try OnionaryAPI.decoder.decode(MealPlan.self, from: data).items
    }
    private func reload() async { do { try await load(); error = nil } catch { self.error = error.localizedDescription } }
    private func run(_ action: @escaping @MainActor () async throws -> Void) {
        busy = true
        Task { defer { busy = false }; do { try await action(); error = nil } catch { self.error = error.localizedDescription } }
    }
}
