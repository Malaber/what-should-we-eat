import Foundation

public enum RecipeImportLink {
    public static func sharedRecipe(_ text: String) throws -> URL {
        guard let url = URL(string: text.trimmingCharacters(in: .whitespacesAndNewlines)),
              url.scheme == "https", url.host != nil, url.user == nil, url.password == nil,
              url.port == nil || url.port == 443, url.path == "/share.html", url.query == nil,
              let token = url.fragment, token.range(of: #"^[A-Za-z0-9_-]{43}$"#, options: .regularExpression) != nil else {
            throw CookingError.response("Enter a valid Onionary recipe-copy link.")
        }
        return url
    }
    public static func sharedText(_ text: String) throws -> URL {
        if let url = try? accepted(text) { return url }
        let detector = try NSDataDetector(types: NSTextCheckingResult.CheckingType.link.rawValue)
        for match in detector.matches(in: text, range: NSRange(text.startIndex..., in: text)) {
            if let url = match.url, let accepted = try? accepted(url.absoluteString) { return accepted }
        }
        throw CookingError.response("No supported recipe link found.")
    }
    public static func accepted(_ text: String) throws -> URL {
        if let url = try? chefkoch(text) { return url }
        return try sharedRecipe(text)
    }
    public static func chefkoch(_ text: String) throws -> URL {
        guard let url = URL(string: text.trimmingCharacters(in: .whitespacesAndNewlines)),
              url.scheme == "https", let host = url.host?.lowercased(),
              host == "chefkoch.de" || host.hasSuffix(".chefkoch.de"),
              url.user == nil, url.password == nil, url.port == nil else {
            throw CookingError.response("Share an HTTPS Chefkoch recipe link.")
        }
        return url
    }
}

public struct RecipeDraft: Codable, Sendable {
    public struct Item: Codable, Identifiable, Sendable {
        public var id: UUID = UUID()
        public var name = ""
        public var quantity: Decimal?
        public var unit: String? = ""
        enum CodingKeys: String, CodingKey { case name, quantity, unit }
        public init() {}
    }
    public struct Step: Codable, Identifiable, Sendable {
        public var id: UUID = UUID()
        public var stepNumber = 1
        public var description = ""
        public var durationMin: Int?
        enum CodingKeys: String, CodingKey { case stepNumber, description, durationMin }
        public init() {}
    }
    public var name = ""
    public var notes: String? = ""
    public var servings: Decimal? = 1
    public var kcalPerServing: Decimal?
    public var activeCookingTimeMin: Int?
    public var totalTimeMin: Int?
    public var ingredients: [Item] = []
    public var instructionSteps: [Step] = []
    public var tags: [String] = []
    public init() {}
    public static func fromRecipeResponse(_ data: Data) throws -> RecipeDraft {
        guard var json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else { throw CookingError.response("Invalid recipe response.") }
        let tags = json["tags"] as? [[String: Any]] ?? []
        json["tags"] = tags.compactMap { $0["name"] as? String }
        let decoder = JSONDecoder(); decoder.keyDecodingStrategy = .convertFromSnakeCase
        return try decoder.decode(RecipeDraft.self, from: JSONSerialization.data(withJSONObject: json))
    }
    public func validatedData() throws -> Data {
        guard !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
              ingredients.allSatisfy({ !$0.name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && ($0.quantity == nil || $0.quantity! > 0) }),
              instructionSteps.allSatisfy({ !$0.description.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && ($0.durationMin ?? 0) >= 0 }),
              (totalTimeMin ?? 0) >= 0, (activeCookingTimeMin ?? 0) >= 0,
              (servings ?? 1) > 0, (servings ?? 1) <= 1_000_000,
              (kcalPerServing ?? 0) >= 0 else { throw CookingError.response("Check recipe name, ingredients, steps, and positive quantities.") }
        var copy = self
        for index in copy.instructionSteps.indices { copy.instructionSteps[index].stepNumber = index + 1 }
        let encoder = JSONEncoder(); encoder.keyEncodingStrategy = .convertToSnakeCase
        // PUT supports partial updates: explicitly encode cleared optional metadata.
        var payload = try JSONSerialization.jsonObject(with: encoder.encode(copy)) as! [String: Any]
        for key in ["notes", "kcal_per_serving", "active_cooking_time_min", "total_time_min"] where payload[key] == nil {
            payload[key] = NSNull()
        }
        return try JSONSerialization.data(withJSONObject: payload)
    }
}
