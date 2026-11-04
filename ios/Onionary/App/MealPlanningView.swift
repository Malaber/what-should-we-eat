import SwiftUI
import OnionaryCore

struct MealPlan: Codable {
    struct Item: Codable, Identifiable {
        let id: Int
        let recipeId: Int
        let isCooked: Bool
        let recipe: Recipe
    }
    let items: [Item]
}
struct ShoppingList: Decodable {
    struct Item: Decodable, Identifiable {
        var id: String { name.lowercased() + "\u{1f}" + (unit ?? "").lowercased() }
        let name: String
        let totalQuantity: Decimal?
        let unit: String?
    }
    let items: [Item]
}

struct MealPlanningView: View {
    @Bindable var store: AppStore
    var cook: () -> Void
    private var items: [MealPlan.Item] { store.mealItems }
    @State private var shopping: [ShoppingList.Item] = []
    @State private var picked: Set<Int> = []
    @State private var checked: Set<String> = []
    @State private var adding = false
    @State private var clearing = false
    @State private var busy = false
    @State private var preferredColumn = NavigationSplitViewColumn.sidebar
    @State private var error: String?
    var body: some View {
        NavigationSplitView(preferredCompactColumn: $preferredColumn) {
            plan.navigationSplitViewColumnWidth(min: 280, ideal: 360, max: 460)
        } detail: {
            shoppingPane
        }.navigationSplitViewStyle(.balanced)
    }
    private var plan: some View {
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
            .refreshable { await reload() }.task(id: store.credential?.token) { await reload() }
            .toolbar {
                Button("Add meals", systemImage: "plus") { picked = []; adding = true }
                Menu {
                    Button("Shopping list") { run {
                        guard store.credential != nil else { return }
                        let data = try await store.request("shopping-list", method: "POST", body: JSONEncoder().encode(items.filter { !$0.isCooked }.map(\.recipeId)))
                        shopping = try OnionaryAPI.decoder.decode(ShoppingList.self, from: data).items
                        checked.formIntersection(Set(shopping.map(\.id)))
                        preferredColumn = .detail
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
    }
    private var shoppingPane: some View {
        List {
            Section {
                Text("Shopping checks and cooking progress are saved locally on this device, not synchronized between devices.").font(.footnote).foregroundStyle(.secondary)
                Button(shopping.isEmpty ? "Generate shopping list" : "Refresh shopping list", systemImage: "arrow.clockwise") {
                    run {
                        let data = try await store.request("shopping-list", method: "POST", body: JSONEncoder().encode(items.filter { !$0.isCooked }.map(\.recipeId)))
                        shopping = try OnionaryAPI.decoder.decode(ShoppingList.self, from: data).items
                        checked.formIntersection(Set(shopping.map(\.id)))
                    }
                }.disabled(busy)
                if let error { Text(error).foregroundStyle(.red) }
            }
            ForEach(shopping) { item in
                Button { if !checked.insert(item.id).inserted { checked.remove(item.id) } } label: {
                    HStack {
                        Image(systemName: checked.contains(item.id) ? "checkmark.circle.fill" : "circle")
                        Text(item.name).strikethrough(checked.contains(item.id))
                        Spacer()
                        Text([item.totalQuantity.map { Numbers.display($0, locale: L10n.locale) } ?? "", item.unit ?? ""].filter { !$0.isEmpty }.joined(separator: " "))
                    }.frame(minHeight: 44)
                }.accessibilityIdentifier("shopping-" + item.name)
                    .accessibilityValue(checked.contains(item.id) ? "Checked" : "Unchecked")
            }
        }.navigationTitle("Shopping list").accessibilityIdentifier("shopping-list")
    }
    private func request(_ path: String, method: String, body: Data? = nil) async throws {
        guard store.credential != nil else { throw CookingError.response("Sign in to your kitchen.") }
        _ = try await store.request(path, method: method, body: body)
    }
    private func load() async throws {
        guard store.credential != nil else { return }
        let account = store.scope
        let data = try await store.request("meal-plan")
        guard account == store.scope else { return }
        store.mealItems = try OnionaryAPI.decoder.decode(MealPlan.self, from: data).items
        store.publishWidget(items, account: account)
    }
    private func reload() async { do { try await load(); error = nil } catch { self.error = error.localizedDescription } }
    private func run(_ action: @escaping @MainActor () async throws -> Void) {
        busy = true
        Task { defer { busy = false }; do { try await action(); error = nil } catch { self.error = error.localizedDescription } }
    }
}
