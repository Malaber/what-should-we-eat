import Foundation

public enum ExternalRecipePage {
    public static let maximumSourceLength = 12_000

    /// Prefer the source's Recipe schema over navigation and unrelated page text.
    public static func recipeText(from html: String) throws -> String {
        let scripts = try! NSRegularExpression(
            pattern: #"<script\b[^>]*\btype\s*=\s*["']application/ld\+json["'][^>]*>(.*?)</script\s*>"#,
            options: [.caseInsensitive, .dotMatchesLineSeparators]
        )
        for match in scripts.matches(in: html, range: NSRange(html.startIndex..., in: html)) {
            guard let range = Range(match.range(at: 1), in: html),
                  let payload = try? JSONSerialization.jsonObject(with: Data(html[range].utf8)),
                  let recipe = findRecipe(payload) else { continue }
            let fields = recipe.filter { ["name", "recipeYield", "recipeIngredient", "recipeInstructions",
                                           "prepTime", "cookTime", "totalTime"].contains($0.key) }
            let data = try JSONSerialization.data(withJSONObject: fields, options: [.sortedKeys, .withoutEscapingSlashes])
            return try bounded(String(decoding: data, as: UTF8.self))
        }

        let cleaned = html
            .replacingOccurrences(of: #"(?is)<!--.*?-->|<(script|style|head|nav|footer|aside|svg)\b[^>]*>.*?</\1\s*>"#,
                                  with: " ", options: .regularExpression)
            .replacingOccurrences(of: #"(?i)</?(?:p|li|h[1-6]|br|section|article)\b[^>]*>"#, with: "\n", options: .regularExpression)
            .replacingOccurrences(of: #"<[^>]+>"#, with: " ", options: .regularExpression)
        let text = decodeEntities(cleaned).split(separator: "\n")
            .map { $0.split(whereSeparator: \.isWhitespace).joined(separator: " ") }
            .filter { !$0.isEmpty }.joined(separator: "\n")
        return try bounded(text)
    }

    private static func findRecipe(_ value: Any) -> [String: Any]? {
        if let values = value as? [Any] {
            return values.lazy.compactMap(findRecipe).first
        }
        guard let object = value as? [String: Any] else { return nil }
        let type = object["@type"]
        let types = type as? [String] ?? (type as? String).map { [$0] } ?? []
        if types.contains(where: { $0 == "Recipe" || $0 == "https://schema.org/Recipe" }) { return object }
        for key in ["@graph", "mainEntity", "itemListElement"] {
            if let child = object[key], let recipe = findRecipe(child) { return recipe }
        }
        return nil
    }

    private static func bounded(_ source: String) throws -> String {
        guard !source.isEmpty, source.count <= maximumSourceLength else {
            throw CookingError.response("Could not read this recipe page. Paste the recipe text instead.")
        }
        return source
    }

    private static func decodeEntities(_ source: String) -> String {
        let entities = ["amp": "&", "lt": "<", "gt": ">", "quot": "\"",
                        "apos": "'", "nbsp": " ", "auml": "ä", "ouml": "ö", "uuml": "ü",
                        "Auml": "Ä", "Ouml": "Ö", "Uuml": "Ü", "szlig": "ß",
                        "frac14": "¼", "frac12": "½", "frac34": "¾", "deg": "°"]
        let regex = try! NSRegularExpression(pattern: #"&(#x[0-9a-fA-F]+|#\d+|[A-Za-z][A-Za-z0-9]+);"#)
        var text = source
        for match in regex.matches(in: source, range: NSRange(source.startIndex..., in: source)).reversed() {
            guard let nameRange = Range(match.range(at: 1), in: source), let whole = Range(match.range, in: text) else { continue }
            let name = String(source[nameRange])
            if let replacement = entities[name] { text.replaceSubrange(whole, with: replacement) }
            else if name.hasPrefix("#") {
                let hexadecimal = name.hasPrefix("#x")
                if let code = UInt32(name.dropFirst(hexadecimal ? 2 : 1), radix: hexadecimal ? 16 : 10),
                   let character = UnicodeScalar(code) { text.replaceSubrange(whole, with: String(character)) }
            }
        }
        return text
    }
}
