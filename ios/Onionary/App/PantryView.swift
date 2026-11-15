import SwiftUI
import OnionaryCore

struct PantryView: View {
    @Bindable var store: AppStore
    var selected: () -> Void
    @State private var input = ""
    @State private var saveError: String?
    @Environment(\.dismiss) private var dismiss

    private struct Entry: Identifiable {
        struct ID: Hashable {
            let supply: PantryMatching.Supply
            let occurrence: Int
        }

        let id: ID
        let index: Int
    }

    private var saved: [PantryMatching.Supply] { store.kitchen.pantrySupplies ?? [] }
    private var entries: [Entry] {
        var counts: [PantryMatching.Supply: Int] = [:]
        return saved.enumerated().map { index, supply in
            let occurrence = counts[supply, default: 0]
            counts[supply] = occurrence + 1
            return Entry(id: .init(supply: supply, occurrence: occurrence), index: index)
        }
    }
    private var pending: [PantryMatching.Supply] { PantryMatching.parse(input) }
    private var hasInput: Bool { !input.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }

    var body: some View {
        NavigationStack {
            List {
                Section {
                    if !saved.isEmpty {
                        ChipFlow(spacing: 8) {
                            ForEach(entries) { entry in
                                let title = ingredientLabel(entry.id.supply)
                                RemovableChip(title: title, removeLabel: String(format: L10n.text("Remove ingredient %@"), title)) {
                                    guard let current = entries.first(where: { $0.id == entry.id }) else { return }
                                    var next = saved
                                    next.remove(at: current.index)
                                    _ = save(next)
                                }.accessibilityIdentifier("pantry-remove-\(title)-\(entry.id.occurrence)")
                            }
                        }
                    }
                    HStack {
                        TextField("3 bananas and 2 eggs", text: $input, axis: .vertical)
                            .lineLimit(1...3)
                            .onChange(of: input) { _, _ in saveError = nil }
                            .accessibilityLabel("Add ingredient")
                            .accessibilityIdentifier("pantry-input")
                        Button { _ = addPending() } label: {
                            Image(systemName: "plus.circle.fill").font(.title3).frame(minWidth: 44, minHeight: 44)
                        }.buttonStyle(.borderless)
                            .accessibilityLabel("Add ingredient")
                            .accessibilityIdentifier("pantry-add")
                            .disabled(pending.isEmpty)
                    }
                    if let saveError { Text(saveError).font(.footnote).foregroundStyle(.red) }
                    Text("One ingredient per line, or separate with ‘and’. Include quantities and units when known.")
                        .font(.footnote).foregroundStyle(.secondary)
                } header: {
                    HStack {
                        Text("What do you have?")
                        Spacer()
                        if !saved.isEmpty || hasInput {
                            Button("Reset") { if save([]) { input = "" } }
                                .buttonStyle(.borderless)
                                .foregroundStyle(OnionaryTheme.accent)
                                .accessibilityIdentifier("pantry-reset")
                        }
                    }
                }
                Section("Matching recipes") {
                    let supplies = saved + pending
                    let matches = PantryMatching.matches(store.kitchen.recipes, supplies: supplies)
                    ForEach(matches) { match in
                        Button {
                            guard addPending() else { return }
                            store.visit(match.recipe); dismiss(); selected()
                        } label: {
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
                    if !supplies.isEmpty && matches.isEmpty { Text("No matching recipes") }
                }
                Text("Quantities refer to the original recipe. Only identical units are compared. Check your supplies before cooking.")
                    .font(.footnote).foregroundStyle(.secondary)
            }.dismissibleKeyboard().navigationTitle("Your pantry")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar { Button("Done") { if addPending() { dismiss() } }.accessibilityIdentifier("close-pantry") }
        }
        .interactiveDismissDisabled(hasInput)
    }

    private func ingredientLabel(_ supply: PantryMatching.Supply) -> String {
        [supply.quantity.map { Numbers.display($0, locale: L10n.locale) } ?? "", supply.unit, supply.name]
            .filter { !$0.isEmpty }.joined(separator: " ")
    }

    private func addPending() -> Bool {
        guard hasInput else { return true }
        let ingredients = pending
        guard !ingredients.isEmpty else {
            saveError = L10n.text("Enter an ingredient name.")
            return false
        }
        guard save(saved + ingredients) else { return false }
        input = ""
        return true
    }

    private func save(_ supplies: [PantryMatching.Supply]) -> Bool {
        do {
            try store.savePantry(supplies)
            saveError = nil
            return true
        } catch {
            saveError = L10n.text(error.localizedDescription)
            return false
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
