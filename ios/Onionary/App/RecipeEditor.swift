import SwiftUI
import OnionaryCore

struct RecipeEditor: View {
    @Bindable var store: AppStore
    @State var draft: RecipeDraft
    @State var recipeID: Int? = nil
    @State var draftID = UUID()
    @State private var draftScope: String?
    @State private var savedRecipe: Recipe?
    @State private var askingReload = false
    @State private var completed = false
    @Environment(\.dismiss) private var dismiss
    @State private var saving = false
    @State private var error: String?
    @FocusState private var focusedStep: UUID?
    @State private var showingStepHelp = false
    var body: some View {
        NavigationStack {
            editorForm.safeAreaInset(edge: .bottom) {
                if saving { ProgressView("Saving recipe…").padding().frame(maxWidth: .infinity).background(.regularMaterial) }
                if let error {
                    ShareLink("Export draft", item: exportText).padding(.horizontal)
                    Label(error, systemImage: "exclamationmark.triangle.fill")
                        .font(.callout).foregroundStyle(.red).padding()
                        .frame(maxWidth: .infinity, alignment: .leading).background(.regularMaterial)
                        .accessibilityIdentifier("recipe-save-error")
                }
            }.connectionRecovery(store).dismissibleKeyboard().navigationTitle(LocalizedStringKey(recipeID == nil ? "New recipe" : "Edit recipe"))
                .toolbar { editorToolbar }
                .alert("Ingredient amount help", isPresented: $showingStepHelp) {
                    Button("Done", role: .cancel) {}
                } message: {
                    Text("Change 100% in the placeholder to the share used in this step, such as 80%. Amounts follow your portions while cooking.")
                }
                .interactiveDismissDisabled(saving || askingReload)
                .onAppear { if draftScope == nil { draftScope = store.scope } }
                .onChange(of: draft) { _, _ in retain() }
                .onDisappear { if !completed { retain() } }
                .alert("Reload cooking recipe?", isPresented: $askingReload) {
                    Button("Reload and reset progress", role: .destructive) {
                        do { if let savedRecipe { try store.reloadCookingRecipe(savedRecipe) }; finish() }
                        catch { self.error = error.localizedDescription }
                    }
                    Button("Keep cooking progress", role: .cancel) { finish() }
                } message: { Text("The saved recipe changed. Reloading clears checks, portion adjustments and tap history for this cooking adventure.") }
        }
    }
    @ToolbarContentBuilder private var editorToolbar: some ToolbarContent {

                    ToolbarItemGroup(placement: .keyboard) {
                        if let focusedStep {
                            Menu {
                                ForEach(insertableIngredients) { ingredient in
                                    Button(ingredient.name) {
                                        insertAmount(ingredient, into: focusedStep)
                                    }
                                }
                            } label: { Label("Insert ingredient amount", systemImage: "plus.circle") }
                            .accessibilityIdentifier("insert-ingredient-amount")
                        }
                    }
                    ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() }.disabled(saving) }
                    ToolbarItem(placement: .primaryAction) { Button("Save") { Task { await save() } }.disabled(saving) }
    }
    private var editorForm: some View {
        WorkspacePanes(focus: focusedStep?.uuidString) {

            metadataSection
            tagsSection
            ingredientsSection
        } secondary: {
            stepsSection
        }.textFieldStyle(.roundedBorder).accessibilityIdentifier("recipe-editor")
    }
    private var metadataSection: some View {
                Section("Recipe") {
                    TextField("Name", text: $draft.name)
                    Picker("Food icon", selection: Binding(get: { FoodIcons.display(draft.icon) }, set: { draft.icon = $0 })) {
                        ForEach(FoodIcons.all, id: \.self) { Text($0).tag($0) }
                    }
                    VStack(alignment: .leading) {
                        Text("Original recipe serves").font(.caption).foregroundStyle(.secondary)
                        TextField("Original recipe serves", value: $draft.servings, format: .number).keyboardType(.decimalPad)
                    }
                    TextField("Notes", text: Binding(get: { draft.notes ?? "" }, set: { draft.notes = $0 }), axis: .vertical)
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Total minutes").font(.caption).foregroundStyle(.secondary)
                        TextField("Total minutes", value: $draft.totalTimeMin, format: .number).keyboardType(.numberPad)
                    }
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Active minutes").font(.caption).foregroundStyle(.secondary)
                        TextField("Active minutes", value: $draft.activeCookingTimeMin, format: .number).keyboardType(.numberPad)
                    }
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Calories per serving").font(.caption).foregroundStyle(.secondary)
                        TextField("Calories per serving", value: $draft.kcalPerServing, format: .number).keyboardType(.decimalPad)
                    }
                    TextField("Tags, separated by commas", text: Binding(get: { draft.tags.joined(separator: ", ") }, set: { draft.tags = $0.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) } }))
                }
    }
    private var tagsSection: some View {
                Section("Suggested tags") {
                    ForEach(Array(Set(RecipeBrowsing.categories(store.kitchen.recipes) + draft.tags)).sorted(), id: \.self) { tag in
                        Toggle(tag, isOn: Binding(
                            get: { draft.tags.contains { $0.localizedCaseInsensitiveCompare(tag) == .orderedSame } },
                            set: { selected in
                                draft.tags.removeAll { $0.localizedCaseInsensitiveCompare(tag) == .orderedSame }
                                if selected { draft.tags.append(tag) }
                            }))
                    }
                }
    }
    private var ingredientsSection: some View {
                Section("Ingredients") {
                    ForEach($draft.ingredients) { $item in
                        IngredientDraftRow(item: $item,
                            move: { moveIngredient(item.id, offset: $0) },
                            remove: { draft.ingredients.removeAll { $0.id == item.id } },
                            drop: { moveIngredient($0, before: item.id) })
                    }
                    Button("Add ingredient") { draft.ingredients.append(.init()) }
                }
    }
    private var stepsSection: some View {
                Section {
                    ForEach($draft.instructionSteps) { $step in
                        stepRow($step)
                    }.id("instruction-steps")
                    Button("Add step") { var step = RecipeDraft.Step(); step.stepNumber = draft.instructionSteps.count + 1; draft.instructionSteps.append(step) }
                } header: {
                    HStack {
                        Text("Steps")
                        Spacer()
                        Button { showingStepHelp = true } label: { Image(systemName: "info.circle") }
                            .accessibilityLabel("Ingredient amount help")
                            .accessibilityIdentifier("step-help")
                    }
                }


    }
    private func stepRow(_ binding: Binding<RecipeDraft.Step>) -> some View {
        let id = binding.wrappedValue.id
        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Step \(binding.wrappedValue.stepNumber)").font(.caption)
                Spacer()
                Menu {
                    Button("Move up") { moveStep(id, offset: -1) }
                    Button("Move down") { moveStep(id, offset: 1) }
                    Button("Delete step", role: .destructive) { draft.instructionSteps.removeAll { $0.id == id }; numberSteps() }
                } label: { Image(systemName: "line.3.horizontal").frame(width: 44, height: 44) }
                .accessibilityLabel("Reorder step")
            }
            TextField("Instruction group (optional)", text: Binding(
                get: { binding.wrappedValue.groupName ?? "" },
                set: { binding.wrappedValue.groupName = $0.isEmpty ? nil : $0 }))
            TextField("Instruction", text: binding.description, axis: .vertical)
                .focused($focusedStep, equals: id)
                .accessibilityIdentifier("instruction-" + id.uuidString)
            Text("Minutes").font(.caption).foregroundStyle(.secondary)
            TextField("Minutes", value: binding.durationMin, format: .number).keyboardType(.numberPad)
        }.id(id.uuidString)
    }
    private func numberSteps() {
        for index in draft.instructionSteps.indices { draft.instructionSteps[index].stepNumber = index + 1 }
    }
    private func moveStep(_ id: UUID, offset: Int) {
        guard let from = draft.instructionSteps.firstIndex(where: { $0.id == id }),
              draft.instructionSteps.indices.contains(from + offset) else { return }
        draft.instructionSteps.swapAt(from, from + offset)
        numberSteps()
    }
    private func moveIngredient(_ text: String?, before target: UUID) -> Bool {
        guard let text, let id = UUID(uuidString: text),
              let from = draft.ingredients.firstIndex(where: { $0.id == id }),
              let to = draft.ingredients.firstIndex(where: { $0.id == target }) else { return false }
        draft.ingredients.move(fromOffsets: IndexSet(integer: from), toOffset: to > from ? to + 1 : to)
        return true
    }
    private func moveIngredient(_ id: UUID, offset: Int) {
        guard let from = draft.ingredients.firstIndex(where: { $0.id == id }) else { return }
        let to = from + offset
        guard draft.ingredients.indices.contains(to) else { return }
        draft.ingredients.swapAt(from, to)
    }
    private var insertableIngredients: [RecipeDraft.Item] {
        draft.ingredients.filter { item in
            guard let quantity = item.quantity else { return false }
            return quantity > Decimal.zero && !item.name.isEmpty
        }
    }
    private func insertAmount(_ ingredient: RecipeDraft.Item, into stepID: UUID) {
        guard let index = draft.instructionSteps.firstIndex(where: { $0.id == stepID }) else { return }
        draft.instructionSteps[index].description += " {{" + ingredient.name + "|100%}}"
    }
    private var exportText: String {
        let encoder = JSONEncoder(); encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        return (try? encoder.encode(draft)).flatMap { String(data: $0, encoding: .utf8) } ?? draft.name
    }
    private func retain() {
        guard !completed, let draftScope else { return }
        do { try store.retainDraft(.init(id: draftID, recipeID: recipeID, draft: draft), scope: draftScope) }
        catch { self.error = L10n.text("Could not save recovery copy. Export your draft before closing.") }
    }
    private func finish() {
        do {
            try store.removeDraft(draftID, scope: draftScope ?? store.scope)
            completed = true; dismiss()
        } catch { self.error = error.localizedDescription }
    }
    private func save() async {
        saving = true; error = nil; defer { saving = false }
        retain()
        guard draftScope == store.scope else { error = L10n.text("Reconnect to the original account before saving this draft."); return }
        do {
            let recipe = try await store.saveRecipe(draft, id: recipeID)
            recipeID = recipe.id; savedRecipe = recipe; retain()
            if let current = store.current, current.id == recipe.id, current.recipe != recipe {
                askingReload = true
            } else { finish() }
        } catch {
            self.error = L10n.text("Save not confirmed. Your draft stays here. Check the server before retrying to avoid duplicates.") + "\n" + L10n.text(error.localizedDescription)
        }
    }
}

struct ImportRecipeView: View {
    @Bindable var store: AppStore
    @State var link: String
    @State private var draft: RecipeDraft?
    @State private var busy = false
    @State private var error: String?
    @Environment(\.dismiss) private var dismiss
    var body: some View {
        Group {
            if let draft { RecipeEditor(store: store, draft: draft) }
            else {
                NavigationStack {
                    Form {
                        TextField("Chefkoch or Onionary URL", text: $link).keyboardType(.URL).textInputAutocapitalization(.never).autocorrectionDisabled()
                        Button("Review recipe") { Task {
                            busy = true; defer { busy = false }
                            do { draft = try await store.importDraft(link) }
                            catch { self.error = L10n.text(error.localizedDescription) }
                        } }.disabled(busy)
                        if busy { ProgressView() }
                        if let error { Text(error).foregroundStyle(.red) }
                    }.connectionRecovery(store).dismissibleKeyboard().navigationTitle("Import recipe")
                        .toolbar { Button("Cancel") { dismiss() } }
                }
            }
        }
    }
}

struct EditRecipeView: View {
    @Bindable var store: AppStore
    let id: Int
    @State private var draft: RecipeDraft?
    @State private var error: String?
    @Environment(\.dismiss) private var dismiss
    var body: some View {
        Group {
            if let draft { RecipeEditor(store: store, draft: draft, recipeID: id) }
            else {
                NavigationStack {
                    VStack {
                        if let error { Text(error); Button("Retry") { Task { await load() } } }
                        else { ProgressView("Loading recipe") }
                    }.padding().toolbar { Button("Cancel") { dismiss() } }
                }
            }
        }.connectionRecovery(store).task(id: store.credential?.token) { if draft == nil { await load() } }
    }
    private func load() async {
        error = nil
        do { draft = try await store.recipeDraft(id: id) } catch { self.error = L10n.text(error.localizedDescription) }
    }
}

private struct IngredientDraftRow: View {
    @Binding var item: RecipeDraft.Item
    var move: (Int) -> Void
    var remove: () -> Void
    var drop: (String?) -> Bool
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            TextField("Ingredient group (optional)", text: Binding(get: { item.groupName ?? "" }, set: { item.groupName = $0.isEmpty ? nil : $0 }))
            HStack {
                TextField("Ingredient", text: $item.name)
                Menu {
                    Button("Move up") { move(-1) }
                    Button("Move down") { move(1) }
                    Button("Delete ingredient", role: .destructive, action: remove)
                } label: { Image(systemName: "line.3.horizontal").frame(minWidth: 44, minHeight: 44) }
                    .accessibilityLabel("Reorder ingredient").draggable(item.id.uuidString)
            }.dropDestination(for: String.self) { ids, _ in drop(ids.first) }
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Quantity").font(.caption).foregroundStyle(.secondary)
                    TextField("Quantity", value: $item.quantity, format: .number).keyboardType(.decimalPad)
                }
                TextField("Unit", text: Binding(get: { item.unit ?? "" }, set: { item.unit = $0 }))
            }
        }.padding(12).background(Color(uiColor: .secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 12))
    }
}
