import Foundation

public struct RecipeTag: Codable, Equatable, Sendable, Identifiable {
    public let id: Int
    public let name: String
}

public enum RecipeBrowsing {
    public enum Sort: String, CaseIterable, Identifiable, Sendable {
        case alphabetical, newest, ingredients, quickest
        public var id: Self { self }
        public var title: String {
            switch self {
            case .alphabetical: "Alphabetical"
            case .newest: "Last added"
            case .ingredients: "Ingredient count"
            case .quickest: "Quickest first"
            }
        }
    }

    public static func categories(_ recipes: [Recipe], query: String = "") -> [String] {
        let names = recipes.flatMap { ($0.tags ?? []).map(\.name) }
        return Array(Set(names)).filter { query.isEmpty || $0.localizedStandardContains(query) }
            .sorted { $0.localizedStandardCompare($1) == .orderedAscending }
    }

    public static func recipes(_ recipes: [Recipe], query: String = "", category: String? = nil,
                               categories: Set<String> = [], sort: Sort = .alphabetical, reversed: Bool = false) -> [Recipe] {
        let terms = query.split(whereSeparator: \.isWhitespace).map(String.init)
        let filtered = recipes.filter { recipe in
            let tags = (recipe.tags ?? []).map(\.name)
            guard category == nil || tags.contains(category!) else { return false }
            guard categories.allSatisfy({ selected in tags.contains { $0.localizedCaseInsensitiveCompare(selected) == .orderedSame } }) else { return false }
            let searchable = ([recipe.name] + tags + recipe.ingredients.map(\.name)).joined(separator: " ")
            return terms.allSatisfy { searchable.localizedStandardContains($0) }
        }
        var creationDates: [Int: Date] = [:]
        if sort == .newest {
            for recipe in filtered {
                guard let timestamp = recipe.createdAt else { continue }
                creationDates[recipe.id] = (try? Date(timestamp, strategy: .iso8601(includingFractionalSeconds: true)))
                    ?? (try? Date(timestamp, strategy: .iso8601))
            }
        }
        let ordered = filtered.sorted { lhs, rhs in
            switch sort {
            case .newest:
                let first = creationDates[lhs.id] ?? .distantPast
                let second = creationDates[rhs.id] ?? .distantPast
                return first == second ? lhs.id > rhs.id : first > second
            case .ingredients:
                if lhs.ingredients.count != rhs.ingredients.count { return lhs.ingredients.count < rhs.ingredients.count }
            case .quickest:
                let first = lhs.totalTimeMin ?? Int.max
                let second = rhs.totalTimeMin ?? Int.max
                if first != second { return first < second }
            case .alphabetical:
                break
            }
            let order = lhs.name.localizedStandardCompare(rhs.name)
            return order == .orderedSame ? lhs.id < rhs.id : order == .orderedAscending
        }
        return reversed ? Array(ordered.reversed()) : ordered
    }
}
