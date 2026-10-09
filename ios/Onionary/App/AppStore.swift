import CryptoKit
import Foundation
import Observation
import OnionaryCore

@MainActor @Observable
final class AppStore {
    var credential: Credential?
    var kitchen = Kitchen()
    var error: String?
    var busy = false
    var pendingImport: String?
    var backend = "https://onionary-test.malaber.de"
    private var file: URL?
    private let signIn = BrowserSignIn()

    var current: Adventure? { kitchen.adventures.first { $0.id == kitchen.currentID } }

    init() {
        #if DEBUG
        if ProcessInfo.processInfo.arguments.contains("--ui-testing") {
            setupUITest(); return
        }
        #endif
        do {
            credential = try CredentialStore.read()
            if let credential { try load(credential) }
        } catch { self.error = "Could not restore your kitchen: \(error.localizedDescription)" }
    }

    func connect() async {
        guard !busy else { return }
        busy = true; defer { busy = false }
        do {
            let server = try Backend.url(backend)
            let next = try await signIn.signIn(server: server)
            try CredentialStore.save(next)
            // Never display one account's data while loading another account.
            kitchen = Kitchen(); file = nil; credential = next
            try load(next)
            await refresh()
        } catch { self.error = error.localizedDescription }
    }

    private func load(_ credential: Credential) throws {
        backend = credential.server.absoluteString
        let identity = credential.server.absoluteString + "|" + credential.userID
        let key = SHA256.hash(data: Data(identity.utf8)).map { String(format: "%02x", $0) }.joined()
        let directory = try FileManager.default.url(for: .applicationSupportDirectory, in: .userDomainMask,
                                                    appropriateFor: nil, create: true)
        let nextFile = directory.appending(path: "Onionary/\(key).json")
        let nextKitchen = try KitchenFile.read(nextFile)
        kitchen = nextKitchen; file = nextFile
    }

    func refresh() async {
        guard let credential else { return }
        do {
            let api = OnionaryAPI(server: credential.server, token: credential.token)
            let recipes = try OnionaryAPI.decoder.decode([Recipe].self, from: await api.data("recipes"))
            // A connection may have changed while the request was in flight.
            guard self.credential?.server == credential.server, self.credential?.userID == credential.userID else { return }
            var next = kitchen; next.recipes = recipes
            try persist(next)
        } catch { self.error = error.localizedDescription }
    }

    private func persist(_ next: Kitchen) throws {
        guard let file else { throw CookingError.response("Your saved kitchen could not be loaded. Reconnect before making changes.") }
        try KitchenFile.write(next, to: file)
        kitchen = next
    }

    func visit(_ recipe: Recipe) {
        do { var next = kitchen; next.visit(recipe); try persist(next) }
        catch { self.error = error.localizedDescription }
    }

    func update(_ operation: (inout Adventure) throws -> Void) {
        guard let index = kitchen.adventures.firstIndex(where: { $0.id == kitchen.currentID }) else { return }
        do {
            var next = kitchen; try operation(&next.adventures[index]); try persist(next)
        } catch { self.error = error.localizedDescription }
    }

    func checkImportInbox() {
        guard credential != nil, pendingImport == nil,
              let inbox = UserDefaults(suiteName: "group.de.malaber.onionary"),
              let link = inbox.string(forKey: "pendingRecipeURL") else { return }
        pendingImport = link
        inbox.removeObject(forKey: "pendingRecipeURL")
    }

    func importDraft(_ link: String) async throws -> RecipeDraft {
        guard let credential else { throw CookingError.response("Sign in before importing.") }
        let url = try RecipeImportLink.chefkoch(link)
        let body = try JSONEncoder().encode(["source": "chefkoch", "url": url.absoluteString])
        let data = try await OnionaryAPI(server: credential.server, token: credential.token).data("recipes/import/parse/html", method: "POST", body: body)
        return try OnionaryAPI.decoder.decode(RecipeDraft.self, from: data)
    }

    func saveRecipe(_ draft: RecipeDraft, id: Int? = nil) async throws {
        guard let credential else { throw CookingError.response("Sign in before saving.") }
        let data = try draft.validatedData()
        _ = try await OnionaryAPI(server: credential.server, token: credential.token).data(id.map { "recipes/\($0)" } ?? "recipes", method: id == nil ? "POST" : "PUT", body: data)
        await refresh()
    }

    func disconnect() async {
        guard !busy else { return }
        busy = true; defer { busy = false }
        do {
            if let credential {
                _ = try await OnionaryAPI(server: credential.server, token: credential.token).data("auth/mobile/logout", method: "POST")
            }
            try CredentialStore.remove(); credential = nil; kitchen = Kitchen(); file = nil
        } catch { self.error = "Could not sign out: \(error.localizedDescription)" }
    }

    #if DEBUG
    private func setupUITest() {
        file = FileManager.default.temporaryDirectory.appending(path: "onionary-ui-kitchen.json")
        if ProcessInfo.processInfo.arguments.contains("--reset") { try? FileManager.default.removeItem(at: file!) }
        kitchen = (try? KitchenFile.read(file!)) ?? Kitchen()
        if kitchen.recipes.isEmpty {
            let json = #"[{"id":1,"household_id":1,"name":"Lemon & cheese pasta","notes":"Finish with lemon zest.","total_time_min":20,"ingredients":[{"id":1,"name":"Cheese","quantity":200,"unit":"g"},{"id":2,"name":"Pasta","quantity":250,"unit":"g"}],"instruction_steps":[{"id":1,"step_number":1,"description":"Boil the pasta in salted water.","duration_min":10},{"id":2,"step_number":2,"description":"Fold in cheese and lemon zest.","duration_min":null}]}]"#
            kitchen.recipes = try! OnionaryAPI.decoder.decode([Recipe].self, from: Data(json.utf8))
        }
        credential = Credential(server: URL(string: "https://ui-test.invalid")!, token: "test", userID: "1")
    }
    #endif
}
