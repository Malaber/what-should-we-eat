import Foundation

public enum FoodIcons {
    public static func emoji(_ input: String) -> String? {
        let value = input.trimmingCharacters(in: .whitespacesAndNewlines)
        guard value.count == 1, value.unicodeScalars.count <= 32,
              let first = value.unicodeScalars.first, first.properties.isEmoji,
              !value.unicodeScalars.contains("\u{FE0E}") else { return nil }

        let keycapBase = first == "#" || first == "*" || (48...57).contains(first.value)
        if keycapBase { return value.unicodeScalars.last == "\u{20E3}" ? value : nil }
        // Single regional indicators are rendered as letters rather than flags.
        if (0x1F1E6...0x1F1FF).contains(first.value) {
            return value.unicodeScalars.count == 2 && value.unicodeScalars.allSatisfy {
                (0x1F1E6...0x1F1FF).contains($0.value)
            } ? value : nil
        }
        return value
    }

    public static func display(_ icon: String?) -> String { icon.flatMap(emoji) ?? "🍽️" }
}
