import Foundation

public enum PantryMatching {
    public struct Supply: Equatable, Sendable {
        public let name: String
        public let quantity: Decimal?
        public let unit: String
    }
    public struct Match: Identifiable, Sendable {
        public let recipe: Recipe
        public let matched: [String]
        public let missing: [String]
        public let short: [String]
        public let unchecked: [String]
        public var id: Int { recipe.id }
    }
    private static func key(_ value: String) -> String {
        let text = value.trimmingCharacters(in: .whitespacesAndNewlines).folding(options: [.diacriticInsensitive, .caseInsensitive], locale: Locale(identifier: "en_US_POSIX"))
        return ["bananen": "banane", "bananas": "banana", "eier": "ei", "eggs": "egg", "tomaten": "tomate", "tomatoes": "tomato", "zwiebeln": "zwiebel", "onions": "onion"][text] ?? text
    }
    private static func unit(_ value: String?) -> String {
        let text = key(value ?? "")
        return ["stuck": "", "stueck": "", "pieces": "", "piece": "", "pcs": "", "gramm": "g", "grams": "g", "milliliter": "ml"][text] ?? text
    }
    /// One entry per line/semicolon; also accepts “3 Bananen und 2 Eier”.
    public static func parse(_ text: String) -> [Supply] {
        let separated = text.replacingOccurrences(of: #"\s+(?:und|and)\s+"#, with: ";", options: .regularExpression)
        return separated.components(separatedBy: CharacterSet(charactersIn: ";\n")).compactMap { line in
            var words = line.split(whereSeparator: \.isWhitespace).map(String.init)
            guard !words.isEmpty else { return nil }
            var quantity: Decimal?
            if let value = try? Numbers.parse(words[0]) { quantity = value; words.removeFirst() }
            var measure = ""
            if let first = words.first, ["g", "kg", "ml", "l", "stuck", "stueck", "pieces", "piece", "pcs", "gramm", "grams"].contains(key(first)) {
                measure = unit(words.removeFirst())
            }
            guard !words.isEmpty else { return nil }
            return Supply(name: words.joined(separator: " "), quantity: quantity, unit: measure)
        }
    }
    public static func matches(_ recipes: [Recipe], supplies: [Supply]) -> [Match] {
        recipes.map { recipe in
            var matched: [String] = [], missing: [String] = [], short: [String] = [], unchecked: [String] = []
            // Aggregate duplicate ingredient names: filling and dough may both use milk.
            let grouped = Dictionary(grouping: recipe.ingredients, by: { key($0.name) + "|" + unit($0.unit) })
            for ingredients in grouped.values {
                let ingredient = ingredients[0]
                let named = supplies.filter { key($0.name) == key(ingredient.name) }
                guard !named.isEmpty else { missing.append(ingredient.name); continue }
                matched.append(ingredient.name)
                let compatible = named.filter { $0.unit == unit(ingredient.unit) }
                guard !compatible.isEmpty, compatible.allSatisfy({ $0.quantity != nil }), ingredients.allSatisfy({ $0.quantity != nil }) else {
                    unchecked.append(ingredient.name); continue
                }
                let available = compatible.reduce(Decimal.zero) { $0 + ($1.quantity ?? 0) }
                let required = ingredients.reduce(Decimal.zero) { $0 + ($1.quantity ?? 0) }
                if available < required { short.append(ingredient.name) }
            }
            return Match(recipe: recipe, matched: matched.sorted(), missing: missing.sorted(), short: short.sorted(), unchecked: unchecked.sorted())
        }.filter { !$0.matched.isEmpty }.sorted {
            if $0.missing.count != $1.missing.count { return $0.missing.count < $1.missing.count }
            if $0.short.count != $1.short.count { return $0.short.count < $1.short.count }
            return $0.recipe.id < $1.recipe.id
        }
    }
}
