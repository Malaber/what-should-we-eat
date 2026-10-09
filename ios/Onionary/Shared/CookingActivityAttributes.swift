import ActivityKit
import OnionaryCore

struct CookingActivityAttributes: ActivityAttributes {
    typealias ContentState = CookingSnapshot
    let scope: String
    let recipeID: Int
}
