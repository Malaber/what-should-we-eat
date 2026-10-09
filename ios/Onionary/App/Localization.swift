import Foundation

/// For composed strings outside SwiftUI's LocalizedStringKey interpolation.
enum L10n {
    static var locale: Locale {
        let choice = UserDefaults.standard.string(forKey: "language") ?? "system"
        return choice == "system" ? .current : Locale(identifier: choice)
    }
    static func text(_ key: String) -> String {
        let code = locale.language.languageCode?.identifier == "de" ? "de" : "en"
        guard let path = Bundle.main.path(forResource: code, ofType: "lproj"), let bundle = Bundle(path: path) else { return key }
        return bundle.localizedString(forKey: key, value: key, table: nil)
    }
    static func format(_ key: String, _ count: Int) -> String { String(format: text(key), locale: locale, count) }
}
