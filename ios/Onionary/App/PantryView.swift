import SwiftUI
import OnionaryCore

struct PantryView: View {
    @Bindable var store: AppStore
    var selected: () -> Void
    @State private var input = ""
    @Environment(\.dismiss) private var dismiss
    var body: some View {
        NavigationStack {
            List {
                Section("What do you have?") {
                    TextField("3 bananas and 2 eggs", text: $input, axis: .vertical)
                        .lineLimit(3...6).accessibilityIdentifier("pantry-input")
                    Text("One ingredient per line, or separate with ‘and’. Include quantities and units when known.")
                        .font(.footnote).foregroundStyle(.secondary)
                }
                Section("Matching recipes") {
                    let matches = PantryMatching.matches(store.kitchen.recipes, supplies: PantryMatching.parse(input))
                    ForEach(matches) { match in
                        Button { store.visit(match.recipe); dismiss(); selected() } label: {
                            VStack(alignment: .leading, spacing: 5) {
                                Text(match.recipe.name).font(.headline)
                                detail("Available", match.matched)
                                detail("Missing", match.missing)
                                detail("Not enough", match.short)
                                detail("Check quantity or unit", match.unchecked)
                            }.foregroundStyle(.primary)
                        }
                        .accessibilityLabel(match.recipe.name)
                        .accessibilityValue(summary(match))
                        .accessibilityIdentifier("pantry-match-\(match.id)")
                    }
                    if !input.isEmpty && matches.isEmpty { Text("No matching recipes") }
                }
                Text("Quantities refer to the original recipe. Only identical units are compared. Check your supplies before cooking.")
                    .font(.footnote).foregroundStyle(.secondary)
            }.dismissibleKeyboard().navigationTitle("Cook with what you have")
                .toolbar { Button("Done") { dismiss() }.accessibilityIdentifier("close-pantry") }
        }
    }
    private func summary(_ match: PantryMatching.Match) -> String {
        [("Available", match.matched), ("Missing", match.missing),
         ("Not enough", match.short), ("Check quantity or unit", match.unchecked)]
            .filter { !$0.1.isEmpty }
            .map { L10n.text($0.0) + ": " + $0.1.joined(separator: ", ") }
            .joined(separator: "; ")
    }
    @ViewBuilder private func detail(_ title: LocalizedStringKey, _ names: [String]) -> some View {
        if !names.isEmpty { HStack(alignment: .top) { Text(title).fontWeight(.medium); Text(names.joined(separator: ", ")) }.font(.caption) }
    }
}
