import Foundation

public enum AccountIdentity {
    public static func maskedEmail(_ email: String) -> String {
        let parts = email.split(separator: "@", omittingEmptySubsequences: false)
        guard parts.count == 2, let first = parts[0].first, !parts[1].isEmpty else { return "***" }
        return String(first) + "***@" + String(parts[1])
    }
}
