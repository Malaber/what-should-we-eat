import SwiftUI
import OnionaryCore

struct CookingTimersBar: View {
    let timers: [RecipeCountdown]
    let remove: (String) -> Void

    var body: some View {
        TimelineView(.periodic(from: .now, by: 1)) { context in
            if timers.count == 1, let timer = timers.first {
                row(timer, at: context.date)
            } else {
                ScrollView {
                    VStack(spacing: 0) {
                        ForEach(timers) { row($0, at: context.date) }
                    }
                }.frame(height: 104)
            }
        }.background(.regularMaterial)
    }

    private func row(_ timer: RecipeCountdown, at now: Date) -> some View {
        let remaining = timer.remaining(at: now)
        return HStack {
            Label(timer.title, systemImage: "timer").lineLimit(1)
            Spacer()
            if let time = RecipeTime(seconds: remaining) {
                Text(time.label(locale: L10n.locale)).monospacedDigit()
                    .accessibilityIdentifier("active-cooking-timer")
            } else {
                Text("Timer done").fontWeight(.semibold)
                    .accessibilityIdentifier("finished-cooking-timer")
            }
            Button { remove(timer.id) } label: {
                Label(remaining > 0 ? "Cancel timer" : "Dismiss timer", systemImage: "xmark.circle.fill")
                    .labelStyle(.iconOnly).frame(minWidth: 44, minHeight: 44)
            }.buttonStyle(.borderless).accessibilityIdentifier("remove-timer-" + timer.id)
        }.padding(.horizontal, 16).frame(minHeight: 52)
    }
}
