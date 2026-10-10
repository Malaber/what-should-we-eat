import Foundation
import OnionaryCore

/// This shared container contains display data only; credentials stay in the app keychain.
enum WidgetSnapshotStore {
    static var file: URL? {
        FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: "group.de.malaber.onionary")?
            .appendingPathComponent("kitchen-widget.json")
    }
    static func read() -> KitchenWidgetSnapshot? {
        guard let file, let data = try? Data(contentsOf: file) else { return nil }
        return try? JSONDecoder().decode(KitchenWidgetSnapshot.self, from: data)
    }
    static func write(_ snapshot: KitchenWidgetSnapshot?) throws {
        guard let file else { return }
        if let snapshot {
            try JSONEncoder().encode(snapshot).write(to: file, options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
        } else if FileManager.default.fileExists(atPath: file.path) {
            try FileManager.default.removeItem(at: file)
        }
    }
}
