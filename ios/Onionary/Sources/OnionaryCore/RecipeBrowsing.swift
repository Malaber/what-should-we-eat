import Foundation

public struct RecipeTag: Codable, Equatable, Sendable, Identifiable {
    public let id: Int
    public let name: String
}

public enum RecipeBrowsing {
    public static func categories(_ recipes: [Recipe], query: String = "") -> [String] {
        let names = recipes.flatMap { ($0.tags ?? []).map(\.name) }
        return Array(Set(names)).filter { query.isEmpty || $0.localizedStandardContains(query) }
            .sorted { $0.localizedStandardCompare($1) == .orderedAscending }
    }

    public static func recipes(_ recipes: [Recipe], query: String = "", category: String? = nil, quickestFirst: Bool = false) -> [Recipe] {
        let terms = query.split(whereSeparator: \.isWhitespace).map(String.init)
        return recipes.filter { recipe in
            let tags = (recipe.tags ?? []).map(\.name)
            guard category == nil || tags.contains(category!) else { return false }
            let searchable = ([recipe.name] + tags + recipe.ingredients.map(\.name)).joined(separator: " ")
            return terms.allSatisfy { searchable.localizedStandardContains($0) }
        }.sorted { lhs, rhs in
            if quickestFirst && lhs.totalTimeMin != rhs.totalTimeMin {
                return (lhs.totalTimeMin ?? Int.max) < (rhs.totalTimeMin ?? Int.max)
            }
            let order = lhs.name.localizedStandardCompare(rhs.name)
            return order == .orderedSame ? lhs.id < rhs.id : order == .orderedAscending
        }
    }
}
