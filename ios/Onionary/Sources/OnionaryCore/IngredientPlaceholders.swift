import Foundation

/// Portable text syntax survives recipe copies and imports without relying on database IDs.
/// Ambiguous/missing ingredients and malformed tokens stay visible for correction.
public enum IngredientPlaceholders {
    public enum Part: Equatable, Sendable {
        case text(String)
        case amount(Ingredient, label: String)

        public var text: String {
            switch self {
            case .text(let text), .amount(_, let text): text
            }
        }
    }

    private static let token = try! NSRegularExpression(pattern: #"\{\{([^{}|]+)\|(\d+(?:[.,]\d+)?)%\}\}"#)

    public static func key(name: String, group: String?) -> String {
        group.map { $0 + "::" + name } ?? name
    }

    public static func parts(_ text: String, ingredients: [Ingredient], multiplier: Decimal = 1, locale: Locale = .current) -> [Part] {
        guard !multiplier.isNaN, multiplier > 0 else { return [.text(text)] }
        var result: [Part] = []
        var cursor = text.startIndex
        for match in token.matches(in: text, range: NSRange(text.startIndex..., in: text)) {
            guard let whole = Range(match.range, in: text),
                  let nameRange = Range(match.range(at: 1), in: text),
                  let percentRange = Range(match.range(at: 2), in: text),
                  let percent = Decimal(string: String(text[percentRange]).replacingOccurrences(of: ",", with: "."),
                                        locale: Locale(identifier: "en_US_POSIX")),
                  percent >= 0, percent <= 100 else { continue }
            let name = text[nameRange].trimmingCharacters(in: .whitespacesAndNewlines)
            let exact = ingredients.filter { $0.name.caseInsensitiveCompare(name) == .orderedSame }
            let matches = exact.isEmpty ? ingredients.filter {
                $0.groupName != nil && key(name: $0.name, group: $0.groupName).caseInsensitiveCompare(name) == .orderedSame
            } : exact
            guard matches.count == 1, let ingredient = matches.first,
                  let quantity = ingredient.quantity, !quantity.isNaN, quantity > 0 else { continue }
            let value = quantity * multiplier * percent / 100
            guard !value.isNaN else { continue }
            let replacement = [Numbers.display(value, locale: locale), ingredient.unit ?? "", ingredient.name]
                .filter { !$0.isEmpty }.joined(separator: " ")
            if cursor != whole.lowerBound { result.append(.text(String(text[cursor..<whole.lowerBound]))) }
            result.append(.amount(ingredient, label: replacement))
            cursor = whole.upperBound
        }
        if cursor != text.endIndex || result.isEmpty { result.append(.text(String(text[cursor...]))) }
        return result
    }

    public static func resolve(_ text: String, ingredients: [Ingredient], multiplier: Decimal = 1, locale: Locale = .current) -> String {
        parts(text, ingredients: ingredients, multiplier: multiplier, locale: locale).map(\.text).joined()
    }
}
