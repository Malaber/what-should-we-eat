import SwiftUI
import UIKit

enum OnionaryTheme {
    static let background = Color(uiColor: UIColor { traits in
        traits.userInterfaceStyle == .dark
            ? UIColor(red: 0.13, green: 0.106, blue: 0.125, alpha: 1)
            : UIColor(red: 0.984, green: 0.961, blue: 0.914, alpha: 1)
    })
    static let accent = Color(uiColor: UIColor { traits in
        traits.userInterfaceStyle == .dark
            ? UIColor(red: 0.96, green: 0.65, blue: 0.79, alpha: 1)
            : UIColor(red: 0.48, green: 0.19, blue: 0.34, alpha: 1)
    })
}
