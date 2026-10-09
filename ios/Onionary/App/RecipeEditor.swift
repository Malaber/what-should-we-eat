import SwiftUI
import OnionaryCore

struct RecipeEditor: View {
    @Bindable var store: AppStore
    @State var draft: RecipeDraft
    var recipeID: Int? = nil
    @Environment(\.dismiss) private var dismiss
    @State private var saving = false
    @State private var error: String?
    var body: some View {
        NavigationStack {
            Form {
                Section("Recipe") {
                    TextField("Name", text: $draft.name)
                    TextField("Notes", text: Binding(get: { draft.notes ?? "" }, set: { draft.notes = $0 }), axis: .vertical)
                    TextField("Total minutes", value: $draft.totalTimeMin, format: .number).keyboardType(.numberPad)
                    TextField("Active minutes", value: $draft.activeCookingTimeMin, format: .number).keyboardType(.numberPad)
                    TextField("Calories per serving", value: $draft.kcalPerServing, format: .number).keyboardType(.decimalPad)
                    TextField("Tags, separated by commas", text: Binding(get: { draft.tags.joined(separator: ", ") }, set: { draft.tags = $0.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) } }))
                }
                Section("Ingredients") {
                    ForEach($draft.ingredients) { $item in
                        VStack {
                            TextField("Ingredient", text: $item.name)
                            HStack {
                                TextField("Quantity", value: $item.quantity, format: .number).keyboardType(.decimalPad)
                                TextField("Unit", text: Binding(get: { item.unit ?? "" }, set: { item.unit = $0 }))
                            }
                        }
                    }.onDelete { draft.ingredients.remove(atOffsets: $0) }
                    Button("Add ingredient") { draft.ingredients.append(.init()) }
                }
                Section("Steps") {
                    ForEach($draft.instructionSteps) { $step in
                        VStack {
                            TextField("Instruction", text: $step.description, axis: .vertical)
                            TextField("Minutes", value: $step.durationMin, format: .number).keyboardType(.numberPad)
                        }
                    }.onDelete { draft.instructionSteps.remove(atOffsets: $0) }
                     .onMove { draft.instructionSteps.move(fromOffsets: $0, toOffset: $1) }
                    Button("Add step") { draft.instructionSteps.append(.init()) }
                }
                if let error { Section { Text(error).foregroundStyle(.red) } }
            }.navigationTitle(LocalizedStringKey(recipeID == nil ? "Import recipe" : "Edit recipe"))
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() }.disabled(saving) }
                    ToolbarItem(placement: .primaryAction) { Button("Save") { Task { await save() } }.disabled(saving) }
                }
                .interactiveDismissDisabled(saving)
        }
    }
    private func save() async {
        saving = true; defer { saving = false }
        do { try await store.saveRecipe(draft, id: recipeID); dismiss() }
        catch { self.error = error.localizedDescription }
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
                        TextField("Chefkoch URL", text: $link).keyboardType(.URL).textInputAutocapitalization(.never).autocorrectionDisabled()
                        Button("Review recipe") { Task {
                            busy = true; defer { busy = false }
                            do { draft = try await store.importDraft(link) }
                            catch { self.error = error.localizedDescription }
                        } }.disabled(busy)
                        if busy { ProgressView() }
                        if let error { Text(error).foregroundStyle(.red) }
                    }.navigationTitle("Import recipe")
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
        }.task { await load() }
    }
    private func load() async {
        error = nil
        do { draft = try await store.recipeDraft(id: id) } catch { self.error = error.localizedDescription }
    }
}
