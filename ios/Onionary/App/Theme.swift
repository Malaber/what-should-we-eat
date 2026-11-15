import SwiftUI
import UIKit

enum OnionaryTheme {
    static let background = Color(uiColor: UIColor { traits in
        traits.userInterfaceStyle == .dark
            ? UIColor(red: 0.13, green: 0.106, blue: 0.125, alpha: 1)
            : UIColor(red: 0.984, green: 0.961, blue: 0.914, alpha: 1)
    })
    static let accents = ["Onion", "Herb", "Blueberry", "Paprika", "Lemon", "Eggplant", "Beetroot"]
    static func name(_ stored: String) -> String { stored == "Ocean" ? "Blueberry" : stored }
    static func color(_ name: String) -> Color { Color(uiColor: UIColor { traits in
        let dark = traits.userInterfaceStyle == .dark
        switch name {
        case "Herb": return dark ? UIColor(red: 0.62, green: 0.85, blue: 0.65, alpha: 1) : UIColor(red: 0.15, green: 0.39, blue: 0.22, alpha: 1)
        case "Ocean", "Blueberry": return dark ? UIColor(red: 0.60, green: 0.78, blue: 1, alpha: 1) : UIColor(red: 0.12, green: 0.32, blue: 0.58, alpha: 1)
        case "Paprika": return dark ? UIColor(red: 1, green: 0.72, blue: 0.55, alpha: 1) : UIColor(red: 0.57, green: 0.24, blue: 0.09, alpha: 1)
        case "Lemon": return dark ? UIColor(red: 1, green: 0.87, blue: 0.58, alpha: 1) : UIColor(red: 0.46, green: 0.32, blue: 0.04, alpha: 1)
        case "Eggplant": return dark ? UIColor(red: 0.80, green: 0.70, blue: 1, alpha: 1) : UIColor(red: 0.31, green: 0.20, blue: 0.49, alpha: 1)
        case "Beetroot": return dark ? UIColor(red: 0.99, green: 0.60, blue: 0.74, alpha: 1) : UIColor(red: 0.54, green: 0.13, blue: 0.29, alpha: 1)
        default: return dark
            ? UIColor(red: 0.96, green: 0.65, blue: 0.79, alpha: 1)
            : UIColor(red: 0.48, green: 0.19, blue: 0.34, alpha: 1)
        }
    }) }
}

extension EnvironmentValues {
    @Entry var onionaryAccent: Color = OnionaryTheme.color("Onion")
}
