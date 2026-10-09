import SwiftUI
import OnionaryCore

private let onion = OnionaryTheme.accent

struct RootView: View {
    @Bindable var store: AppStore
    @State private var tab = 0
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
                    NavigationStack {
                        List {
                            Section("Your kitchen") {
                                Text(store.credential?.server.host() ?? "").font(.headline)
                                Text("Progress is saved on this device separately for each backend and account.").foregroundStyle(.secondary)
                                ConnectionView(store: store)
                            }
                            Section {
                                Button("Sign out", role: .destructive) { Task { await store.disconnect() } }.disabled(store.busy)
                            }
                        }.navigationTitle("Settings")
                    }.tabItem { Label("Settings", systemImage: "gearshape") }.tag(2)
                }
            }
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
    var filtered: [Recipe] { store.kitchen.recipes.filter { search.isEmpty || $0.name.localizedCaseInsensitiveContains(search) } }
    var body: some View {
        List {
            if search.isEmpty && !store.kitchen.recent.isEmpty {
                Section("Recently visited") {
                    ForEach(store.kitchen.recent.prefix(8)) { adventure in
                        recipeRow(adventure.recipe, subtitle: "Continue · \(adventure.checked.count) checked")
                    }
                }
            }
            Section("Your recipes") {
                ForEach(filtered) { recipe in recipeRow(recipe, subtitle: recipe.totalTimeMin.map { "\($0) min" } ?? "Ready when you are") }
            }
            if filtered.isEmpty {
                ContentUnavailableView(search.isEmpty ? "Your recipe book is waiting" : "No matching recipes",
                    systemImage: "book.closed", description: Text(search.isEmpty ? "Add recipes in your web kitchen, then refresh here." : "Try another search."))
            }
        }.navigationTitle("Recipe book").searchable(text: $search, prompt: "Find something delicious")
            .refreshable { await store.refresh() }
            .toolbar { Button("Refresh", systemImage: "arrow.clockwise") { Task { await store.refresh() } } }
            .task {
                if store.kitchen.recipes.isEmpty && !ProcessInfo.processInfo.arguments.contains("--ui-testing") { await store.refresh() }
            }
    }
    func recipeRow(_ recipe: Recipe, subtitle: String) -> some View {
        Button { store.visit(recipe); selected() } label: {
            HStack(spacing: 14) {
                Image(systemName: "leaf").font(.title2).foregroundStyle(onion).frame(width: 44, height: 52)
                VStack(alignment: .leading, spacing: 5) {
                    Text(recipe.name).font(.headline).foregroundStyle(.primary)
                    Text(subtitle).font(.caption).foregroundStyle(.secondary)
                }
                Spacer(); Image(systemName: "chevron.right").font(.caption).foregroundStyle(.tertiary)
            }.padding(.vertical, 5)
        }.accessibilityIdentifier("recipe-\(recipe.id)")
    }
}

struct CookingView: View {
    @Bindable var store: AppStore
    var browse: () -> Void
    @State private var scaling = false
    @State private var history = false
    @State private var recentAction: CheckChange?
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    var body: some View {
        Group {
            if let adventure = store.current {
                List {
                    Section {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("TODAY’S COOKING ADVENTURE").font(.caption2.bold()).tracking(2).foregroundStyle(onion)
                            Text(adventure.recipe.name).font(.system(.largeTitle, design: .serif, weight: .semibold))
                            HStack {
                                Label("\(Numbers.display(adventure.multiplier))× recipe", systemImage: "scalemass")
                                if let minutes = adventure.recipe.totalTimeMin { Label("\(minutes) min", systemImage: "clock") }
                            }.font(.subheadline).foregroundStyle(.secondary)
                            HStack(spacing: 16) {
                                Button {
                                    store.update { try $0.scale(baseServings: $0.baseServings, portions: $0.portions - 1) }
                                } label: { Image(systemName: "minus").frame(width: 32, height: 32) }
                                    .buttonStyle(.bordered).disabled(adventure.portions <= 1)
                                    .accessibilityLabel("One fewer portion").accessibilityIdentifier("portion-minus")
                                Button { scaling = true } label: {
                                    VStack(spacing: 3) {
                                        Text(Numbers.display(adventure.portions)).font(.title2.bold()).monospacedDigit().lineLimit(1).minimumScaleFactor(0.5)
                                        Text("portions · tap to edit").font(.caption2)
                                    }.frame(maxWidth: .infinity)
                                }.buttonStyle(.plain).accessibilityLabel("\(Numbers.display(adventure.portions)) portions. Edit amount")
                                Button {
                                    store.update { try $0.scale(baseServings: $0.baseServings, portions: $0.portions + 1) }
                                } label: { Image(systemName: "plus").frame(width: 32, height: 32) }
                                    .buttonStyle(.bordered).accessibilityLabel("One more portion").accessibilityIdentifier("portion-plus")
                            }
                            ProgressView(value: Double(adventure.checked.count), total: Double(max(1, adventure.recipe.ingredients.count + adventure.recipe.instructionSteps.count)))
                                .accessibilityLabel("Cooking progress")
                            Text("\(adventure.checked.count) of \(adventure.recipe.ingredients.count + adventure.recipe.instructionSteps.count) checked")
                                .font(.caption).foregroundStyle(.secondary)
                            Button("Adjust portions", systemImage: "slider.horizontal.3") { scaling = true }.buttonStyle(.bordered)
                        }.padding(.vertical, 12)
                    }
                    Section("Gather your ingredients") {
                        ForEach(adventure.recipe.ingredients) { ingredient in
                            let amount = adventure.quantity(ingredient).map(Numbers.display) ?? ""
                            checkRow(key: "ingredient-\(ingredient.id)", label: ingredient.name,
                                subtitle: [amount, ingredient.unit ?? ""].filter { !$0.isEmpty }.joined(separator: " "), adventure: adventure)
                        }
                    }
                    Section("Let’s cook") {
                        ForEach(adventure.recipe.instructionSteps.sorted { $0.stepNumber < $1.stepNumber }) { step in
                            checkRow(key: "step-\(step.id)", label: step.description,
                                     subtitle: "Step \(step.stepNumber)" + (step.durationMin.map { " · \($0) min" } ?? ""), adventure: adventure)
                        }
                    }
                    if let notes = adventure.recipe.notes, !notes.isEmpty { Section("Kitchen notes") { Text(notes) } }
                    Section { Button("Choose another recipe", action: browse) }
                }.sensoryFeedback(.selection, trigger: adventure.portions)
                 .sensoryFeedback(.selection, trigger: adventure.checked)
                 .safeAreaInset(edge: .bottom) {
                    VStack(spacing: 10) {
                        if let action = recentAction {
                            Text((action.undoes != nil ? "Undid · " : action.redoes != nil ? "Redid · " : action.isChecked ? "Checked · " : "Unchecked · ") + action.label)
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
                            Button("History", systemImage: "clock.arrow.circlepath") { history = true }
                        }
                    }.padding().background(.regularMaterial)
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
        }.navigationTitle("Onionary").navigationBarTitleDisplayMode(.inline)
            .toolbar { if store.current != nil {
                Menu { Button("Adjust portions") { scaling = true }; Button("Tap history") { history = true } }
                label: { Label("Cooking options", systemImage: "ellipsis.circle") }
            } }
            .sheet(isPresented: $scaling) { ScalingView(store: store) }
            .sheet(isPresented: $history) { HistoryView(store: store) }
    }
    func checkRow(key: String, label: String, subtitle: String, adventure: Adventure) -> some View {
        let checked = adventure.checked.contains(key)
        return Button { store.update { $0.toggle(key: key, label: label) } } label: {
            HStack(alignment: .top, spacing: 14) {
                Image(systemName: checked ? "checkmark.circle.fill" : "circle").font(.title2).foregroundStyle(checked ? onion : .secondary)
                VStack(alignment: .leading, spacing: 5) {
                    Text(label).foregroundStyle(.primary).strikethrough(checked).opacity(checked ? 0.55 : 1)
                    if !subtitle.isEmpty { Text(subtitle).font(.subheadline).foregroundStyle(.secondary) }
                }
                Spacer(minLength: 0)
            }.padding(.vertical, 10).frame(minHeight: 44).contentShape(Rectangle())
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
                        Text("Currently cooking for \(Numbers.display(adventure.portions)) portions")
                            .font(.subheadline).foregroundStyle(.secondary)
                        ForEach(adventure.recipe.ingredients) { ingredient in
                            HStack(alignment: .top) {
                                Text(ingredient.name)
                                Spacer()
                                Text([adventure.quantity(ingredient).map { Numbers.display($0) } ?? "", ingredient.unit ?? ""].filter { !$0.isEmpty }.joined(separator: " "))
                                    .monospacedDigit().foregroundStyle(.secondary)
                            }
                        }
                    } header: { Text("Your ingredients right now") }
                }
                Section("Scale the whole recipe") {
                    field("Recipe multiplier", text: $multiplier).accessibilityIdentifier("multiplier")
                    Button("Apply multiplier") { apply { try $0.scale(multiplier: Numbers.parse(multiplier)) } }
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
                    Button("Apply portions") { apply { try $0.scale(baseServings: Numbers.parse(base), portions: Numbers.parse(portions)) } }
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
            }.navigationTitle("Make it your size").navigationBarTitleDisplayMode(.inline)
                .toolbar { Button("Done") { dismiss() } }
                .onAppear {
                    if let adventure = store.current {
                        multiplier = Numbers.text(adventure.multiplier); base = Numbers.text(adventure.baseServings)
                        portions = Numbers.text(adventure.portions)
                    }
                }
        }
    }
    func field(_ label: String, text: Binding<String>) -> some View {
        VStack(alignment: .leading) { Text(label).font(.caption).foregroundStyle(.secondary)
            TextField(label, text: Binding(get: {
                if editingField == label { return text.wrappedValue }
                return (try? Numbers.parse(text.wrappedValue)).map { Numbers.display($0) } ?? text.wrappedValue
            }, set: { text.wrappedValue = $0 }))
                .keyboardType(.decimalPad).focused($editingField, equals: label)
        }
    }
    func stepPortions(_ change: Decimal) {
        do {
            let value = try Numbers.parse(portions) + change
            portions = Numbers.text(try Numbers.parse(Numbers.text(value)))
            UISelectionFeedbackGenerator().selectionChanged()
        } catch { self.error = error.localizedDescription }
    }
    func apply(_ operation: (inout Adventure) throws -> Void) {
        // Validate locally before dismissing; AppStore commits only after atomic persistence.
        do {
            guard var preview = store.current else { return }; try operation(&preview)
            store.update(operation)
            if store.error == nil { dismiss() }
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
                        Text((entry.redoes != nil ? "Redo · " : entry.undoes == nil ? "" : "Undo · ") + (entry.isChecked ? "Checked" : "Unchecked"))
                        Text(entry.timestamp.formatted(date: .abbreviated, time: .standard)).font(.caption).foregroundStyle(.secondary)
                    }.padding(.vertical, 5)
                }
            }.navigationTitle("Tap history").toolbar {
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
