import Foundation

public struct CookingSnapshot: Codable, Hashable, Sendable {
    public let recipeID: Int
    public let title: String
    public let checked: Int
    public let total: Int
    public let nextStep: String
    public let portions: String
    public var complete: Bool { total > 0 && checked == total }

    public init(_ adventure: Adventure, locale: Locale = .current) {
        recipeID = adventure.id
        title = String(adventure.recipe.name.prefix(120))
        (checked, total) = adventure.checklistProgress
        let next = adventure.recipe.instructionSteps.sorted { $0.stepNumber < $1.stepNumber }
            .first { !adventure.checked.contains("step-\($0.id)") }
        nextStep = String(next.map { IngredientPlaceholders.resolve($0.description,
            ingredients: adventure.recipe.ingredients, multiplier: adventure.multiplier, locale: locale) }?.prefix(240) ?? "")
        portions = Numbers.display(adventure.portions, locale: locale)
    }
}
