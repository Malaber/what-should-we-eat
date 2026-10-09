import Foundation

public struct KitchenWidgetSnapshot: Codable, Equatable, Sendable {
    public struct Meal: Codable, Equatable, Sendable, Identifiable {
        public let id: Int
        public let name: String
        public let cooked: Bool
        public init(id: Int, name: String, cooked: Bool) {
            self.id = id; self.name = String(name.prefix(120)); self.cooked = cooked
        }
    }
    public let scope: String
    public let updated: Date
    public let expires: Date
    public let meals: [Meal]
    public let language: String
    public init(scope: String, meals: [Meal], language: String = "system", now: Date = Date(), calendar: Calendar = .current) {
        self.scope = scope; self.meals = Array(meals.prefix(50)); self.updated = now; self.language = language
        // Monday boundaries are stable regardless of the locale's first weekday.
        var week = calendar; week.firstWeekday = 2; week.minimumDaysInFirstWeek = 4
        expires = week.dateInterval(of: .weekOfYear, for: now)?.end ?? now.addingTimeInterval(7 * 86400)
    }
    public func isCurrent(at date: Date) -> Bool { date >= updated && date < expires }
    public func link(recipeID: Int? = nil) -> URL {
        var components = URLComponents()
        components.scheme = "de.malaber.onionary"; components.host = "kitchen"
        components.queryItems = [URLQueryItem(name: "scope", value: scope)]
        if let recipeID { components.queryItems?.append(URLQueryItem(name: "recipe", value: String(recipeID))) }
        return components.url!
    }
}

public enum KitchenDeepLink {
    public enum Destination: Equatable { case kitchen, recipe(Int), cooking }
    public static func destination(_ url: URL, scope: String) -> Destination? {
        guard !scope.isEmpty, url.scheme == "de.malaber.onionary", url.path.isEmpty,
              let parts = URLComponents(url: url, resolvingAgainstBaseURL: false),
              parts.queryItems?.filter({ $0.name == "scope" }).count == 1,
              parts.queryItems?.first(where: { $0.name == "scope" })?.value == scope else { return nil }
        if url.host == "cooking" { return .cooking }
        guard url.host == "kitchen" else { return nil }
        if let recipe = parts.queryItems?.first(where: { $0.name == "recipe" })?.value {
            guard let id = Int(recipe), id > 0 else { return nil }
            return .recipe(id)
        }
        return .kitchen
    }
}
