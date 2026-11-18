import SwiftUI
import OnionaryCore

/// Adjustments in the preview remain local until cooking starts or resumes.
struct RecipePreview: View {
    @Environment(\.onionaryAccent) private var accent
    @Bindable var store: AppStore
    let recipe: Recipe
    let cook: () -> Void
    @State private var portionInput: String?
    private var originalPortions: Decimal { recipe.servings ?? 1 }
    private var initialPortions: Decimal { store.kitchen.adventures.first { $0.id == recipe.id }?.portions ?? originalPortions }
    private var selectedPortions: Decimal? {
        guard let portionInput else { return initialPortions }
        return try? Numbers.parse(portionInput)
    }
    private var multiplier: Decimal { (selectedPortions ?? initialPortions) / originalPortions }

    var body: some View {
        List {
            Section {
                Text(recipe.name).font(.title2.bold())
                if let servings = recipe.servings { LabeledContent("Original recipe serves", value: Numbers.display(servings, locale: L10n.locale)) }
                if let minutes = recipe.totalTimeMin { LabeledContent("Total minutes", value: String(minutes)) }
                let tags = RecipeBrowsing.tagNames(recipe.tags)
                Text(tags.isEmpty ? L10n.text("No tags") : tags.joined(separator: " · ")).foregroundStyle(.secondary)
                portionControls
                Button {
                    guard selectedPortions != nil else { return }
                    if store.visit(recipe, portions: portionInput == nil ? nil : selectedPortions) {
                        portionInput = nil
                        cook()
                    }
                } label: {
                    Label(store.kitchen.adventures.contains(where: { $0.id == recipe.id }) ? "Resume cooking" : "Cook this recipe", systemImage: "flame.fill")
                        .labelStyle(.titleAndIcon)
                        .font(.headline)
                        .foregroundStyle(Color(uiColor: .systemBackground))
                        .frame(maxWidth: .infinity, minHeight: 36)
                }
                .buttonStyle(.borderedProminent)
                .tint(accent)
                .disabled(selectedPortions == nil)
                .accessibilityIdentifier("preview-cook")
            }
            if let tools = recipe.equipment, !tools.isEmpty {
                Section("Equipment") {
                    ForEach(tools, id: \.self) { Text($0) }
                }
            }
            Section("Ingredients") {
                ForEach(recipe.ingredients) { ingredient in
                    VStack(alignment: .leading) {
                        if let group = ingredient.groupName { Text(group).font(.caption).foregroundStyle(.secondary) }
                        Text(ingredient.name)
                        Text([ingredient.quantity.map { Numbers.display($0 * multiplier, locale: L10n.locale) },
                              ingredient.unit].compactMap { $0 }.joined(separator: " ")).foregroundStyle(.secondary)
                    }
                }
            }
            Section("Steps") {
                ForEach(recipe.instructionSteps.sorted { $0.stepNumber < $1.stepNumber }) { step in
                    VStack(alignment: .leading) {
                        if let group = step.groupName { Text(group).font(.caption).foregroundStyle(.secondary) }
                        Text(IngredientPlaceholders.resolve(step.description, ingredients: recipe.ingredients, multiplier: multiplier, locale: L10n.locale))
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

    private var portionControls: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Cooking for").font(.caption).foregroundStyle(.secondary)
            HStack(spacing: 12) {
                portionButton("One fewer portion", icon: "minus", id: "preview-portion-minus", change: -1)
                    .disabled((selectedPortions ?? initialPortions) <= 1)
                TextField("Cooking for", text: Binding(
                    get: { portionInput ?? Numbers.display(initialPortions, locale: L10n.locale) },
                    set: { portionInput = $0 }
                ))
                .keyboardType(.decimalPad)
                .multilineTextAlignment(.center)
                .monospacedDigit()
                .textFieldStyle(.roundedBorder)
                .accessibilityIdentifier("preview-portion-count")
                portionButton("One more portion", icon: "plus", id: "preview-portion-plus", change: 1)
                    .disabled((selectedPortions ?? initialPortions) >= 1_000_000_000)
            }
            if selectedPortions == nil {
                Text("Enter a positive number, such as 1.53 or 4.32.").font(.caption).foregroundStyle(.red)
            }
        }.sensoryFeedback(.selection, trigger: selectedPortions)
    }

    private func portionButton(_ title: LocalizedStringKey, icon: String, id: String, change: Decimal) -> some View {
        Button {
            portionInput = Numbers.text(min((selectedPortions ?? initialPortions) + change, 1_000_000_000))
        } label: {
            Label(title, systemImage: icon).labelStyle(.iconOnly).frame(minWidth: 44, minHeight: 44)
        }.buttonStyle(.borderless).accessibilityIdentifier(id)
    }
}
