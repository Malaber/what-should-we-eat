import SwiftUI
import OnionaryCore

/// Preview is read-only; only the explicit cooking action creates/visits an adventure.
struct RecipePreview: View {
    @Bindable var store: AppStore
    let recipe: Recipe
    let cook: () -> Void
    var body: some View {
        List {
            Section {
                Text(recipe.name).font(.title2.bold())
                if let servings = recipe.servings { LabeledContent("Original recipe serves", value: Numbers.display(servings, locale: L10n.locale)) }
                if let minutes = recipe.totalTimeMin { LabeledContent("Total minutes", value: String(minutes)) }
                if let tags = recipe.tags { Text(tags.map(\.name).joined(separator: " · ")).foregroundStyle(.secondary) }
                Button(store.kitchen.adventures.contains(where: { $0.id == recipe.id }) ? "Resume cooking" : "Cook this recipe", systemImage: "flame") {
                    store.visit(recipe); cook()
                }.buttonStyle(.borderedProminent).accessibilityIdentifier("preview-cook")
            }
            Section("Ingredients") {
                ForEach(recipe.ingredients) { ingredient in
                    VStack(alignment: .leading) {
                        if let group = ingredient.groupName { Text(group).font(.caption).foregroundStyle(.secondary) }
                        Text(ingredient.name)
                        Text([ingredient.quantity.map { Numbers.display($0, locale: L10n.locale) } ?? "", ingredient.unit ?? ""].joined(separator: " ")).foregroundStyle(.secondary)
                    }
                }
            }
            Section("Steps") {
                ForEach(recipe.instructionSteps.sorted { $0.stepNumber < $1.stepNumber }) { step in
                    VStack(alignment: .leading) {
                        if let group = step.groupName { Text(group).font(.caption).foregroundStyle(.secondary) }
                        Text(IngredientPlaceholders.resolve(step.description, ingredients: recipe.ingredients, multiplier: 1, locale: L10n.locale))
                    }
                }
            }
            if let notes = recipe.notes, !notes.isEmpty { Section("Notes") { Text(notes) } }
        }.navigationTitle("Recipe preview").navigationBarTitleDisplayMode(.inline)
            .accessibilityIdentifier("recipe-preview")
            .toolbar {
                Button("Edit recipe", systemImage: "pencil") { store.editingRecipe = recipe }
                Button("Share recipe copy", systemImage: "square.and.arrow.up") { store.sharingRecipe = recipe }
            }
    }
}
