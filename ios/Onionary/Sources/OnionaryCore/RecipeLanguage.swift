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
