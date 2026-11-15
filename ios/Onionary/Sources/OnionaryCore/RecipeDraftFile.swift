import Foundation

/// Account-scoped recovery copies. Invalid and incomplete forms are deliberately retained.
public struct SavedRecipeDraft: Codable, Identifiable, Sendable {
    public var id: UUID
    public var recipeID: Int?
    public var updatedAt: Date
    public var draft: RecipeDraft
    public init(id: UUID, recipeID: Int?, draft: RecipeDraft) {
        self.id = id; self.recipeID = recipeID; self.draft = draft; updatedAt = Date()
    }
}

public enum RecipeDraftFile {
    public static func read(_ url: URL) throws -> [SavedRecipeDraft] {
        guard FileManager.default.fileExists(atPath: url.path) else { return [] }
        return try JSONDecoder().decode([SavedRecipeDraft].self, from: Data(contentsOf: url))
    }
    public static func write(_ drafts: [SavedRecipeDraft], to url: URL) throws {
        try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
        try JSONEncoder().encode(drafts).write(to: url, options: .atomic)
    }
}
