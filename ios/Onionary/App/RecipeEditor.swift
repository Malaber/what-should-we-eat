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
                        RecipeOrderSheet(title: "Reorder ingredients", items: $draft.ingredients) { item in
                            Text(item.name.isEmpty ? L10n.text("Ingredient") : item.name).lineLimit(2)
                        }
                    case .steps:
                        RecipeOrderSheet(title: "Reorder steps", items: $draft.instructionSteps, didMove: numberSteps) { step in
                            Text(step.description.isEmpty ? L10n.format("Step %lld", step.stepNumber) : step.description).lineLimit(2)
                        }
                    }
                }
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
                    ToolbarItem(placement: .primaryAction) { Button("Save") { Task { await save() } }.disabled(saving || hasOverlongTag) }
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
                }
    }
    private var tagsSection: some View {
        Section("Tags") {
            if !draft.tags.isEmpty {
                RecipeTagFlow(spacing: 8) {
                    ForEach(committedTags, id: \.self) { tag in
                        Button { draft.tags.removeAll { $0.localizedCaseInsensitiveCompare(tag) == .orderedSame } } label: {
                            HStack(spacing: 6) {
                                Text(tag)
                                Image(systemName: "xmark").font(.caption.weight(.semibold)).accessibilityHidden(true)
                            }
                            .padding(.horizontal, 10)
                            .padding(.vertical, 4)
                            .background(OnionaryTheme.accent.opacity(0.15), in: Capsule())
                            .overlay { Capsule().strokeBorder(OnionaryTheme.accent.opacity(0.45)) }
                            .frame(minHeight: 44)
                            .contentShape(Rectangle())
                        }.buttonStyle(.plain)
                            .accessibilityLabel(Text(String(format: L10n.text("Remove tag %@"), tag)))
                            .accessibilityIdentifier("remove-tag-" + tag)
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
        if !pendingTag.isEmpty && !draft.tags.contains(where: { $0.localizedCaseInsensitiveCompare(pendingTag) == .orderedSame }) {
            copy.tags.append(pendingTag)
        }
        return copy
    }
    private var ingredientsSection: some View {
        Section {
            ForEach($draft.ingredients) { $item in
                IngredientDraftRow(item: $item, remove: { draft.ingredients.removeAll { $0.id == item.id } })
            }
            Button("Add ingredient") { draft.ingredients.append(.init()) }
        } header: {
            HStack {
                Text("Ingredients")
                Spacer()
                if draft.ingredients.count > 1 {
                    Button("Reorder", systemImage: "arrow.up.arrow.down") { recipeOrder = .ingredients }
                        .accessibilityLabel("Reorder ingredients")
                }
            }
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
                        if draft.instructionSteps.count > 1 {
                            Button("Reorder", systemImage: "arrow.up.arrow.down") { recipeOrder = .steps }
                                .accessibilityLabel("Reorder steps")
                        }
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
                    Button("Delete step", role: .destructive) { draft.instructionSteps.removeAll { $0.id == id }; numberSteps() }
                } label: { Image(systemName: "ellipsis.circle").frame(width: 44, height: 44) }
                .accessibilityLabel("Step options")
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
        return (try? encoder.encode(recoveryCopy)).flatMap { String(data: $0, encoding: .utf8) } ?? draft.name
    }
    private func retain() {
        guard !completed, let draftScope else { return }
        do { try store.retainDraft(.init(id: draftID, recipeID: recipeID, draft: recoveryCopy), scope: draftScope) }
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
        guard !hasOverlongTag else { return }
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

private struct RecipeTagFlow: Layout {
    let spacing: CGFloat

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        arrange(width: proposal.width ?? .infinity, subviews: subviews) { _, _, _ in }
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        _ = arrange(width: bounds.width, subviews: subviews) { view, origin, size in
            view.place(at: CGPoint(x: bounds.minX + origin.x, y: bounds.minY + origin.y),
                       anchor: .topLeading, proposal: ProposedViewSize(size))
        }
    }

    private func arrange(width: CGFloat, subviews: Subviews, place: (LayoutSubview, CGPoint, CGSize) -> Void) -> CGSize {
        var x: CGFloat = 0
        var y: CGFloat = 0
        var rowHeight: CGFloat = 0
        var usedWidth: CGFloat = 0
        for view in subviews {
            let proposedWidth = min(view.sizeThatFits(.unspecified).width, width)
            let size = view.sizeThatFits(ProposedViewSize(width: proposedWidth, height: nil))
            if x > 0, x + size.width > width {
                x = 0
                y += rowHeight + spacing
                rowHeight = 0
            }
            place(view, CGPoint(x: x, y: y), size)
            usedWidth = max(usedWidth, x + size.width)
            x += size.width + spacing
            rowHeight = max(rowHeight, size.height)
        }
        return CGSize(width: usedWidth, height: y + rowHeight)
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
    var remove: () -> Void
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            TextField("Ingredient group (optional)", text: Binding(get: { item.groupName ?? "" }, set: { item.groupName = $0.isEmpty ? nil : $0 }))
            HStack {
                TextField("Ingredient", text: $item.name)
                Menu {
                    Button("Delete ingredient", role: .destructive, action: remove)
                } label: { Image(systemName: "ellipsis.circle").frame(minWidth: 44, minHeight: 44) }
                    .accessibilityLabel("Ingredient options")
            }
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

private struct RecipeOrderSheet<Item: Identifiable, Row: View>: View {
    let title: LocalizedStringKey
    @Binding var items: [Item]
    var didMove: () -> Void = {}
    @ViewBuilder var row: (Item) -> Row
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            List {
                ForEach(items, content: row)
                    .onMove { offsets, destination in
                        items.move(fromOffsets: offsets, toOffset: destination)
                        didMove()
                    }
            }
            .environment(\.editMode, .constant(.active))
            .navigationTitle(title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
        }
    }
}
