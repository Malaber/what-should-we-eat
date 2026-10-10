import SwiftUI
import OnionaryCore

private let onion = OnionaryTheme.accent

struct RootView: View {
    @Bindable var store: AppStore
    @State private var tab = 0
    @Environment(\.locale) private var locale
    @Environment(\.scenePhase) private var scenePhase
    var body: some View {
        Group {
            if store.credential == nil {
                NavigationStack { ConnectionView(store: store) }
            } else {
                TabView(selection: $tab) {
                    NavigationStack { CookingView(store: store, browse: { tab = 1 }) }
                        .tabItem { Label("Cooking", systemImage: "flame") }.tag(0)
                    NavigationStack { RecipesView(store: store, selected: { tab = 0 }) }
                        .tabItem { Label("Recipes", systemImage: "book.closed") }.tag(1)
                    NavigationStack { MealPlanningView(store: store, cook: { tab = 0 }) }
                        .tabItem { Label("Kitchen", systemImage: "calendar") }.tag(3)
                    NavigationStack { SettingsView(store: store) }.tabItem { Label("Settings", systemImage: "gearshape") }.tag(2)
                }.id(locale.identifier + (store.credential?.server.absoluteString ?? "") + (store.credential?.userID ?? ""))
            }
        }.onChange(of: scenePhase) { _, phase in if phase == .active { store.checkImportInbox(); store.synchronizeCookingActivity(); Task { await store.refreshWidget() } } }
         .onChange(of: store.credential?.userID) { store.checkImportInbox() }
         .task { store.checkImportInbox(); store.synchronizeCookingActivity(); await store.refreshWidget() }
         .onOpenURL { store.openWidgetURL($0) }
         .onChange(of: store.widgetNavigation) { _, route in
             guard let route else { return }; tab = route == .kitchen ? 3 : 0; store.widgetNavigation = nil
         }
         .sheet(item: $store.sharingRecipe) { recipe in RecipeSharingView(store: store, recipe: recipe) }
         .sheet(item: $store.editingRecipe) { recipe in EditRecipeView(store: store, id: recipe.id) }
         .sheet(isPresented: Binding(get: { store.pendingImport != nil }, set: { if !$0 { store.pendingImport = nil } })) {
             ImportRecipeView(store: store, link: store.pendingImport ?? "")
         }
    }
}

struct ConnectionView: View {
    @Bindable var store: AppStore
    var body: some View {
        VStack(alignment: .leading, spacing: 24) {
            Text("🧅").font(.system(size: 56)).accessibilityHidden(true)
            Text("YOUR COOKING COMPANION").font(.caption2.bold()).tracking(3).foregroundStyle(onion)
            Text("Welcome to Onionary.").font(.system(.largeTitle, design: .serif, weight: .semibold))
            Text("Your recipes. Your kitchen. Pick up where you left off.").foregroundStyle(.secondary)
            VStack(alignment: .leading, spacing: 8) {
                Text("Backend address").font(.caption.bold())
                TextField("https://onionary-test.malaber.de", text: $store.backend)
                    .textInputAutocapitalization(.never).autocorrectionDisabled().keyboardType(.URL)
                    .textFieldStyle(.roundedBorder).accessibilityIdentifier("backend")
                Text("Choose your own Onionary server. Your passkey is verified on that server in a secure browser window.")
                    .font(.caption).foregroundStyle(.secondary)
            }
            Button { Task { await store.connect() } } label: {
                HStack { if store.busy { ProgressView() }; Label("Sign in with a passkey", systemImage: "person.badge.key.fill") }
                    .frame(maxWidth: .infinity).padding(.vertical, 8)
            }.buttonStyle(.borderedProminent).disabled(store.busy)
            Text("Use Face ID, Touch ID, a security key, or your password manager.").font(.footnote).foregroundStyle(.secondary)
        }.padding(24).frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            .background(OnionaryTheme.background).navigationTitle("Onionary")
    }
}

struct RecipesView: View {
    @Bindable var store: AppStore
    var selected: () -> Void
    @State private var search = ""
    @State private var intelligence = false
    @State private var category: String?
    @State private var quickestFirst = false
    var filtered: [Recipe] { RecipeBrowsing.recipes(store.kitchen.recipes, query: search, category: category, quickestFirst: quickestFirst) }
    var body: some View {
        List {
            if let category {
                Section {
                    HStack {
                        Label(category, systemImage: "tag.fill").font(.headline)
                        Spacer()
                        Button("All recipes") { self.category = nil }
                    }
                }
            } else {
                let categories = RecipeBrowsing.categories(store.kitchen.recipes, query: search)
                if !categories.isEmpty {
                    Section("Browse by tag") {
                        ScrollView(.horizontal) {
                            HStack(spacing: 10) {
                                ForEach(categories, id: \.self) { tag in
                                    Button { category = tag } label: {
                                        VStack(alignment: .leading, spacing: 4) {
                                            Label(tag, systemImage: "tag.fill").font(.headline).lineLimit(1)
                                            Text("\(RecipeBrowsing.recipes(store.kitchen.recipes, category: tag).count) recipes")
                                                .font(.caption).foregroundStyle(.secondary)
                                        }.padding(.horizontal, 12).padding(.vertical, 8)
                                            .frame(minWidth: 140, alignment: .leading)
                                            .background(OnionaryTheme.accent.opacity(0.12), in: RoundedRectangle(cornerRadius: 16))
                                    }.buttonStyle(.plain).accessibilityIdentifier("category-" + tag)
                                }
                            }
                        }.scrollIndicators(.hidden)
                            .contentMargins(.horizontal, 16, for: .scrollContent)
                            .listRowInsets(EdgeInsets(top: 0, leading: 0, bottom: 0, trailing: 0))
                            .listRowBackground(Color.clear)
                            .listRowSeparator(.hidden)
                    }.compactTagSection()
                }
            }
            if search.isEmpty && category == nil && !store.kitchen.recent.isEmpty {
                Section("Recently visited") {
                    ForEach(store.kitchen.recent.prefix(8)) { adventure in
                        recipeRow(adventure.recipe, subtitle: L10n.format("Continue · %lld checked", adventure.checked.count))
                    }
                }
            }
            Section {
                ForEach(filtered) { recipe in recipeRow(recipe, subtitle: recipe.totalTimeMin.map { "\($0) min" } ?? "Ready when you are") }
            } header: {
                HStack {
                    Text("Your recipes")
                    Spacer()
                    Menu {
                        Toggle("Quickest first", isOn: $quickestFirst)
                    } label: { Label("Sort recipes", systemImage: "arrow.up.arrow.down").labelStyle(.iconOnly) }
                    .accessibilityIdentifier("sort-recipes")
                }
            }
            if filtered.isEmpty {
                ContentUnavailableView(LocalizedStringKey(search.isEmpty ? "Your recipe book is waiting" : "No matching recipes"),
                    systemImage: "book.closed", description: Text(LocalizedStringKey(search.isEmpty ? "Add recipes in your web kitchen, then refresh here." : "Try another search.")))
            }
        }.dismissibleKeyboard().navigationTitle("Recipe book").searchable(text: $search, prompt: "Find something delicious")
            .sheet(isPresented: $intelligence) { IntelligenceRecipeView(store: store) }
            .refreshable { await store.refresh() }
            .toolbar {
                Menu {
                    Button("Create with Intelligence", systemImage: "sparkles") { intelligence = true }
                    Button("Import recipe", systemImage: "square.and.arrow.down") { store.pendingImport = "" }
                } label: { Label("Add recipe", systemImage: "plus") }
                .accessibilityIdentifier("add-recipe")
            }
            .task {
                if store.kitchen.recipes.isEmpty && !ProcessInfo.processInfo.arguments.contains("--ui-testing") { await store.refresh() }
            }
    }
    func recipeRow(_ recipe: Recipe, subtitle: String) -> some View {
        Button { store.visit(recipe); selected() } label: {
            HStack(spacing: 10) {
                Image(systemName: "leaf").font(.title2).foregroundStyle(onion).frame(width: 28, height: 36)
                VStack(alignment: .leading, spacing: 5) {
                    Text(recipe.name).font(.headline).foregroundStyle(.primary)
                    Text(LocalizedStringKey(subtitle)).font(.caption).foregroundStyle(.secondary)
                    if let tags = recipe.tags, !tags.isEmpty {
                        Text(tags.map(\.name).joined(separator: " · "))
                            .font(.caption).foregroundStyle(onion).fixedSize(horizontal: false, vertical: true)
                    }
                }
                Spacer(); Image(systemName: "chevron.right").font(.caption).foregroundStyle(.tertiary)
            }.frame(minHeight: 44)
        }.accessibilityIdentifier("recipe-\(recipe.id)")
         .swipeActions(edge: .leading) { Button("Edit", systemImage: "pencil") { store.editingRecipe = recipe }.tint(onion)
             Button("Share", systemImage: "square.and.arrow.up") { store.sharingRecipe = recipe }
         }
    }
}

struct CookingView: View {
    @Bindable var store: AppStore
    var browse: () -> Void
    private enum Sheet: Identifiable {
        case portions, history, tag(String)
        var id: String {
            switch self {
            case .portions: "portions"
            case .history: "history"
            case .tag(let name): "tag:" + name
            }
        }
    }
    @State private var sheet: Sheet?
    @State private var restart = false
    @State private var recentAction: CheckChange?
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    var body: some View {
        Group {
            if let adventure = store.current {
                List {
                    Section {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("TODAY’S COOKING ADVENTURE").font(.caption2.bold()).tracking(2).foregroundStyle(onion)
                            Text(adventure.recipe.name).font(.system(.title2, design: .serif, weight: .semibold))
                            HStack {
                                Label("\(Numbers.display(adventure.multiplier, locale: L10n.locale))× recipe", systemImage: "scalemass")
                                if let minutes = adventure.recipe.totalTimeMin { Label("\(minutes) min", systemImage: "clock") }
                            }.font(.subheadline).foregroundStyle(.secondary)
                            HStack(spacing: 16) {
                                Button {
                                    store.update { try $0.scale(baseServings: $0.baseServings, portions: $0.portions - 1) }
                                } label: { Image(systemName: "minus").frame(width: 32, height: 32) }
                                    .buttonStyle(.bordered).disabled(adventure.portions <= 1)
                                    .accessibilityLabel("One fewer portion").accessibilityIdentifier("portion-minus")
                                Button { sheet = .portions } label: {
                                    VStack(spacing: 3) {
                                        Text(Numbers.display(adventure.portions, locale: L10n.locale)).font(.title2.bold()).monospacedDigit().lineLimit(1).minimumScaleFactor(0.5)
                                        Text("portions · tap to edit").font(.caption2)
                                    }.frame(maxWidth: .infinity)
                                }.buttonStyle(.plain).accessibilityLabel("\(Numbers.display(adventure.portions, locale: L10n.locale)) portions. Edit amount")
                                Button {
                                    store.update { try $0.scale(baseServings: $0.baseServings, portions: $0.portions + 1) }
                                } label: { Image(systemName: "plus").frame(width: 32, height: 32) }
                                    .buttonStyle(.bordered).accessibilityLabel("One more portion").accessibilityIdentifier("portion-plus")
                            }
                            ProgressView(value: Double(adventure.checked.count), total: Double(max(1, adventure.recipe.ingredients.count + adventure.recipe.instructionSteps.count)))
                                .accessibilityLabel("Cooking progress")
                            Text("\(adventure.checked.count) of \(adventure.recipe.ingredients.count + adventure.recipe.instructionSteps.count) checked")
                                .font(.caption).foregroundStyle(.secondary)
                            Button("Adjust portions", systemImage: "slider.horizontal.3") { sheet = .portions }.buttonStyle(.bordered)
                        }.padding(.vertical, 4)
                    }
                    if let tags = adventure.recipe.tags, !tags.isEmpty {
                        Section("Tags") {
                            ScrollView(.horizontal) {
                                HStack {
                                    ForEach(tags, id: \.name) { tag in
                                        Button { sheet = .tag(tag.name) } label: { Label(tag.name, systemImage: "tag") }
                                            .buttonStyle(.bordered).accessibilityIdentifier("recipe-tag-" + tag.name)
                                    }
                                }
                            }.scrollIndicators(.hidden)
                        }
                    }
                    Section("Gather your ingredients") {
                        ForEach(adventure.recipe.ingredients) { ingredient in
                            let amount = adventure.quantity(ingredient).map { Numbers.display($0, locale: L10n.locale) } ?? ""
                            checkRow(key: "ingredient-\(ingredient.id)", label: ingredient.name,
                                subtitle: [amount, ingredient.unit ?? ""].filter { !$0.isEmpty }.joined(separator: " "), adventure: adventure)
                        }
                    }
                    Section("Let’s cook") {
                        ForEach(adventure.recipe.instructionSteps.sorted { $0.stepNumber < $1.stepNumber }) { step in
                            checkRow(key: "step-\(step.id)", label: IngredientPlaceholders.resolve(step.description, ingredients: adventure.recipe.ingredients, multiplier: adventure.multiplier, locale: L10n.locale),
                                     subtitle: L10n.format("Step %lld", step.stepNumber) + (step.durationMin.map { " · \($0) min" } ?? ""), adventure: adventure)
                        }
                    }
                    if let notes = adventure.recipe.notes, !notes.isEmpty { Section("Kitchen notes") { Text(notes) } }
                    Section { Button("Choose another recipe", action: browse) }
                }.sensoryFeedback(.selection, trigger: adventure.portions)
                 .sensoryFeedback(.selection, trigger: adventure.checked)
                 .safeAreaInset(edge: .bottom) {
                    VStack(spacing: 10) {
                        if let action = recentAction {
                            Text(L10n.text(action.undoes != nil ? "Undid · " : action.redoes != nil ? "Redid · " : action.isChecked ? "Checked · " : "Unchecked · ") + action.label)
                                .font(.subheadline).lineLimit(2).frame(maxWidth: .infinity, alignment: .leading)
                                .accessibilityIdentifier("recent-action")
                                .transition(.move(edge: .bottom).combined(with: .opacity))
                        }
                        HStack {
                            Button("Undo", systemImage: "arrow.uturn.backward") { store.update { $0.undo() } }
                                .disabled(!adventure.canUndo).accessibilityIdentifier("undo")
                            Spacer()
                            Button("Redo", systemImage: "arrow.uturn.forward") { store.update { $0.redo() } }
                                .disabled(!adventure.canRedo).accessibilityIdentifier("redo")
                            Spacer()
                            Button("History", systemImage: "clock.arrow.circlepath") { sheet = .history }
                        }
                    }.padding(.horizontal).padding(.vertical, 8).background(.regularMaterial)
                    .onChange(of: adventure.history.last?.id) { _, _ in
                        withAnimation(reduceMotion ? nil : .easeInOut(duration: 0.25)) { recentAction = adventure.history.last }
                    }
                    .task(id: recentAction?.id) {
                        guard recentAction != nil else { return }
                        do { try await Task.sleep(for: .seconds(4)) } catch { return }
                        withAnimation(reduceMotion ? nil : .easeInOut(duration: 0.25)) { recentAction = nil }
                    }
                }
            } else {
                ContentUnavailableView {
                    Label("What shall we cook?", systemImage: "fork.knife")
                } description: { Text("Choose a recipe. We’ll keep your place, even when life interrupts.") }
                actions: { Button("Choose a recipe", action: browse).buttonStyle(.borderedProminent) }
            }
        }.dismissibleKeyboard().navigationTitle("Onionary").navigationBarTitleDisplayMode(.inline)
            .confirmationDialog("Restart cooking? Current checks and history will be cleared; the latest recipe will be used.", isPresented: $restart, titleVisibility: .visible) {
                Button("Restart", role: .destructive) { store.restartCurrentRecipe() }
            }
            .toolbar { if store.current != nil {
                ToolbarItem(placement: .topBarLeading) {
                    Button { Task { await store.toggleCookingMode() } } label: {
                        Image(systemName: store.cookingActivity.active ? "flame.fill" : "flame")
                    }.accessibilityLabel("Cooking mode")
                        .accessibilityValue(Text(store.cookingActivity.active ? "On" : "Off"))
                        .accessibilityIdentifier("cooking-mode")
                }
                ToolbarItem(placement: .topBarTrailing) {
                Menu {
                    Button("Edit recipe") { store.editingRecipe = store.current?.recipe }
                    Button("Share recipe copy") { store.sharingRecipe = store.current?.recipe }
                    Button("Restart with latest recipe", role: .destructive) { restart = true }
                    Button("Adjust portions") { sheet = .portions }; Button("Tap history") { sheet = .history }
                }
                label: { Label("Cooking options", systemImage: "ellipsis.circle") }
                }
            } }
            // One presentation owner, with destination data bound to its identity.
            // Independent boolean/computed bindings can compete during SwiftUI updates.
            .sheet(item: $sheet) { destination in
                switch destination {
                case .portions: ScalingView(store: store)
                case .history: HistoryView(store: store)
                case .tag(let name):
                    NavigationStack {
                        List(RecipeBrowsing.recipes(store.kitchen.recipes, category: name)) { recipe in
                            Button(recipe.name) { store.visit(recipe); sheet = nil }
                                .accessibilityIdentifier("tag-recipe-" + String(recipe.id))
                        }.navigationTitle(name)
                            .toolbar { Button("Done") { sheet = nil } }
                    }
                }
            }
    }
    func checkRow(key: String, label: String, subtitle: String, adventure: Adventure) -> some View {
        let checked = adventure.checked.contains(key)
        return Button { store.update { $0.toggle(key: key, label: label) } } label: {
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: checked ? "checkmark.circle.fill" : "circle").font(.title2).foregroundStyle(checked ? onion : .secondary)
                VStack(alignment: .leading, spacing: 5) {
                    Text(label).foregroundStyle(.primary).strikethrough(checked).opacity(checked ? 0.55 : 1)
                    if !subtitle.isEmpty { Text(subtitle).font(.subheadline).foregroundStyle(.secondary) }
                }
                Spacer(minLength: 0)
            }.padding(.vertical, 3).frame(minHeight: 44).contentShape(Rectangle())
        }.buttonStyle(.plain).accessibilityLabel(label + (subtitle.isEmpty ? "" : ", " + subtitle))
            .accessibilityValue(checked ? "Checked" : "Unchecked").accessibilityHint("Double tap to toggle. Undo reverses the last change.")
            .accessibilityIdentifier(key)
    }
}

struct ScalingView: View {
    @Bindable var store: AppStore
    @Environment(\.dismiss) private var dismiss
    @State private var multiplier = "1"
    @State private var base = "1"
    @State private var portions = "1"
    @State private var ingredientID: Int?
    @State private var available = ""
    @State private var error: String?
    @FocusState private var editingField: String?
    var body: some View {
        NavigationStack {
            Form {
                if let adventure = store.current {
                    Section {
                        Text(adventure.recipe.name).font(.headline)
                        Text("Currently cooking for \(Numbers.display(adventure.portions, locale: L10n.locale)) portions")
                            .font(.subheadline).foregroundStyle(.secondary)
                        ForEach(adventure.recipe.ingredients) { ingredient in
                            HStack(alignment: .top) {
                                Text(ingredient.name)
                                Spacer()
                                Text([adventure.quantity(ingredient).map { Numbers.display($0, locale: L10n.locale) } ?? "", ingredient.unit ?? ""].filter { !$0.isEmpty }.joined(separator: " "))
                                    .monospacedDigit().foregroundStyle(.secondary)
                            }
                        }
                    } header: { Text("Your ingredients right now") }
                }
                Section {
                    field("Original recipe serves", text: $base)
                    HStack {
                        field("Cooking for", text: $portions).accessibilityIdentifier("portions")
                        Button { stepPortions(-1) } label: { Image(systemName: "minus").frame(width: 32, height: 32) }
                            .buttonStyle(.bordered).accessibilityLabel("Decrease portions by one")
                            .disabled((try? Numbers.parse(portions)) == nil || ((try? Numbers.parse(portions)) ?? 0) <= 1)
                        Button { stepPortions(1) } label: { Image(systemName: "plus").frame(width: 32, height: 32) }
                            .buttonStyle(.bordered).accessibilityLabel("Increase portions by one")
                    }

                } header: { Text("By portions") } footer: {
                    Text("Set how many portions the original recipe serves. Use + and − for whole-portion changes, or type any amount, such as 1.53 or 4.32.")
                }
                Section {
                    Picker("Ingredient", selection: $ingredientID) {
                        Text("Choose an ingredient").tag(nil as Int?)
                        ForEach(store.current?.recipe.ingredients.filter { ($0.quantity ?? 0) > 0 } ?? []) { ingredient in
                            Text("\(ingredient.name) (\(ingredient.unit ?? "units"))").tag(ingredient.id as Int?)
                        }
                    }
                    field("Amount you have", text: $available).accessibilityIdentifier("available-amount")
                    Button("Use this amount") {
                        guard let ingredient = store.current?.recipe.ingredients.first(where: { $0.id == ingredientID }) else { return }
                        apply { try $0.scale(ingredient: ingredient, available: Numbers.parse(available)) }
                    }.disabled(ingredientID == nil)
                } header: { Text("Use what you have") } footer: {
                    Text("Enter the amount in the ingredient’s original unit. If a recipe needs 200 g of cheese and you have 170 g, every ingredient becomes 0.85× its original amount. Cooking times stay unchanged.")
                }
                if let error { Text(error).foregroundStyle(.red) }
            }.dismissibleKeyboard().navigationTitle("Make it your size").navigationBarTitleDisplayMode(.inline)
                .toolbar { Button("Done") { commitPortions(); dismiss() } }
                .onChange(of: editingField) { old, _ in
                    if old == "Cooking for" || old == "Original recipe serves" { commitPortions() }
                    if old == "Amount you have", !available.isEmpty { commitIngredient() }
                }
                .onAppear {
                    if let adventure = store.current {
                        multiplier = Numbers.text(adventure.multiplier); base = Numbers.text(adventure.baseServings)
                        portions = Numbers.text(adventure.portions)
                    }
                }
        }
    }
    func field(_ label: String, text: Binding<String>) -> some View {
        VStack(alignment: .leading) { Text(LocalizedStringKey(label)).font(.caption).foregroundStyle(.secondary)
            TextField(LocalizedStringKey(label), text: Binding(get: {
                if editingField == label { return text.wrappedValue }
                return (try? Numbers.parse(text.wrappedValue)).map { Numbers.display($0, locale: L10n.locale) } ?? text.wrappedValue
            }, set: { text.wrappedValue = $0 }))
                .keyboardType(.decimalPad).focused($editingField, equals: label)
        }
    }
    func commitPortions() {
        apply { try $0.scale(baseServings: Numbers.parse(base), portions: Numbers.parse(portions)) }
    }
    func commitIngredient() {
        guard let ingredient = store.current?.recipe.ingredients.first(where: { $0.id == ingredientID }) else { return }
        apply { try $0.scale(ingredient: ingredient, available: Numbers.parse(available)) }
    }
    func stepPortions(_ change: Decimal) {
        do {
            let value = try Numbers.parse(portions) + change
            portions = Numbers.text(try Numbers.parse(Numbers.text(value)))
            commitPortions()
            UISelectionFeedbackGenerator().selectionChanged()
        } catch { self.error = error.localizedDescription }
    }
    func apply(_ operation: (inout Adventure) throws -> Void) {
        // Validate locally before dismissing; AppStore commits only after atomic persistence.
        do {
            guard var preview = store.current else { return }; try operation(&preview)
            store.update(operation)
            if store.error == nil {
                error = nil
                if let adventure = store.current {
                    base = Numbers.text(adventure.baseServings)
                    portions = Numbers.text(adventure.portions)
                }
            }
        } catch { self.error = error.localizedDescription }
    }
}

struct HistoryView: View {
    @Bindable var store: AppStore
    @Environment(\.dismiss) private var dismiss
    var body: some View {
        NavigationStack {
            List {
                if store.current?.history.isEmpty != false {
                    ContentUnavailableView("Every tap has a trail", systemImage: "clock.arrow.circlepath",
                        description: Text("Checks, unchecks, and undo actions appear here with their times."))
                }
                ForEach(store.current?.history.reversed() ?? []) { entry in
                    VStack(alignment: .leading, spacing: 5) {
                        Text(entry.label).font(.headline)
                        Text(L10n.text(entry.redoes != nil ? "Redo · " : entry.undoes == nil ? "" : "Undo · ") + L10n.text(entry.isChecked ? "Checked" : "Unchecked"))
                        Text(entry.timestamp.formatted(date: .abbreviated, time: .standard)).font(.caption).foregroundStyle(.secondary)
                    }.padding(.vertical, 5)
                }
            }.dismissibleKeyboard().navigationTitle("Tap history").toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    HStack {
                        Button("Undo", systemImage: "arrow.uturn.backward") { store.update { $0.undo() } }.disabled(store.current?.canUndo != true)
                        Button("Redo", systemImage: "arrow.uturn.forward") { store.update { $0.redo() } }.disabled(store.current?.canRedo != true)
                    }
                }
                ToolbarItem(placement: .topBarTrailing) { Button("Done") { dismiss() } }
            }
        }
    }
}

private extension View {
    @ViewBuilder
    func compactTagSection() -> some View {
        if #available(iOS 26.0, *) {
            self.listSectionMargins(.horizontal, 0)
                .listSectionMargins(.vertical, 4)
        } else {
            self.listSectionSpacing(8)
        }
    }
}
