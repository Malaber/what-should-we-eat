import SwiftUI
import OnionaryCore

struct RecipeEditor: View {
    @Bindable var store: AppStore
    @State var draft: RecipeDraft
    @State var recipeID: Int? = nil
    @State var draftID = UUID()
    var savedBaseline: RecipeDraft? = nil
    var isRecovery = false
    @State private var baseline: RecipeDraft?
    @State private var draftScope: String?
    @State private var savedRecipe: Recipe?
    @State private var askingReload = false
    @State private var completed = false
    @Environment(\.dismiss) private var dismiss
    @State private var saving = false
    @State private var error: String?
    @FocusState private var focusedStep: UUID?
    @State private var showingStepHelp = false
    @State private var tagInput = ""
    private enum RecipeOrder: String, Identifiable {
        case ingredients, steps
        var id: Self { self }
    }
    @State private var recipeOrder: RecipeOrder?
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
                .sheet(item: $recipeOrder) { order in
                    switch order {
                    case .ingredients:
                        RecipeOrderSheet(title: "Reorder ingredients", items: $draft.ingredients, groupName: \.groupName) { item in
                            item.name.isEmpty ? L10n.text("Ingredient") : item.name
                        }
                    case .steps:
                        RecipeOrderSheet(title: "Reorder steps", items: $draft.instructionSteps, groupName: \.groupName, didMove: numberSteps) { step in
                            step.description.isEmpty ? L10n.format("Step %lld", step.stepNumber) : step.description
                        }
                    }
                }
                .alert("Ingredient amount help", isPresented: $showingStepHelp) {
                    Button("Done", role: .cancel) {}
                } message: {
                    Text("Change 100% in the placeholder to the share used in this step, such as 80%. Amounts follow your portions while cooking.")
                }
                .interactiveDismissDisabled(saving || askingReload)
                .onAppear {
                    if draftScope == nil {
                        draftScope = store.scope
                        baseline = isRecovery ? savedBaseline : (recipeID == nil ? RecipeDraft() : draft)
                    }
                }
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
                    ToolbarItem(placement: .primaryAction) { Button("Save") { Task { await save() } }.disabled(saving || hasOverlongTag || hasInvalidIcon) }
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
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Food icon").font(.caption).foregroundStyle(.secondary)
                        TextField("One emoji (optional)", text: Binding(
                            get: { draft.icon ?? "" }, set: { draft.icon = $0.isEmpty ? nil : $0 }),
                                  prompt: Text(verbatim: FoodIcons.display(nil)))
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                            .accessibilityIdentifier("recipe-emoji")
                        if hasInvalidIcon {
                            Text("Enter a single emoji.").font(.footnote).foregroundStyle(.red)
                        }
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
                }
    }
    private var tagsSection: some View {
        Section("Tags") {
            if !draft.tags.isEmpty {
                ChipFlow(spacing: 8) {
                    ForEach(committedTags, id: \.self) { tag in
                        RemovableChip(title: tag, removeLabel: String(format: L10n.text("Remove tag %@"), tag)) {
                            draft.tags.removeAll { $0.localizedCaseInsensitiveCompare(tag) == .orderedSame }
                        }.accessibilityIdentifier("remove-tag-" + tag)
                    }
                }
            }
            HStack {
                TextField("Add tag", text: $tagInput)
                    .submitLabel(.done)
                    .onSubmit { addTag(pendingTag) }
                    .onChange(of: tagInput) { _, _ in retain() }
                    .accessibilityIdentifier("recipe-tag-input")
                Button { addTag(pendingTag) } label: {
                    Image(systemName: "plus.circle.fill").font(.title3).frame(minWidth: 44, minHeight: 44)
                }.buttonStyle(.borderless)
                    .accessibilityLabel("Add tag")
                    .accessibilityIdentifier("add-recipe-tag")
                    .disabled(!canAddTag(pendingTag))
            }
            if hasOverlongTag {
                Text("Use up to 100 characters per tag.").font(.footnote).foregroundStyle(.secondary)
            }
            if !pendingTag.isEmpty {
                ForEach(RecipeBrowsing.categories(store.kitchen.recipes, query: pendingTag)
                    .filter { canAddTag($0) }.prefix(6), id: \.self) { tag in
                    Button { addTag(tag) } label: { Label(tag, systemImage: "plus.circle") }
                        .accessibilityIdentifier("suggest-recipe-tag-" + tag)
                }
            }
        }
    }
    private var committedTags: [String] {
        var seen = Set<String>()
        return draft.tags.filter { seen.insert($0.lowercased()).inserted }
    }
    private var pendingTag: String { tagInput.trimmingCharacters(in: .whitespacesAndNewlines) }
    private var hasInvalidIcon: Bool {
        guard let icon = draft.icon, !icon.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return false }
        return FoodIcons.emoji(icon) == nil
    }
    private var hasOverlongTag: Bool {
        pendingTag.unicodeScalars.count > 100 || draft.tags.contains { $0.unicodeScalars.count > 100 }
    }

    private func canAddTag(_ tag: String) -> Bool {
        !tag.isEmpty && tag.unicodeScalars.count <= 100
            && !draft.tags.contains { $0.localizedCaseInsensitiveCompare(tag) == .orderedSame }
    }

    private func addTag(_ tag: String) {
        if canAddTag(tag) { draft.tags.append(tag) }
        if tag.unicodeScalars.count <= 100 { tagInput = "" }
    }

    private var recoveryCopy: RecipeDraft {
        var copy = draft
        copy.tags = committedTags
        if !pendingTag.isEmpty && !draft.tags.contains(where: { $0.localizedCaseInsensitiveCompare(pendingTag) == .orderedSame }) {
            copy.tags.append(pendingTag)
        }
        return copy
    }
    private var ingredientsSection: some View {
        Section {
            ForEach($draft.ingredients) { $item in
                VStack(alignment: .leading, spacing: 8) {
                    groupHeading(item.groupName, startsGroup: startsGroup(item, in: draft.ingredients, group: \.groupName))
                    IngredientDraftRow(item: $item, remove: { draft.ingredients.removeAll { $0.id == item.id } })
                        .padding(.leading, item.groupName == nil ? 0 : 8)
                }
            }
            Button("Add ingredient") { draft.ingredients.append(.init()) }
        } header: {
            HStack {
                Text("Ingredients")
                Spacer()
                if !draft.ingredients.isEmpty {
                    Button("Reorder", systemImage: "arrow.up.arrow.down") { recipeOrder = .ingredients }
                        .accessibilityLabel("Reorder ingredients")
                }
            }
        }
    }
    private var stepsSection: some View {
                Section {
                    ForEach($draft.instructionSteps) { $step in
                        VStack(alignment: .leading, spacing: 8) {
                            groupHeading(step.groupName, startsGroup: startsGroup(step, in: draft.instructionSteps, group: \.groupName))
                            stepRow($step).padding(.leading, step.groupName == nil ? 0 : 8)
                        }
                    }.id("instruction-steps")
                    Button("Add step") { var step = RecipeDraft.Step(); step.stepNumber = draft.instructionSteps.count + 1; draft.instructionSteps.append(step) }
                } header: {
                    HStack {
                        Text("Steps")
                        Spacer()
                        if !draft.instructionSteps.isEmpty {
                            Button("Reorder", systemImage: "arrow.up.arrow.down") { recipeOrder = .steps }
                                .accessibilityLabel("Reorder steps")
                        }
                        Button { showingStepHelp = true } label: { Image(systemName: "info.circle") }
                            .accessibilityLabel("Ingredient amount help")
                            .accessibilityIdentifier("step-help")
                    }
                }


    }
    @ViewBuilder private func groupHeading(_ name: String?, startsGroup: Bool) -> some View {
        if startsGroup, let name, !name.isEmpty {
            Text(name).font(.headline).accessibilityAddTraits(.isHeader)
        }
    }
    private func startsGroup<Item: Identifiable>(_ item: Item, in items: [Item], group: KeyPath<Item, String?>) -> Bool {
        guard let index = items.firstIndex(where: { $0.id == item.id }) else { return false }
        return index == 0 || items[index - 1][keyPath: group] != item[keyPath: group]
    }
    private func stepRow(_ binding: Binding<RecipeDraft.Step>) -> some View {
        let id = binding.wrappedValue.id
        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Step \(binding.wrappedValue.stepNumber)").font(.caption)
                Spacer()
                Button(role: .destructive) {
                    draft.instructionSteps.removeAll { $0.id == id }
                    numberSteps()
                } label: {
                    Label("Delete step", systemImage: "trash").labelStyle(.iconOnly)
                        .frame(minWidth: 44, minHeight: 44).contentShape(Rectangle())
                }.buttonStyle(.borderless)
            }
            TextField("Instruction", text: binding.description, axis: .vertical)
                .focused($focusedStep, equals: id)
                .accessibilityIdentifier("instruction-" + id.uuidString)
            Text("Minutes").font(.caption).foregroundStyle(.secondary)
            TextField("Minutes", value: binding.durationMin, format: .number).keyboardType(.numberPad)
        }.recipeDraftCard().id(id.uuidString)
    }
    private func numberSteps() {
        for index in draft.instructionSteps.indices { draft.instructionSteps[index].stepNumber = index + 1 }
    }
    private var insertableIngredients: [RecipeDraft.Item] {
        draft.ingredients.filter { item in
            guard let quantity = item.quantity else { return false }
            return quantity > Decimal.zero && !item.name.isEmpty
        }
    }
    private func insertAmount(_ ingredient: RecipeDraft.Item, into stepID: UUID) {
        guard let index = draft.instructionSteps.firstIndex(where: { $0.id == stepID }) else { return }
        let duplicate = draft.ingredients.filter { $0.name.caseInsensitiveCompare(ingredient.name) == .orderedSame }.count > 1
        let key = IngredientPlaceholders.key(name: ingredient.name, group: duplicate ? ingredient.groupName : nil)
        draft.instructionSteps[index].description += " {{" + key + "|100%}}"
    }
    private var exportText: String {
        let encoder = JSONEncoder(); encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        return (try? encoder.encode(recoveryCopy)).flatMap { String(data: $0, encoding: .utf8) } ?? draft.name
    }
    private func retain() {
        guard !completed, let draftScope else { return }
        let copy = recoveryCopy
        do {
            if let baseline, copy.changes(from: baseline).isEmpty {
                if store.savedDrafts.contains(where: { $0.id == draftID }) {
                    try store.removeDraft(draftID, scope: draftScope)
                }
            } else {
                try store.retainDraft(.init(id: draftID, recipeID: recipeID, draft: copy, baseline: baseline), scope: draftScope)
            }
        } catch { self.error = L10n.text("Could not save recovery copy. Export your draft before closing.") }
    }
    private func finish() {
        do {
            try store.removeDraft(draftID, scope: draftScope ?? store.scope)
            completed = true; dismiss()
        } catch { self.error = error.localizedDescription }
    }
    private func save() async {
        saving = true; error = nil; defer { saving = false }
        guard !hasOverlongTag, !hasInvalidIcon else { return }
        if recipeID != nil, let baseline, recoveryCopy.changes(from: baseline).isEmpty {
            finish()
            return
        }
        draft.icon = draft.icon.flatMap(FoodIcons.emoji)
        draft.tags = committedTags
        addTag(pendingTag)
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
                        TextField("Recipe URL", text: $link).keyboardType(.URL).textInputAutocapitalization(.never).autocorrectionDisabled()
                            .accessibilityIdentifier("recipe-import-url")
                        Text("Other recipe websites use Apple Intelligence on this device.")
                            .font(.footnote).foregroundStyle(.secondary)
                        Button("Review recipe") { Task {
                            busy = true; error = nil; defer { busy = false }
                            do { draft = try await store.importDraft(link) }
                            catch { self.error = L10n.text(error.localizedDescription) }
                        } }.disabled(busy).accessibilityIdentifier("review-recipe-import")
                        if busy { ProgressView() }
                        if let error { Text(error).foregroundStyle(.red) }
                    }.accessibilityIdentifier("recipe-import-form")
                        .connectionRecovery(store).dismissibleKeyboard().navigationTitle("Import recipe")
                        .interactiveDismissDisabled(busy)
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

struct DraftChangesView: View {
    let store: AppStore
    let saved: SavedRecipeDraft
    @Environment(\.dismiss) private var dismiss
    @State private var currentRecipe: RecipeDraft?
    @State private var loading = true

    var body: some View {
        NavigationStack {
            List {
                if let baseline = saved.baseline ?? currentRecipe {
                    if saved.baseline == nil, saved.recipeID != nil {
                        Text("Compared with the recipe currently on the server.").foregroundStyle(.secondary)
                    }
                    let changes = saved.draft.changes(from: baseline)
                    if changes.isEmpty { Text("No recipe changes") }
                    ForEach(changes) { change in
                        Section(LocalizedStringKey(change.field)) {
                            if !change.before.isEmpty {
                                Text("Before").font(.caption).foregroundStyle(.secondary)
                                Text(change.before)
                            }
                            Text("Draft").font(.caption).foregroundStyle(.secondary)
                            if change.after.isEmpty { Text("Cleared").foregroundStyle(.secondary) }
                            else { Text(change.after) }
                        }
                    }
                } else if loading {
                    ProgressView()
                } else {
                    Text("This draft was saved before changes were tracked.")
                }
            }.navigationTitle("Draft changes").navigationBarTitleDisplayMode(.inline)
                .toolbar { Button("Done") { dismiss() } }
        }.task {
            defer { loading = false }
            guard saved.baseline == nil else { return }
            if let id = saved.recipeID { currentRecipe = try? await store.recipeDraft(id: id) }
            else { currentRecipe = RecipeDraft() }
        }
    }
}

private struct IngredientDraftRow: View {
    @Binding var item: RecipeDraft.Item
    var remove: () -> Void
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                TextField("Ingredient", text: $item.name)
                Button(role: .destructive, action: remove) {
                    Label("Delete ingredient", systemImage: "trash").labelStyle(.iconOnly)
                        .frame(minWidth: 44, minHeight: 44).contentShape(Rectangle())
                }.buttonStyle(.borderless)
            }
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Quantity").font(.caption).foregroundStyle(.secondary)
                    TextField("Quantity", value: $item.quantity, format: .number).keyboardType(.decimalPad)
                }
                TextField("Unit", text: Binding(get: { item.unit ?? "" }, set: { item.unit = $0 }))
            }
        }.recipeDraftCard()
    }
}

private extension View {
    func recipeDraftCard() -> some View {
        let shape = RoundedRectangle(cornerRadius: 12)
        return padding(12)
            .background(Color(uiColor: .secondarySystemGroupedBackground), in: shape)
            .overlay { shape.strokeBorder(Color(uiColor: .separator)).allowsHitTesting(false) }
    }
}

private struct RecipeOrderSheet<Item: Identifiable>: View {
    let title: LocalizedStringKey
    @Binding var items: [Item]
    let groupName: WritableKeyPath<Item, String?>
    var didMove: () -> Void = {}
    var rowTitle: (Item) -> String
    @Environment(\.dismiss) private var dismiss
    @State private var groupsAdded: [String] = []
    @State private var newGroup = ""
    @State private var addingGroup = false

    private var groups: [String] {
        var seen = Set<String>()
        return (items.compactMap { $0[keyPath: groupName] } + groupsAdded)
            .filter { !$0.isEmpty && seen.insert($0).inserted }
    }
    private var trimmedGroup: String { newGroup.trimmingCharacters(in: .whitespacesAndNewlines) }
    private var canAddGroup: Bool {
        !trimmedGroup.isEmpty && trimmedGroup.unicodeScalars.count <= 100 && !groups.contains(trimmedGroup)
    }

    var body: some View {
        NavigationStack {
            List {
                ForEach(items) { item in
                    let index = items.firstIndex { $0.id == item.id }
                    let name = rowTitle(item)
                    HStack {
                        VStack(alignment: .leading) {
                            Text(name).lineLimit(2)
                            if let group = item[keyPath: groupName] {
                                Text(group).font(.caption).foregroundStyle(.secondary)
                            }
                        }
                        Spacer()
                        if !groups.isEmpty {
                            Menu {
                                Picker("Group", selection: Binding(
                                    get: { item[keyPath: groupName] },
                                    set: { assign(item.id, to: $0) }
                                )) {
                                    Text("Without group").tag(nil as String?)
                                    ForEach(groups, id: \.self) { Text($0).tag(Optional($0)) }
                                }
                            } label: {
                                Label("Group", systemImage: "folder").labelStyle(.iconOnly)
                                    .frame(minWidth: 44, minHeight: 44)
                            }.accessibilityLabel("Group")
                        }
                        Button { moveOne(item.id, by: -1) } label: {
                            Label("Move \(name) up", systemImage: "chevron.up").labelStyle(.iconOnly)
                                .frame(minWidth: 44, minHeight: 44)
                        }.disabled(index == items.startIndex)
                        Button { moveOne(item.id, by: 1) } label: {
                            Label("Move \(name) down", systemImage: "chevron.down").labelStyle(.iconOnly)
                                .frame(minWidth: 44, minHeight: 44)
                        }.disabled(index == items.index(before: items.endIndex))
                    }
                    .buttonStyle(.borderless)
                }.onMove(perform: move)
            }
            .environment(\.editMode, .constant(.active))
            .accessibilityIdentifier("recipe-order-list")
            .navigationTitle(title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) { Button("Add group", systemImage: "folder.badge.plus") { addingGroup = true } }
                ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } }
            }
            .alert("Add group", isPresented: $addingGroup) {
                TextField("Group name", text: $newGroup)
                Button("Cancel", role: .cancel) { newGroup = "" }
                Button("Add") {
                    if canAddGroup { groupsAdded.append(trimmedGroup) }
                    newGroup = ""
                }.disabled(!canAddGroup)
            }
        }
    }

    private func move(_ offsets: IndexSet, to destination: Int) {
        items.move(fromOffsets: offsets, toOffset: destination)
        didMove()
    }

    private func moveOne(_ id: Item.ID, by offset: Int) {
        guard let index = items.firstIndex(where: { $0.id == id }),
              items.indices.contains(index + offset) else { return }
        move(IndexSet(integer: index), to: offset > 0 ? index + 2 : index - 1)
    }

    private func assign(_ id: Item.ID, to group: String?) {
        guard let index = items.firstIndex(where: { $0.id == id }), items[index][keyPath: groupName] != group else { return }
        var reordered = items
        var item = reordered.remove(at: index)
        item[keyPath: groupName] = group
        let sibling = reordered.lastIndex { $0[keyPath: groupName] == group }
        reordered.insert(item, at: sibling.map { $0 + 1 } ?? index)
        items = reordered
        didMove()
    }
}
