#if DEBUG
import Foundation
import OnionaryCore

/// Deterministic UI-test transport. Compiled out of release builds.
@MainActor enum UITestBackend {
    static var recipe: [String: Any] = ["id":1,"household_id":1,"name":"Lemon & cheese pasta","notes":"Finish with lemon zest.","total_time_min":20,"active_cooking_time_min":10,"kcal_per_serving":400,"tags":[["id":1,"name":"vegetarian"]],"ingredients":[["id":1,"name":"Cheese","quantity":200,"unit":"g"],["id":2,"name":"Pasta","quantity":250,"unit":"g"]],"instruction_steps":[["id":1,"step_number":1,"description":"Boil the pasta in salted water.","duration_min":10],["id":2,"step_number":2,"description":"Fold in cheese and lemon zest."]]]
    static var planned = false
    static var cooked = false
    static func data(_ path: String, method: String, body: Data?, token: String) throws -> Data {
        if ProcessInfo.processInfo.arguments.contains("--offline-save"), path == "recipes", method == "POST" { throw APIError.unavailable }
        if path == "auth/mobile/refresh" {
            return try JSONSerialization.data(withJSONObject: ["access_token": "renewed", "user_id": "1", "name": "Test Cook", "email": "cook@example.org",
                "refresh_token": "renewed-refresh", "access_expires_at": Date().addingTimeInterval(14 * 86400).timeIntervalSince1970,
                "session_expires_at": Date().addingTimeInterval(42 * 86400).timeIntervalSince1970])
        }
        if ProcessInfo.processInfo.arguments.contains("--renew-session"), token == "test" { throw APIError.unauthorized }
        if ProcessInfo.processInfo.arguments.contains("--expired-session"), token == "test" { throw APIError.unauthorized }
        let input = try body.map { try JSONSerialization.jsonObject(with: $0) as? [String: Any] } ?? nil
        var result: Any = [:]
        if path == "users/me/delete" {
            if ProcessInfo.processInfo.arguments.contains("--offline-delete") { throw APIError.unavailable }
            guard input?["email"] as? String == "cook@example.org" else { throw APIError.unavailable }
            return Data()
        }
        if path == "users/me" { result = ["id": 1, "name": "Test Cook", "email": "cook@example.org"] }
        else if path == "recipes" && method == "GET" { result = [recipe] }
        else if path == "recipes/1" && method == "GET" { result = recipe }
        else if path == "recipes/1" && method == "PUT", let input {
            for (key,value) in input { recipe[key] = value }
            recipe["ingredients"] = (input["ingredients"] as? [[String: Any]] ?? []).enumerated().map { index,item in var copy=item; copy["id"]=index+10; return copy }
            recipe["instruction_steps"] = (input["instruction_steps"] as? [[String: Any]] ?? []).enumerated().map { index,item in var copy=item; copy["id"]=index+10; return copy }
            recipe["tags"] = (input["tags"] as? [String] ?? []).enumerated().map { ["id":$0.offset+1,"name":$0.element] as [String:Any] }
            result=recipe
        } else if path == "recipes/import/parse/html" || path == "recipe-shares/preview" {
            var draft=recipe;draft["tags"]=["vegetarian"];result=draft
        } else if path == "recipes" && method == "POST" { result=recipe }
        else if path == "meal-plan/add" { planned=true }
        else if path == "meal-plan/1/cooked" { cooked=method == "POST" }
        else if path == "meal-plan/1" || (path == "meal-plan" && method == "DELETE") { planned=false }
        else if path == "meal-plan" { result=["items":planned ? [["id":1,"recipe_id":1,"is_cooked":cooked,"recipe":recipe]] : []] }
        else if path == "shopping-list" { result=["items":[["name":"cheese","total_quantity":200,"unit":"g"]]] }
        else if path == "recipe-shares" && method == "POST" { result=["id":"test-link","url":"https://example.org/share.html#"+String(repeating:"a",count:43),"expires_at":"2026-12-01T12:00:00Z"] }
        else if path == "recipe-shares" { result=[] }
        else if path == "recipe-shares/test-link" && method == "DELETE" { result=[:] }
        else { throw CookingError.response("Unexpected UI test request: \(method) \(path)") }
        return try JSONSerialization.data(withJSONObject: result)
    }
}
#endif
