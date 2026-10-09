import SwiftUI
import WidgetKit
import OnionaryCore

struct KitchenEntry: TimelineEntry {
    let date: Date
    let snapshot: KitchenWidgetSnapshot?
}
struct KitchenProvider: TimelineProvider {
    func placeholder(in context: Context) -> KitchenEntry {
        KitchenEntry(date: .now, snapshot: KitchenWidgetSnapshot(scope: "preview", meals: [
            .init(id: 1, name: "Lemon & cheese pasta", cooked: false),
            .init(id: 2, name: "Vegetable soup", cooked: true)
        ]))
    }
    func getSnapshot(in context: Context, completion: @escaping (KitchenEntry) -> Void) {
        completion(context.isPreview ? placeholder(in: context) : KitchenEntry(date: .now, snapshot: WidgetSnapshotStore.read()))
    }
    func getTimeline(in context: Context, completion: @escaping (Timeline<KitchenEntry>) -> Void) {
        let now = Date()
        let snapshot = WidgetSnapshotStore.read()
        let current = snapshot?.isCurrent(at: now) == true ? snapshot : nil
        var entries = [KitchenEntry(date: now, snapshot: current)]
        if let current { entries.append(KitchenEntry(date: current.expires, snapshot: nil)) }
        completion(Timeline(entries: entries, policy: .after(now.addingTimeInterval(3600))))
    }
}
struct KitchenWidget: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: "OnionaryKitchen", provider: KitchenProvider()) { entry in
            KitchenWidgetView(entry: entry)
                .environment(\.locale, entry.snapshot?.language == "de" ? Locale(identifier: "de") : entry.snapshot?.language == "en" ? Locale(identifier: "en") : .current)
                .containerBackground(.background, for: .widget)
        }.configurationDisplayName("This week’s kitchen")
            .description("Your household meal plan, ready to cook.")
            .supportedFamilies([.systemSmall, .systemMedium, .systemLarge])
    }
}
private struct KitchenWidgetView: View {
    let entry: KitchenEntry
    @Environment(\.widgetFamily) private var family
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("This week’s kitchen", systemImage: "calendar").font(.headline)
            if let snapshot = entry.snapshot, snapshot.isCurrent(at: entry.date), !snapshot.meals.isEmpty {
                ForEach(snapshot.meals.prefix(family == .systemSmall ? 2 : family == .systemMedium ? 3 : 7)) { meal in
                    Link(destination: snapshot.link(recipeID: meal.id)) {
                        Label(meal.name, systemImage: meal.cooked ? "checkmark.circle.fill" : "fork.knife")
                            .font(.subheadline).lineLimit(1).foregroundStyle(meal.cooked ? .secondary : .primary)
                    }
                }
                Spacer(minLength: 0)
                Text(snapshot.updated, style: .relative).font(.caption2).foregroundStyle(.secondary)
            } else {
                Text("Open Kitchen to update your plan.").font(.subheadline).foregroundStyle(.secondary)
            }
        }.frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            .widgetURL(entry.snapshot?.link() ?? URL(string: "de.malaber.onionary://kitchen"))
    }
}
