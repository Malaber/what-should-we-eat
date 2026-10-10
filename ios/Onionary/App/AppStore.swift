import CryptoKit
import Foundation
import Observation
import WidgetKit
import OnionaryCore

@MainActor @Observable
final class AppStore {
    var credential: Credential?
    var kitchen = Kitchen()
    var error: String?
    var busy = false
    let cookingActivity = CookingActivityController()
    var scope: String {
        guard let credential else { return "" }
        return SHA256.hash(data: Data((credential.server.absoluteString + "|" + credential.userID).utf8)).map { String(format: "%02x", $0) }.joined()
    }
    var pendingImport: String?
    var editingRecipe: Recipe?
    var sharingRecipe: Recipe?
    var backend = UserDefaults.standard.string(forKey: "backend") ?? "https://onionary-test.malaber.de"
    var widgetNavigation: KitchenDeepLink.Destination?
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
            if credential == nil || WidgetSnapshotStore.read()?.scope != scope { clearWidget() }
        } catch { self.error = "Could not restore your kitchen: \(error.localizedDescription)" }
    }

    func connect() async {
        guard !busy else { return }
        busy = true; defer { busy = false }
        do {
            let server = try Backend.url(backend)
            let next = try await signIn.signIn(server: server)
            try CredentialStore.save(next)
            UserDefaults.standard.set(server.absoluteString, forKey: "backend")
            // Never display one account's data while loading another account.
            await stopCookingActivity()
            clearWidget()
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
            await refreshWidget()
        } catch { self.error = error.localizedDescription }
    }

    private func persist(_ next: Kitchen) throws {
        guard let file else { throw CookingError.response("Your saved kitchen could not be loaded. Reconnect before making changes.") }
        try KitchenFile.write(next, to: file)
        kitchen = next
        synchronizeCookingActivity()
    }

    private func clearWidget() {
        do { try WidgetSnapshotStore.write(nil); WidgetCenter.shared.reloadTimelines(ofKind: "OnionaryKitchen") }
        catch { self.error = error.localizedDescription }
    }

    func publishWidget(_ items: [MealPlan.Item], account: String) {
        guard account == scope, !account.isEmpty else { return }
        do {
            let snapshot = KitchenWidgetSnapshot(scope: account,
                meals: items.map { .init(id: $0.recipeId, name: $0.recipe.name, cooked: $0.isCooked) },
                language: UserDefaults.standard.string(forKey: "language") ?? "system")
            try WidgetSnapshotStore.write(snapshot)
            WidgetCenter.shared.reloadTimelines(ofKind: "OnionaryKitchen")
        } catch { self.error = error.localizedDescription }
    }

    func refreshWidget() async {
        guard let credential else { clearWidget(); return }
        let account = scope
        do {
            let data = try await OnionaryAPI(server: credential.server, token: credential.token).data("meal-plan")
            let plan = try OnionaryAPI.decoder.decode(MealPlan.self, from: data)
            publishWidget(plan.items, account: account)
        } catch {
            // Offline snapshots retain their timestamp and expire at the week boundary.
        }
    }

    func openWidgetURL(_ url: URL) {
        guard let destination = KitchenDeepLink.destination(url, scope: scope) else {
            if url.scheme == "de.malaber.onionary", url.host == "kitchen" { widgetNavigation = .kitchen }
            return
        }
        if case let .recipe(id) = destination {
            guard let recipe = kitchen.recipes.first(where: { $0.id == id }) else { widgetNavigation = .kitchen; return }
            visit(recipe)
        }
        widgetNavigation = destination
    }

    func synchronizeCookingActivity() {
        let snapshot = current.map { CookingSnapshot($0, locale: L10n.locale) }
        let account = scope
        Task { try? await cookingActivity.synchronize(snapshot, scope: account) }
    }

    private var cookingModePreference: String { "cookingModeDisabled." + scope + "." + String(current?.recipe.id ?? 0) }

    func toggleCookingMode() async {
        if cookingActivity.active {
            UserDefaults.standard.set(true, forKey: cookingModePreference)
            await stopCookingActivity()
        } else {
            UserDefaults.standard.removeObject(forKey: cookingModePreference)
            await startCookingActivity()
        }
    }

    func startCookingActivity() async {
        guard let current else { return }
        do { try await cookingActivity.synchronize(CookingSnapshot(current, locale: L10n.locale), scope: scope, start: true) }
        catch { self.error = error.localizedDescription }
    }

    func stopCookingActivity() async { try? await cookingActivity.synchronize(nil, scope: scope) }

    func visit(_ recipe: Recipe) {
        do { var next = kitchen; next.visit(recipe); try persist(next) }
        catch { self.error = error.localizedDescription }
    }

    func update(_ operation: (inout Adventure) throws -> Void) {
        guard let index = kitchen.adventures.firstIndex(where: { $0.id == kitchen.currentID }) else { return }
        do {
            var next = kitchen; try operation(&next.adventures[index]); try persist(next)
            if !UserDefaults.standard.bool(forKey: cookingModePreference) {
                let snapshot = current.map { CookingSnapshot($0, locale: L10n.locale) }
                let account = scope
                // Automatic starts never interrupt cooking with an authorization error.
                Task { try? await cookingActivity.synchronize(snapshot, scope: account, start: true) }
            }
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
        let url = try RecipeImportLink.accepted(link)
        let isCopy = (try? RecipeImportLink.sharedRecipe(link)) != nil
        let body = try JSONEncoder().encode(["source": "chefkoch", "url": url.absoluteString])
        let data = try await OnionaryAPI(server: credential.server, token: credential.token).data(isCopy ? "recipe-shares/preview" : "recipes/import/parse/html", method: "POST", body: body)
        return try OnionaryAPI.decoder.decode(RecipeDraft.self, from: data)
    }

    func shareRecipe(_ id: Int, hours: Int) async throws -> RecipeShareLink {
        guard let credential else { throw CookingError.response("Sign in before sharing.") }
        let data = try await OnionaryAPI(server: credential.server, token: credential.token).data("recipe-shares", method: "POST", body: JSONEncoder().encode(["recipe_id": id, "hours": hours]))
        return try OnionaryAPI.decoder.decode(RecipeShareLink.self, from: data)
    }
    func revokeRecipeLink(_ id: String) async throws {
        guard let credential else { return }
        _ = try await OnionaryAPI(server: credential.server, token: credential.token).data("recipe-shares/\(id)", method: "DELETE")
    }

    func recipeDraft(id: Int) async throws -> RecipeDraft {
        guard let credential else { throw CookingError.response("Sign in before editing.") }
        let data = try await OnionaryAPI(server: credential.server, token: credential.token).data("recipes/\(id)")
        return try RecipeDraft.fromRecipeResponse(data)
    }

    func restartCurrentRecipe() {
        guard let current, let latest = kitchen.recipes.first(where: { $0.id == current.id }) else { return }
        do {
            var next = kitchen
            next.adventures.removeAll { $0.id == current.id }
            next.visit(latest)
            try persist(next)
        } catch { self.error = error.localizedDescription }
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
            try CredentialStore.remove(); await stopCookingActivity(); clearWidget(); credential = nil; kitchen = Kitchen(); file = nil
        } catch { self.error = "Could not sign out: \(error.localizedDescription)" }
    }

    #if DEBUG
    private func setupUITest() {
        file = FileManager.default.temporaryDirectory.appending(path: "onionary-ui-kitchen.json")
        if ProcessInfo.processInfo.arguments.contains("--reset") {
            try? FileManager.default.removeItem(at: file!)
            UserDefaults.standard.removeObject(forKey: "appearance")
            UserDefaults.standard.removeObject(forKey: "language")
        }
        kitchen = (try? KitchenFile.read(file!)) ?? Kitchen()
        if kitchen.recipes.isEmpty {
            let json = #"[{"id":1,"household_id":1,"name":"Lemon & cheese pasta","notes":"Finish with lemon zest.","total_time_min":20,"ingredients":[{"id":1,"name":"Cheese","quantity":200,"unit":"g"},{"id":2,"name":"Pasta","quantity":250,"unit":"g"}],"instruction_steps":[{"id":1,"step_number":1,"description":"Boil the pasta in salted water.","duration_min":10},{"id":2,"step_number":2,"description":"Fold in cheese and lemon zest.","duration_min":null}]}]"#
            kitchen.recipes = try! OnionaryAPI.decoder.decode([Recipe].self, from: Data(json.utf8))
        }
        credential = Credential(server: URL(string: "https://ui-test.invalid")!, token: "test", userID: "1")
    }
    #endif
}
