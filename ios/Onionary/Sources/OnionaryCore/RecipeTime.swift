import Foundation

/// Portable time references, independent of ingredients and portion scaling.
public struct RecipeTime: Equatable, Sendable {
    public static let maximumSeconds = 24 * 60 * 60
    public let seconds: Int

    public init?(seconds: Int) {
        guard (1...Self.maximumSeconds).contains(seconds) else { return nil }
        self.seconds = seconds
    }

    private static let units = try! NSRegularExpression(pattern: #"^(?:(\d{1,3})h)?(?:(\d{1,4})m)?(?:(\d{1,5})s)?$"#)

    public init?(_ value: String) {
        let range = NSRange(value.startIndex..., in: value)
        guard let match = Self.units.firstMatch(in: value, range: range), match.range == range else { return nil }
        let values = (1...3).map { index in
            Range(match.range(at: index), in: value).flatMap { Int(value[$0]) } ?? 0
        }
        self.init(seconds: values[0] * 3600 + values[1] * 60 + values[2])
    }

    public static func stepMinutes(_ value: Int?) -> RecipeTime? {
        guard let value, (1...maximumSeconds / 60).contains(value) else { return nil }
        return RecipeTime(seconds: value * 60)
    }

    public var placeholder: String { "{{time|\(seconds)s}}" }

    public func label(locale: Locale) -> String {
        let formatter = DateComponentsFormatter()
        var calendar = Calendar(identifier: .gregorian)
        calendar.locale = locale
        formatter.calendar = calendar
        formatter.allowedUnits = [.hour, .minute, .second]
        formatter.unitsStyle = .short
        formatter.zeroFormattingBehavior = .dropAll
        return formatter.string(from: TimeInterval(seconds)) ?? "\(seconds) s"
    }
}

public struct RecipeCountdown: Codable, Equatable, Identifiable, Sendable {
    public let id: String
    public let title: String
    public let deadline: Date

    public func remaining(at date: Date) -> Int {
        Int(max(0, min(Double(RecipeTime.maximumSeconds), deadline.timeIntervalSince(date).rounded(.up))))
    }
}
