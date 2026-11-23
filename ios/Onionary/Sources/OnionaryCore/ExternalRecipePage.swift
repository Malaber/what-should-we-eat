import Foundation

public enum ExternalRecipePage {
    public static let maximumSourceLength = 12_000
    private static let scripts = try! NSRegularExpression(
        pattern: #"<script\b[^>]*\btype\s*=\s*(?:"application/ld\+json"|'application/ld\+json'|application/ld\+json\b)[^>]*>(.*?)</script\s*>"#,
        options: [.caseInsensitive, .dotMatchesLineSeparators]
    )

    private static func recipes(in html: String) -> [[String: Any]] {
        var recipes: [[String: Any]] = []
        for match in scripts.matches(in: html, range: NSRange(html.startIndex..., in: html)) {
            guard let range = Range(match.range(at: 1), in: html),
                  let payload = try? JSONSerialization.jsonObject(with: Data(html[range].utf8)) else { continue }
            recipes.append(contentsOf: findRecipes(payload))
        }
        return recipes
    }

    /// Complete Schema.org Recipe data can be reviewed without a language model.
    public static func structuredDraft(from html: String) -> RecipeDraft? {
        for recipe in recipes(in: html) {
            guard let name = plainText(recipe["name"]), name.count <= 255,
                  let rawIngredients = recipe["recipeIngredient"] as? [Any], !rawIngredients.isEmpty,
                  let instructions = recipe["recipeInstructions"] else { continue }
            let ingredients = rawIngredients.compactMap { plainText($0).map(ingredient) }
            guard ingredients.count == rawIngredients.count, ingredients.allSatisfy({ $0.name.count <= 255 }),
                  let steps = steps(instructions), !steps.isEmpty else { continue }
            var draft = RecipeDraft()
            draft.name = name
            draft.servings = servings(recipe["recipeYield"])
            draft.activeCookingTimeMin = minutes(recipe["prepTime"])
            draft.totalTimeMin = minutes(recipe["totalTime"])
            draft.ingredients = ingredients
            draft.instructionSteps = steps.enumerated().map { index, step in
                var numbered = step
                numbered.stepNumber = index + 1
                numbered.description = linkAmounts(in: step.description, using: ingredients)
                return numbered
            }
            return draft
        }
        return nil
    }

    /// Prefer the source's Recipe schema over navigation and unrelated page text.
    public static func recipeText(from html: String) throws -> String {
        if let recipe = recipes(in: html).first {
            let fields = recipe.filter { ["name", "recipeYield", "recipeIngredient", "recipeInstructions",
                                           "prepTime", "cookTime", "totalTime"].contains($0.key) }
            if let data = try? JSONSerialization.data(withJSONObject: fields, options: [.sortedKeys, .withoutEscapingSlashes]),
               let source = try? bounded(String(decoding: data, as: UTF8.self)) { return source }
        }

        let content = html.range(of: #"(?is)<main\b[^>]*>.*?</main\s*>"#, options: .regularExpression)
            .map { String(html[$0]) } ?? html
        let cleaned = content
            .replacingOccurrences(of: #"(?is)<!--.*?-->|<(script|style|head|nav|footer|aside|svg)\b[^>]*>.*?</\1\s*>"#,
                                  with: " ", options: .regularExpression)
            .replacingOccurrences(of: #"(?i)</?(?:p|li|h[1-6]|br|section|article)\b[^>]*>"#, with: "\n", options: .regularExpression)
            .replacingOccurrences(of: #"<[^>]+>"#, with: " ", options: .regularExpression)
        let text = decodeEntities(cleaned).split(separator: "\n")
            .map { $0.split(whereSeparator: \.isWhitespace).joined(separator: " ") }
            .filter { !$0.isEmpty }.joined(separator: "\n")
        return try bounded(text)
    }

    private static func findRecipes(_ value: Any, depth: Int = 0) -> [[String: Any]] {
        guard depth < 20 else { return [] }
        if let values = value as? [Any] {
            return values.flatMap { findRecipes($0, depth: depth + 1) }
        }
        guard let object = value as? [String: Any] else { return [] }
        if hasType(object, "Recipe") { return [object] }
        return ["@graph", "mainEntity", "itemListElement", "item"].compactMap { object[$0] }
            .flatMap { findRecipes($0, depth: depth + 1) }
    }

    private static func hasType(_ object: [String: Any], _ name: String) -> Bool {
        let type = object["@type"]
        let types = type as? [String] ?? (type as? String).map { [$0] } ?? []
        return types.contains { [$0, $0.replacingOccurrences(of: "https://schema.org/", with: "", options: .anchored),
                                 $0.replacingOccurrences(of: "http://schema.org/", with: "", options: .anchored)].contains(name) }
    }

    private static func plainText(_ value: Any?) -> String? {
        guard let source = value as? String else { return nil }
        let cleaned = decodeEntities(source.replacingOccurrences(of: #"<[^>]+>"#, with: " ", options: .regularExpression))
            .split(whereSeparator: \.isWhitespace).joined(separator: " ")
        return cleaned.isEmpty ? nil : cleaned
    }

    private static func steps(_ source: Any, group: String? = nil, depth: Int = 0) -> [RecipeDraft.Step]? {
        guard depth < 20 else { return nil }
        if let items = source as? [Any] {
            var result: [RecipeDraft.Step] = []
            for item in items {
                guard let children = steps(item, group: group, depth: depth + 1) else { return nil }
                result.append(contentsOf: children)
            }
            return result
        }
        if let item = source as? [String: Any], hasType(item, "HowToSection"), let children = item["itemListElement"] {
            let title = plainText(item["name"]).map { String($0.unicodeScalars.prefix(100)) }
            return steps(children, group: title ?? group, depth: depth + 1)
        }
        let item = source as? [String: Any]
        guard let description = plainText(item?["text"] ?? source) else { return nil }
        var step = RecipeDraft.Step()
        step.description = description
        step.durationMin = minutes(item?["performTime"])
        step.groupName = group
        return [step]
    }

    private static func minutes(_ value: Any?) -> Int? {
        guard let text = value as? String,
              let match = duration.firstMatch(in: text, range: NSRange(text.startIndex..., in: text)) else { return nil }
        let parts = (1...3).map { index in
            Range(match.range(at: index), in: text).flatMap { Int(text[$0]) } ?? 0
        }
        let total = parts[0] * 60 + parts[1] + (parts[2] + 59) / 60
        return total > 0 ? total : nil
    }

    private static let duration = try! NSRegularExpression(pattern: #"^PT(?:(\d{1,5})H)?(?:(\d{1,5})M)?(?:(\d{1,5})S)?$"#)

    private static func servings(_ value: Any?) -> Decimal? {
        if let number = value as? NSNumber, number.decimalValue > 0, number.decimalValue <= 1_000_000 { return number.decimalValue }
        if let values = value as? [Any] { return values.lazy.compactMap(servings).first }
        guard let text = plainText(value), let first = text.split(separator: " ").first,
              let count = try? Numbers.parse(String(first)), count > 0, count <= 1_000_000 else { return nil }
        return count
    }

    private static let quantity = try! NSRegularExpression(
        pattern: #"^(\d+\s+\d+[/⁄]\d+|\d*[¼½¾⅓⅔⅛⅜⅝⅞]|\d+[/⁄]\d+|\d+(?:[.,]\d+)?)\s*([\p{L}]+\.?\s+.*|[^\d\s].*)$"#
    )
    private static let fractions: [Character: String] = ["¼": "1/4", "½": "1/2", "¾": "3/4", "⅓": "1/3", "⅔": "2/3",
                                                          "⅛": "1/8", "⅜": "3/8", "⅝": "5/8", "⅞": "7/8"]
    private static let units: Set<String> = ["mg", "g", "kg", "ml", "cl", "dl", "l", "oz", "lb", "lbs", "tsp", "tbsp", "tl",
                                             "el", "gram", "grams", "gramm", "cup", "cups", "teaspoon", "teaspoons",
                                             "tablespoon", "tablespoons", "prise", "prisen", "pinch", "stück", "bund"]

    private static func ingredient(_ line: String) -> RecipeDraft.Item {
        var item = RecipeDraft.Item()
        item.name = line
        guard let match = quantity.firstMatch(in: line, range: NSRange(line.startIndex..., in: line)),
              let amount = Range(match.range(at: 1), in: line), let remaining = Range(match.range(at: 2), in: line) else { return item }
        let raw = line[amount]
        let spelling = raw.last.flatMap { fractions[$0] }.map { raw.dropLast() + " " + $0 } ?? String(raw)
        let tokens = spelling.replacingOccurrences(of: "⁄", with: "/").split(whereSeparator: \.isWhitespace)
        let values = tokens.compactMap { token -> Decimal? in
            let fraction = token.split(separator: "/", omittingEmptySubsequences: false)
            if fraction.count == 2, let numerator = try? Numbers.parse(String(fraction[0])),
               let denominator = try? Numbers.parse(String(fraction[1])) { return numerator / denominator }
            return try? Numbers.parse(String(token))
        }
        let amountValue = values.reduce(Decimal.zero, +)
        let tail = line[remaining].trimmingCharacters(in: .whitespaces)
        guard tokens.count == values.count, amountValue > 0, let first = tail.split(separator: " ").first,
              first.first?.isLetter == true, !["bis", "to", "or", "oder", "and", "und"].contains(first.lowercased()) else { return item }
        item.quantity = amountValue
        if units.contains(first.lowercased().trimmingCharacters(in: CharacterSet(charactersIn: "."))),
           tail.count > first.count {
            item.unit = String(first)
            item.name = tail.dropFirst(first.count).trimmingCharacters(in: .whitespaces)
        } else {
            item.name = tail
        }
        return item
    }

    private static func linkAmounts(in text: String, using ingredients: [RecipeDraft.Item]) -> String {
        // Match only explicit quantities with the same unit and a unique name.
        let names = Dictionary(grouping: ingredients, by: { $0.name.lowercased() })
        let matches = names.values.compactMap { items -> RecipeDraft.Item? in
            guard items.count == 1, let item = items.first, item.quantity != nil,
                  let unit = item.unit, units.contains(unit.lowercased()), !item.name.contains(where: { "{}|".contains($0) }),
                  !item.name.contains("::") else { return nil }
            return item
        }.sorted { $0.name.count > $1.name.count }
        var result = text
        for item in matches {
            guard let unit = item.unit, let original = item.quantity else { continue }
            let name = NSRegularExpression.escapedPattern(for: item.name)
            let escapedUnit = NSRegularExpression.escapedPattern(for: unit)
            let pattern = #"(?<![\p{L}\d.,/–-])(\d+(?:[.,]\d+)?)\s*"# + escapedUnit + #"\s+"# + name + #"(?![\p{L}\d])"#
            guard let regex = try? NSRegularExpression(pattern: pattern, options: .caseInsensitive) else { continue }
            for match in regex.matches(in: result, range: NSRange(result.startIndex..., in: result)).reversed() {
                guard let range = Range(match.range, in: result), let number = Range(match.range(at: 1), in: result),
                      let amount = try? Numbers.parse(String(result[number])), amount <= original else { continue }
                let percent = amount * 100 / original
                var exact = percent
                var rounded = Decimal.zero
                NSDecimalRound(&rounded, &exact, 4, .plain)
                guard rounded == percent else { continue }
                result.replaceSubrange(range, with: "{{\(item.name)|\(Numbers.text(percent))%}}")
            }
        }
        return result
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
