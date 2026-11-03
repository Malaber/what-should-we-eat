import Foundation

public enum RecipeLanguage: String, CaseIterable, Identifiable, Sendable {
    case automatic, german, english, french, spanish, italian
    public var id: String { rawValue }
    public var title: String {
        switch self {
        case .automatic: "Detect input language"
        case .german: "Deutsch"
        case .english: "English"
        case .french: "Français"
        case .spanish: "Español"
        case .italian: "Italiano"
        }
    }
    public var instruction: String {
        self == .automatic
            ? "Detect the language of the user's recipe text. Keep ALL recipe names, ingredients, units and instructions in that same language. German input must remain German. Do not translate to the device or system language."
            : "Write ALL recipe names, ingredients, units and instructions in \(title), regardless of input or device language."
    }
}

public enum RecipeAIMode: String, CaseIterable, Identifiable, Sendable {
    case format, generate
    public var id: String { rawValue }
    public var title: String { self == .format ? "Format existing recipe" : "Create a recipe" }
    public var instruction: String {
        switch self {
        case .format:
            "Only structure the supplied recipe. Preserve ingredient names, quantities, units, servings, step order and all cooking details as closely as possible. Do not invent, substitute, optimize, omit or add ingredients or instructions. Leave missing numeric quantities and servings null, and missing units empty. Keep original wording unless formatting requires a minimal change. Follow the selected output-language instruction; only translate if explicitly requested."
        case .generate:
            "Create a practical complete recipe from the user's ideas. You may invent ingredients and cooking steps where unspecified, but respect every supplied ingredient, quantity, portion count and constraint. Never claim allergy safety."
        }
    }
}
