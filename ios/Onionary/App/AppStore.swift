import CryptoKit
import Foundation
import Observation
import WidgetKit
import OnionaryCore

@MainActor @Observable
final class AppStore {
    var accountDeleted = false
    var credential: Credential?
    var kitchen = Kitchen()
    var error: String?
    var busy = false
    var refreshing = false
    var needsReauthentication = false
    var reauthenticationError: String?
    var mealItems: [MealPlan.Item] = []
    private var renewal: Task<Credential, Error>?
    private var equipmentRequests: Set<String> = []

    let cookingActivity = CookingActivityController()
    var scope: String {
        guard let credential else { return "" }
        return SHA256.hash(data: Data((credential.server.absoluteString + "|" + credential.userID).utf8)).map { String(format: "%02x", $0) }.joined()
    }
    var pendingImport: String?
    var editingRecipe: Recipe?
    var sharingRecipe: Recipe?
    var backend = UserDefaults.standard.string(forKey: "backend") ?? Backend.defaultAddress
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
            kitchen = Kitchen(); mealItems = []; file = nil; credential = next; needsReauthentication = false
            try load(next)
            await refresh()
        } catch { self.error = error.localizedDescription }
    }

    /// All authenticated requests share one renewal. Only a rejected 401 is replayed;
    /// uncertain network failures never repeat a mutation.
    func request(_ path: String, method: String = "GET", body: Data? = nil) async throws -> Data {
        guard let original = credential else { throw APIError.unauthorized }
        let account = scope
        var active = original
        if let expiry = active.accessExpiresAt, expiry <= Date().timeIntervalSince1970 + 60 {
            active = try await renew()
        }
        do {
            let data = try await OnionaryAPI(server: active.server, token: active.token).data(path, method: method, body: body)
            guard account == scope else { throw APIError.unauthorized }
            return data
        } catch APIError.unauthorized {
            // Another request may already have renewed the same credential.
            guard account == scope, let currentCredential = credential else { throw APIError.unauthorized }
            active = currentCredential.token != active.token ? currentCredential : try await renew()
            guard account == scope else { throw APIError.unauthorized }
            do {
                let data = try await OnionaryAPI(server: active.server, token: active.token).data(path, method: method, body: body)
                guard account == scope else { throw APIError.unauthorized }
                return data
            }
            catch APIError.unauthorized { needsReauthentication = true; throw APIError.unauthorized }
        }
    }

    private func renew() async throws -> Credential {
        if let renewal { return try await renewal.value }
        guard let previous = credential, let refresh = previous.refreshToken,
              (previous.sessionExpiresAt ?? 0) > Date().timeIntervalSince1970 else {
            needsReauthentication = true; throw APIError.unauthorized
        }
        let task = Task { @MainActor in
            let data = try await OnionaryAPI(server: previous.server, token: "").data("auth/mobile/refresh", method: "POST",
                body: JSONEncoder().encode(["refresh_token": refresh]))
            let next = try OnionaryAPI.decoder.decode(TokenResponse.self, from: data).credential(server: previous.server)
            guard self.credential?.token == previous.token, next.userID == previous.userID else { throw APIError.unauthorized }
            #if DEBUG
            if previous.server.host != "ui-test.invalid" { try CredentialStore.save(next) }
            #else
            try CredentialStore.save(next)
            #endif
            self.credential = next
            self.needsReauthentication = false
            return next
        }
        renewal = task
        defer { renewal = nil }
        do { return try await task.value }
        catch APIError.unauthorized {
            // A manual passkey sign-in may finish while renewal is in flight.
            if let current = credential, current.server == previous.server,
               current.userID == previous.userID, current.token != previous.token { return current }
            if credential?.token == previous.token { needsReauthentication = true }
            throw APIError.unauthorized
        }
    }

    func reauthenticate() async {
        guard !busy, let previous = credential else { return }
        busy = true; reauthenticationError = nil
        defer { busy = false }
        do {
            let next: Credential
            #if DEBUG
            if ProcessInfo.processInfo.arguments.contains("--test-passkey-success") || ProcessInfo.processInfo.arguments.contains("--test-passkey-wrong-account") {
                next = Credential(server: previous.server, token: "reauthed",
                    userID: ProcessInfo.processInfo.arguments.contains("--test-passkey-wrong-account") ? "2" : previous.userID,
                    refreshToken: "test-refresh", accessExpiresAt: Date().addingTimeInterval(14 * 86400).timeIntervalSince1970,
                    sessionExpiresAt: Date().addingTimeInterval(42 * 86400).timeIntervalSince1970)
            } else { next = try await signIn.signIn(server: previous.server) }
            #else
            next = try await signIn.signIn(server: previous.server)
            #endif
            guard next.userID == previous.userID, credential?.userID == previous.userID,
                  credential?.server == previous.server else {
                throw CookingError.response(L10n.text("Use the same account to reconnect. Your current kitchen has not changed."))
            }
            #if DEBUG
            if previous.server.host != "ui-test.invalid" { try CredentialStore.save(next) }
            #else
            try CredentialStore.save(next)
            #endif
            credential = next; needsReauthentication = false; error = nil
            await refresh()
        } catch { reauthenticationError = error.localizedDescription }
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
        mealItems = (try? JSONDecoder().decode([MealPlan.Item].self, from: Data(contentsOf: nextFile.appendingPathExtension("meals")))) ?? []
    }

    func refresh() async {
        #if DEBUG
        if ProcessInfo.processInfo.arguments.contains("--marketing") { return }
        #endif
        guard let credential, !refreshing else { return }
        refreshing = true
        defer { refreshing = false }
        do {
            let recipes = try OnionaryAPI.decoder.decode([Recipe].self, from: await request("recipes"))
            // A connection may have changed while the request was in flight.
            guard self.credential?.server == credential.server, self.credential?.userID == credential.userID else { return }
            if credential.name == nil || credential.email == nil {
                struct Profile: Decodable { let id: Int; let name: String; let email: String }
                let profile = try OnionaryAPI.decoder.decode(Profile.self, from: await request("users/me"))
                guard scope == SHA256.hash(data: Data((credential.server.absoluteString + "|" + String(profile.id)).utf8)).map({ String(format: "%02x", $0) }).joined() else { return }
                if var updated = self.credential {
                    updated.name = profile.name; updated.email = profile.email
                    #if DEBUG
                    if updated.server.host != "ui-test.invalid" { try CredentialStore.save(updated) }
                    #else
                    try CredentialStore.save(updated)
                    #endif
                    self.credential = updated
                }
            }
            var next = kitchen; next.recipes = recipes
            try persist(next)
            await syncEquipment()
            await refreshWidget()
            error = nil
        } catch APIError.unauthorized { error = nil }
        catch { self.error = error.localizedDescription }
    }

    private func persist(_ next: Kitchen, syncCooking: Bool = true) throws {
        guard let file else { throw CookingError.response("Your saved kitchen could not be loaded. Reconnect before making changes.") }
        try KitchenFile.write(next, to: file)
        kitchen = next
        if syncCooking { synchronizeCookingActivity() }
    }

    func savePantry(_ supplies: [PantryMatching.Supply]) throws {
        guard credential != nil else { throw APIError.unauthorized }
        guard supplies != (kitchen.pantrySupplies ?? []) else { return }
        var next = kitchen
        next.pantrySupplies = supplies.isEmpty ? nil : supplies
        try persist(next)
    }

    func toggleEquipment(_ name: String) {
        do {
            var next = kitchen
            next.toggleEquipment(name)
            try persist(next, syncCooking: false)
            Task { await syncEquipment() }
        } catch { self.error = error.localizedDescription }
    }

    private func syncEquipment() async {
        let account = scope
        guard !account.isEmpty, equipmentRequests.insert(account).inserted else { return }
        defer { equipmentRequests.remove(account) }
        struct Inventory: Decodable { let owned: [String] }
        do {
            repeat {
                let sent = kitchen.equipmentUpdate
                let body = sent.isEmpty ? nil : try JSONEncoder().encode(sent)
                let data = try await request("users/me/equipment", method: body == nil ? "GET" : "PUT", body: body)
                guard account == scope else { return }
                let result = try OnionaryAPI.decoder.decode(Inventory.self, from: data)
                var next = kitchen
                next.reconcileEquipment(result.owned, sent: sent)
                if next != kitchen { try persist(next, syncCooking: false) }
            } while kitchen.hasPendingEquipment
        } catch {
            // Keep the queued checks for the next toggle or foreground refresh.
        }
    }

    func startCookingTimer(_ time: RecipeTime, id: String, title: String) {
        do {
            var next = kitchen
            if next.startTimer(id: id, title: title, time: time) { try persist(next) }
        } catch { self.error = error.localizedDescription }
    }

    func removeCookingTimer(_ id: String) {
        do {
            var next = kitchen
            next.removeTimer(id)
            try persist(next)
        } catch { self.error = error.localizedDescription }
    }

    private func clearWidget() {
        do { try writeWidgetSnapshot(nil) }
        catch { self.error = error.localizedDescription }
    }

    private func writeWidgetSnapshot(_ snapshot: KitchenWidgetSnapshot?) throws {
        #if DEBUG
        if ProcessInfo.processInfo.arguments.contains("--ui-testing") {
            // Fixture meals must stay in the test app. Asking WidgetKit to
            // reload would also wake the system's widget host in every case.
            try WidgetSnapshotStore.write(snapshot, to: file?.appendingPathExtension("widget"))
            return
        }
        #endif
        try WidgetSnapshotStore.write(snapshot)
        WidgetCenter.shared.reloadTimelines(ofKind: "OnionaryKitchen")
    }

    func publishWidget(_ items: [MealPlan.Item], account: String) {
        guard account == scope, !account.isEmpty else { return }
        do {
            if let file { try JSONEncoder().encode(items).write(to: file.appendingPathExtension("meals"), options: .atomic) }
            mealItems = items
            let snapshot = KitchenWidgetSnapshot(scope: account,
                meals: items.map { .init(id: $0.recipeId, name: $0.recipe.name, cooked: $0.isCooked) },
                language: UserDefaults.standard.string(forKey: "language") ?? "system")
            try writeWidgetSnapshot(snapshot)
        } catch { self.error = error.localizedDescription }
    }

    func refreshWidget() async {
        guard let credential else { clearWidget(); return }
        let account = scope
        do {
            let data = try await request("meal-plan")
            let plan = try OnionaryAPI.decoder.decode(MealPlan.self, from: data)
            guard account == scope else { return }
            publishWidget(plan.items, account: account)
        } catch {
            // Offline snapshots retain their timestamp and expire at the week boundary.
        }
    }

    func openWidgetURL(_ url: URL) {
        Task { await refresh() }
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

    @discardableResult func visit(_ recipe: Recipe, portions: Decimal? = nil) -> Bool {
        do {
            var next = kitchen
            if let portions { try next.visit(recipe, portions: portions) }
            else { next.visit(recipe) }
            try persist(next)
            if portions != nil { synchronizeCookingActivity() }
            return true
        } catch {
            self.error = error.localizedDescription
            return false
        }
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
        let url: URL
        let endpoint: String
        switch try RecipeImportLink.source(link) {
        case .onionary(let copy):
            url = copy
            endpoint = "recipe-shares/preview"
        case .chefkoch(let recipe):
            url = recipe
            endpoint = "recipes/import/parse/html"
        case .website(let page):
            return try await RecipeIntelligence.importPage(page)
        }
        let body = try JSONEncoder().encode(["source": "chefkoch", "url": url.absoluteString])
        let data = try await request(endpoint, method: "POST", body: body)
        return try OnionaryAPI.decoder.decode(RecipeDraft.self, from: data)
    }

    func shareRecipe(_ id: Int, hours: Int) async throws -> RecipeShareLink {
        guard let credential else { throw CookingError.response("Sign in before sharing.") }
        let data = try await request("recipe-shares", method: "POST", body: JSONEncoder().encode(["recipe_id": id, "hours": hours]))
        return try OnionaryAPI.decoder.decode(RecipeShareLink.self, from: data)
    }
    func revokeRecipeLink(_ id: String) async throws {
        guard let credential else { return }
        _ = try await request("recipe-shares/\(id)", method: "DELETE")
    }

    func recipeDraft(id: Int) async throws -> RecipeDraft {
        guard let credential else { throw CookingError.response("Sign in before editing.") }
        let data = try await request("recipes/\(id)")
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

    var savedDrafts: [SavedRecipeDraft] = []
    private var draftsFile: URL? { file?.appendingPathExtension("drafts") }
    func loadDrafts() {
        savedDrafts = []
        do { savedDrafts = try draftsFile.map { try RecipeDraftFile.read($0) } ?? [] }
        catch { self.error = error.localizedDescription }
    }
    func retainDraft(_ draft: SavedRecipeDraft, scope expected: String) throws {
        guard scope == expected, let draftsFile else { throw APIError.unavailable }
        var drafts = try RecipeDraftFile.read(draftsFile)
        drafts.removeAll { $0.id == draft.id }; drafts.insert(draft, at: 0)
        try RecipeDraftFile.write(drafts, to: draftsFile); savedDrafts = drafts
    }
    func removeDraft(_ id: UUID, scope expected: String) throws {
        guard scope == expected, let draftsFile else { throw APIError.unavailable }
        var drafts = try RecipeDraftFile.read(draftsFile)
        drafts.removeAll { $0.id == id }
        try RecipeDraftFile.write(drafts, to: draftsFile); savedDrafts = drafts
    }
    @discardableResult
    func saveRecipe(_ draft: RecipeDraft, id: Int? = nil) async throws -> Recipe {
        guard credential != nil else { throw CookingError.response("Sign in before saving.") }
        let expectedScope = scope
        let data = try draft.validatedData()
        let response = try await request(id.map { "recipes/\($0)" } ?? "recipes", method: id == nil ? "POST" : "PUT", body: data)
        let decoder = JSONDecoder(); decoder.keyDecodingStrategy = .convertFromSnakeCase
        let recipe = try decoder.decode(Recipe.self, from: response)
        guard scope == expectedScope else { throw APIError.unauthorized }
        var next = kitchen
        next.recipes.removeAll { $0.id == recipe.id }; next.recipes.append(recipe)
        // The server has confirmed the write. Cache failures must not trigger another POST.
        do { try persist(next) } catch { kitchen = next; self.error = error.localizedDescription }
        return recipe
    }
    func reloadCookingRecipe(_ recipe: Recipe) throws {
        guard current?.id == recipe.id else { return }
        var next = kitchen
        next.reloadCurrentRecipe(recipe)
        try persist(next)
    }

    func deleteAccount(email: String) async throws {
        guard !busy else { throw APIError.unavailable }
        busy = true; defer { busy = false }
        _ = try await request("users/me/delete", method: "POST", body: JSONEncoder().encode(["email": email]))
        renewal?.cancel(); renewal = nil
        if let file {
            try? FileManager.default.removeItem(at: file)
            try? FileManager.default.removeItem(at: file.appendingPathExtension("meals"))
            try? FileManager.default.removeItem(at: file.appendingPathExtension("drafts"))
            savedDrafts = []
        }
        try? CredentialStore.remove()
        await stopCookingActivity(); clearWidget()
        credential = nil; kitchen = Kitchen(); mealItems = []; file = nil
        pendingImport = nil; editingRecipe = nil; sharingRecipe = nil
        needsReauthentication = false; reauthenticationError = nil; error = nil
        accountDeleted = true
    }

    func disconnect() async {
        guard !busy else { return }
        busy = true; defer { busy = false }
        do {
            if let credential {
                _ = try await request("auth/mobile/logout", method: "POST")
            }
            try CredentialStore.remove(); await stopCookingActivity(); clearWidget(); credential = nil; kitchen = Kitchen(); mealItems = []; file = nil; needsReauthentication = false
        } catch { self.error = "Could not sign out: \(error.localizedDescription)" }
    }

    #if DEBUG
    private func setupUITest() {
        let arguments = ProcessInfo.processInfo.arguments
        let testFile = FileManager.default.temporaryDirectory.appending(path: "onionary-ui-kitchen.json")
        file = testFile
        if arguments.contains("--fresh-equipment-cache") { try? FileManager.default.removeItem(at: testFile) }
        if ProcessInfo.processInfo.arguments.contains("--reset") {
            for key in UserDefaults.standard.dictionaryRepresentation().keys where key.hasPrefix("cookingModeDisabled.") {
                UserDefaults.standard.removeObject(forKey: key)
            }
            try? FileManager.default.removeItem(at: testFile)
            for extensionName in ["drafts", "meals", "widget"] {
                try? FileManager.default.removeItem(at: testFile.appendingPathExtension(extensionName))
            }
            UserDefaults.standard.removeObject(forKey: "accent")
            UserDefaults.standard.removeObject(forKey: "recipe-sort")
            UserDefaults.standard.removeObject(forKey: "recipe-sort-reversed")
            UserDefaults.standard.removeObject(forKey: "appearance")
            UserDefaults.standard.removeObject(forKey: "language")
            UserDefaults.standard.removeObject(forKey: "ui-test-equipment")
        }
        kitchen = (try? KitchenFile.read(testFile)) ?? Kitchen()
        let recipeOptions = ["--ordering-fixture", "--equipment-fixture", "--timer-fixture"]
        if kitchen.recipes.isEmpty && recipeOptions.contains(where: arguments.contains) {
            let data = try! JSONSerialization.data(withJSONObject: [UITestBackend.recipe])
            kitchen.recipes = try! OnionaryAPI.decoder.decode([Recipe].self, from: data)
        } else if kitchen.recipes.isEmpty {
            let json = #"[{"id":1,"household_id":1,"name":"Lemon & cheese pasta","notes":"Finish with lemon zest.","total_time_min":20,"ingredients":[{"id":1,"name":"Cheese","quantity":200,"unit":"g"},{"id":2,"name":"Pasta","quantity":250,"unit":"g"}],"instruction_steps":[{"id":1,"step_number":1,"description":"Boil the pasta in salted water.","duration_min":10},{"id":2,"step_number":2,"description":"Fold in {{Cheese|20%}} and lemon zest.","duration_min":null}]}]"#
            kitchen.recipes = try! OnionaryAPI.decoder.decode([Recipe].self, from: Data(json.utf8))
        }
        if ProcessInfo.processInfo.arguments.contains("--marketing") {
            // Keep screenshot appearance local to this Debug fixture. A global
            // simulator appearance RPC can race cold SpringBoard startup.
            UserDefaults.standard.set("light", forKey: "appearance")
            // Keep the recipe featured in the cooking captures near the top
            // of the alphabetic book on the Duo's shorter cover display.
            let names = ["Creamy lemon pasta", "Roasted tomato soup", "Crispy chickpea bowls", "Mushroom risotto", "Apple cinnamon pancakes", "Herby potato salad"]
            let recipes: [[String: Any]] = names.enumerated().map { index, name in
                var recipe = UITestBackend.recipe
                recipe["id"] = index + 1
                recipe["name"] = name
                recipe["total_time_min"] = [20, 35, 25, 40, 15, 30][index]
                recipe["servings"] = 2
                recipe["tags"] = [["id": 1, "name": "Vegetarian"], ["id": 2, "name": index % 2 == 0 ? "Quick & easy" : "Comfort food"]]
                return recipe
            }
            kitchen.recipes = try! OnionaryAPI.decoder.decode([Recipe].self, from: JSONSerialization.data(withJSONObject: recipes))
        }
        let editingActiveRecipe = arguments.contains("--editing-active-recipe")
        if (editingActiveRecipe || arguments.contains("--active-recipe")), let recipe = kitchen.recipes.first {
            kitchen.visit(recipe)
            if editingActiveRecipe, let ingredient = recipe.ingredients.first,
               let current = kitchen.adventures.firstIndex(where: { $0.id == recipe.id }) {
                kitchen.adventures[current].toggle(key: "ingredient-\(ingredient.id)", label: ingredient.name)
            }
        }
        credential = Credential(server: URL(string: "https://ui-test.invalid")!, token: "test", userID: "1", name: "Test Cook", email: "cook@example.org")
        if arguments.contains("--marketing-lock-screen") {
            for recipe in kitchen.recipes {
                UserDefaults.standard.set(true, forKey: "cookingModeDisabled.\(scope).\(recipe.id)")
            }
        }
        if ProcessInfo.processInfo.arguments.contains("--renew-session") {
            credential?.refreshToken = "test-refresh"
            credential?.sessionExpiresAt = Date().addingTimeInterval(42 * 86400).timeIntervalSince1970
            UITestBackend.expireSessionAfterBackgrounding()
        }
    }
    #endif
}
