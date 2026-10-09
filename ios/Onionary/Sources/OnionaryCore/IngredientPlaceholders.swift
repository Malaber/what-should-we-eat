import Foundation

/// Portable text syntax survives recipe copies and imports without relying on database IDs.
/// Ambiguous/missing ingredients and malformed tokens stay visible for correction.
public enum IngredientPlaceholders {
    public static func resolve(_ text: String, ingredients: [Ingredient], multiplier: Decimal = 1, locale: Locale = .current) -> String {
        guard !multiplier.isNaN, multiplier > 0,
              let regex = try? NSRegularExpression(pattern: #"\{\{([^{}|]+)\|(\d+(?:[.,]\d+)?)%\}\}"#) else { return text }
        var result = text
        for match in regex.matches(in: text, range: NSRange(text.startIndex..., in: text)).reversed() {
            guard let whole = Range(match.range, in: result),
                  let nameRange = Range(match.range(at: 1), in: text),
                  let percentRange = Range(match.range(at: 2), in: text),
                  let percent = Decimal(string: String(text[percentRange]).replacingOccurrences(of: ",", with: ".")),
                  percent >= 0, percent <= 100 else { continue }
            let name = text[nameRange].trimmingCharacters(in: .whitespacesAndNewlines)
            let matches = ingredients.filter { $0.name.caseInsensitiveCompare(name) == .orderedSame }
            guard matches.count == 1, let ingredient = matches.first,
                  let quantity = ingredient.quantity, !quantity.isNaN, quantity > 0 else { continue }
            let value = quantity * multiplier * percent / 100
            guard !value.isNaN else { continue }
            let replacement = [Numbers.display(value, locale: locale), ingredient.unit ?? "", ingredient.name]
                .filter { !$0.isEmpty }.joined(separator: " ")
            result.replaceSubrange(whole, with: replacement)
        }
        return result
    }
}
