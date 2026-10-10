import FoundationModels
import SwiftUI
import OnionaryCore

struct IntelligenceRecipeView: View {
    @Bindable var store: AppStore
    @State private var prompt = ""
    @State private var draft: RecipeDraft?
    @State private var busy = false
    @State private var error: String?
    @Environment(\.dismiss) private var dismiss
    private var unavailable: String? {
        guard #available(iOS 26, *) else { return L10n.text("Requires iOS 26 or later.") }
        switch SystemLanguageModel.default.availability {
        case .available: return nil
        case .unavailable(.appleIntelligenceNotEnabled): return L10n.text("Enable Apple Intelligence in Settings.")
        case .unavailable(.modelNotReady): return L10n.text("Apple Intelligence is downloading its model.")
        case .unavailable: return L10n.text("Apple Intelligence is unavailable on this device.")
        }
    }
    var body: some View {
        if let draft { RecipeEditor(store: store, draft: draft) }
        else {
            NavigationStack {
                Form {
                    Section("Describe your recipe") {
                        TextEditor(text: $prompt).frame(minHeight: 160)
                            .accessibilityLabel("Describe your recipe")
                        Text("Paste a recipe or describe ingredients, portions and cooking steps.").foregroundStyle(.secondary)
                    }
                    Section("Apple Intelligence") {
                        Text("Generation stays on this device. Review ingredients, quantities and cooking instructions before saving to your backend.")
                        if let unavailable { Text(unavailable).foregroundStyle(.secondary) }
                        if let error { Text(error).foregroundStyle(.red) }
                        Button("Create recipe draft") { Task { await generate() } }
                            .disabled(busy || prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || unavailable != nil)
                        if busy { ProgressView() }
                    }
                }.dismissibleKeyboard().navigationTitle("Create with Intelligence")
                    .toolbar { Button("Cancel") { dismiss() } }
                    .interactiveDismissDisabled(busy)
            }
        }
    }
    private func generate() async {
        guard #available(iOS 26, *), unavailable == nil else { return }
        busy = true; error = nil; defer { busy = false }
        do {
            let session = LanguageModelSession(instructions: "Create a recipe draft from the user's text, in their language. Preserve provided quantities and portions. Use explicit units. Never claim allergy safety. Return practical complete cooking instructions.")
            let result = try await session.respond(to: String(prompt.prefix(12000)), generating: GeneratedRecipe.self).content
            var recipe = RecipeDraft(); recipe.name = result.name; recipe.servings = Decimal(result.servings)
            recipe.ingredients = result.ingredients.map { source in
                var item = RecipeDraft.Item(); item.name = source.name; item.quantity = Decimal(source.quantity); item.unit = source.unit; return item
            }
            recipe.instructionSteps = result.steps.enumerated().map { index, description in
                var step = RecipeDraft.Step(); step.stepNumber = index + 1; step.description = description; return step
            }
            _ = try recipe.validatedData()
            draft = recipe
        } catch { self.error = error.localizedDescription }
    }
}

@available(iOS 26, *) @Generable private struct GeneratedRecipe {
    var name: String
    @Guide(.minimum(0.01), .maximum(1000)) var servings: Double
    @Guide(.minimumCount(1), .maximumCount(60)) var ingredients: [GeneratedIngredient]
    @Guide(.minimumCount(1), .maximumCount(40)) var steps: [String]
}
@available(iOS 26, *) @Generable private struct GeneratedIngredient {
    var name: String
    @Guide(.minimum(0.001), .maximum(1_000_000)) var quantity: Double
    var unit: String
}
