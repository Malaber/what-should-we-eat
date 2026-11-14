import XCTest
@testable import OnionaryCore

final class RecipeDraftFileTests: XCTestCase {
    func testIncompleteDraftSurvivesRestartAndIsScoped() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let first = root.appendingPathComponent("account-a.drafts")
        let second = root.appendingPathComponent("account-b.drafts")
        var draft = RecipeDraft(); draft.name = "Unfinished cake"; draft.ingredients = [.init()]
        let saved = SavedRecipeDraft(id: UUID(), recipeID: 42, draft: draft)
        try RecipeDraftFile.write([saved], to: first)
        let restored = try RecipeDraftFile.read(first)
        XCTAssertEqual(restored.first?.id, saved.id)
        XCTAssertEqual(restored.first?.recipeID, 42)
        XCTAssertEqual(restored.first?.draft.name, draft.name)
        XCTAssertEqual(restored.first?.draft.ingredients.count, 1)
        XCTAssertTrue(try RecipeDraftFile.read(second).isEmpty)
        try RecipeDraftFile.write([], to: first)
        XCTAssertTrue(try RecipeDraftFile.read(first).isEmpty)
    }
    func testCorruptionIsReportedInsteadOfOverwritingWork() throws {
        let file = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: file) }
        try Data("broken".utf8).write(to: file)
        XCTAssertThrowsError(try RecipeDraftFile.read(file))
    }
}
