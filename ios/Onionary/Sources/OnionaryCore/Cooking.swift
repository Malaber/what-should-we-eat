import Foundation

public struct Ingredient: Codable, Identifiable, Equatable, Sendable {
    public let id: Int
    public let name: String
    public let quantity: Decimal?
    public let unit: String?
}

public struct CookingStep: Codable, Identifiable, Equatable, Sendable {
    public let id: Int
    public let stepNumber: Int
    public let description: String
    public let durationMin: Int?
}

public struct Recipe: Codable, Identifiable, Equatable, Sendable {
    public let id: Int
    public let householdId: Int
    public let name: String
    public let notes: String?
    public var tags: [RecipeTag]? = nil
    public var servings: Decimal? = nil
    public let totalTimeMin: Int?
    public let ingredients: [Ingredient]
    public let instructionSteps: [CookingStep]
}

public enum CookingError: LocalizedError {
    case invalidNumber, invalidServer, response(String)
    public var errorDescription: String? {
        switch self {
        case .invalidNumber: "Enter a positive number, such as 1.53 or 4.32."
        case .invalidServer: "Enter an HTTPS backend address without a path, password, or query."
        case .response(let message): message
        }
    }
}

public enum Numbers {
    /// Decimal arithmetic keeps user-entered ratios out of binary floating-point math.
    public static func parse(_ text: String) throws -> Decimal {
        let normalized = text.trimmingCharacters(in: .whitespacesAndNewlines).replacingOccurrences(of: ",", with: ".")
        guard normalized.range(of: #"^\d+(\.\d+)?$"#, options: .regularExpression) != nil,
              let value = Decimal(string: normalized, locale: Locale(identifier: "en_US_POSIX")),
              !value.isNaN, value > 0, value <= Decimal(1_000_000_000) else { throw CookingError.invalidNumber }
        return value
    }
    /// Presentation only. Calculations and persisted values keep full Decimal precision.
    public static func display(_ value: Decimal, locale: Locale = .current) -> String {
        let formatter = NumberFormatter()
        formatter.locale = locale
        formatter.numberStyle = .decimal
        formatter.maximumFractionDigits = 2
        formatter.minimumFractionDigits = 0
        formatter.usesGroupingSeparator = false
        return formatter.string(from: NSDecimalNumber(decimal: value)) ?? "–"
    }
    public static func text(_ value: Decimal) -> String { NSDecimalNumber(decimal: value).stringValue }
}

public struct CheckChange: Codable, Identifiable, Equatable, Sendable {
    public let id: UUID
    public let timestamp: Date
    public let key: String
    public let label: String
    public let wasChecked: Bool
    public let isChecked: Bool
    public let undoes: UUID?
    public var redoes: UUID? = nil
}

public struct Adventure: Codable, Identifiable, Equatable, Sendable {
    public var id: Int { recipe.id }
    public let recipe: Recipe
    public private(set) var multiplier: Decimal = 1
    public private(set) var baseServings: Decimal = 1
    public private(set) var checked: Set<String> = []
    public private(set) var history: [CheckChange] = []
    private var undoStack: [UUID] = []
    private var redoStack: [UUID]? = nil
    public var lastVisited: Date
    public var canUndo: Bool { !undoStack.isEmpty }
    public var canRedo: Bool { redoStack?.isEmpty == false }
    public var portions: Decimal { baseServings * multiplier }

    public init(recipe: Recipe, now: Date = Date()) { self.recipe = recipe; baseServings = recipe.servings ?? 1; lastVisited = now }
    public func quantity(_ ingredient: Ingredient) -> Decimal? { ingredient.quantity.map { $0 * multiplier } }
    public mutating func scale(multiplier: Decimal) throws {
        guard !multiplier.isNaN, multiplier > 0, multiplier <= 1_000_000_000 else { throw CookingError.invalidNumber }
        self.multiplier = multiplier
    }
    public mutating func scale(baseServings: Decimal, portions: Decimal) throws {
        guard !baseServings.isNaN, !portions.isNaN, baseServings > 0, portions > 0,
              baseServings <= 1_000_000_000, portions <= 1_000_000_000 else { throw CookingError.invalidNumber }
        try scale(multiplier: portions / baseServings)
        self.baseServings = baseServings
    }
    public mutating func scale(ingredient: Ingredient, available: Decimal) throws {
        guard let original = ingredient.quantity, original > 0, !available.isNaN, available > 0 else { throw CookingError.invalidNumber }
        try scale(multiplier: available / original)
    }
    public mutating func toggle(key: String, label: String, now: Date = Date()) {
        let previous = checked.contains(key)
        let change = CheckChange(id: UUID(), timestamp: now, key: key, label: label,
                                 wasChecked: previous, isChecked: !previous, undoes: nil)
        set(key, checked: !previous)
        history.append(change)
        undoStack.append(change.id)
        redoStack = []
    }
    /// Undo itself is recorded, so accidental checks AND unchecks remain inspectable.
    public mutating func undo(now: Date = Date()) {
        guard let id = undoStack.popLast(), let original = history.first(where: { $0.id == id }) else { return }
        let previous = checked.contains(original.key)
        redoStack = (redoStack ?? []) + [id]
        set(original.key, checked: original.wasChecked)
        history.append(CheckChange(id: UUID(), timestamp: now, key: original.key, label: original.label,
                                   wasChecked: previous, isChecked: original.wasChecked, undoes: id))
    }
    public mutating func redo(now: Date = Date()) {
        guard let id = redoStack?.popLast(), let original = history.first(where: { $0.id == id }) else { return }
        let previous = checked.contains(original.key)
        set(original.key, checked: original.isChecked)
        undoStack.append(id)
        history.append(CheckChange(id: UUID(), timestamp: now, key: original.key, label: original.label,
                                   wasChecked: previous, isChecked: original.isChecked, undoes: nil, redoes: id))
    }
    private mutating func set(_ key: String, checked value: Bool) {
        if value { checked.insert(key) } else { checked.remove(key) }
    }
}

public struct Kitchen: Codable, Equatable, Sendable {
    public var recipes: [Recipe] = []
    public var adventures: [Adventure] = []
    public var currentID: Int?
    public init() {}
    public mutating func visit(_ recipe: Recipe, now: Date = Date()) {
        if let index = adventures.firstIndex(where: { $0.id == recipe.id }) {
            adventures[index].lastVisited = now
        } else { adventures.append(Adventure(recipe: recipe, now: now)) }
        currentID = recipe.id
    }
    public var recent: [Adventure] { adventures.sorted { $0.lastVisited > $1.lastVisited } }
}

public enum Backend {
    public static func url(_ text: String) throws -> URL {
        guard var parts = URLComponents(string: text.trimmingCharacters(in: .whitespacesAndNewlines)),
              parts.scheme?.lowercased() == "https", let host = parts.host, !host.isEmpty,
              parts.user == nil, parts.password == nil, parts.query == nil, parts.fragment == nil,
              parts.path == "" || parts.path == "/" else { throw CookingError.invalidServer }
        parts.scheme = "https"; parts.host = host.lowercased(); parts.path = ""
        guard let url = parts.url else { throw CookingError.invalidServer }
        return url
    }
}

public enum KitchenFile {
    public static func read(_ url: URL) throws -> Kitchen {
        guard FileManager.default.fileExists(atPath: url.path) else { return Kitchen() }
        return try JSONDecoder().decode(Kitchen.self, from: Data(contentsOf: url))
    }
    public static func write(_ kitchen: Kitchen, to url: URL) throws {
        try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
        try JSONEncoder().encode(kitchen).write(to: url, options: .atomic)
    }
}
