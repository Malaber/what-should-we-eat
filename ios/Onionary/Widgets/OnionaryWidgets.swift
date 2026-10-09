import ActivityKit
import SwiftUI
import WidgetKit
import OnionaryCore

@main
struct OnionaryWidgets: WidgetBundle {
    var body: some Widget { CookingLiveActivity() }
}

struct CookingLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: CookingActivityAttributes.self) { context in
            VStack(alignment: .leading, spacing: 8) {
                Label(context.state.title, systemImage: "flame.fill").font(.headline).lineLimit(2)
                HStack {
                    Text("\(context.state.portions) portions")
                    Spacer()
                    Text("\(context.state.checked) / \(context.state.total)").monospacedDigit()
                }.font(.caption)
                ProgressView(value: Double(context.state.checked), total: Double(max(1, context.state.total)))
                Text(context.isStale ? "Open Onionary to refresh" : context.state.nextStep)
                    .font(.subheadline).lineLimit(3)
            }.padding().activityBackgroundTint(Color(.secondarySystemBackground))
                .widgetURL(URL(string: "de.malaber.onionary://cooking?scope=\(context.attributes.scope)"))
        } dynamicIsland: { context in
            DynamicIsland {
                DynamicIslandExpandedRegion(.leading) { Image(systemName: "flame.fill") }
                DynamicIslandExpandedRegion(.trailing) { Text("\(context.state.checked)/\(context.state.total)").monospacedDigit() }
                DynamicIslandExpandedRegion(.bottom) {
                    VStack(alignment: .leading) {
                        Text(context.state.title).font(.headline).lineLimit(1)
                        Text(context.isStale ? "Open Onionary to refresh" : context.state.nextStep).font(.caption).lineLimit(2)
                    }
                }
            } compactLeading: { Image(systemName: "flame.fill")
            } compactTrailing: { Text("\(context.state.checked)/\(context.state.total)").monospacedDigit()
            } minimal: { Image(systemName: "flame.fill") }
            .widgetURL(URL(string: "de.malaber.onionary://cooking?scope=\(context.attributes.scope)"))
        }
    }
}
