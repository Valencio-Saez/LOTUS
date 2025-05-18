//
//  LOTUS_IOSApp.swift
//  LOTUS-IOS
//
//  Created by Valencio Muskiet on 18/05/2025.
//

import SwiftUI
import SwiftData

@main
struct LOTUS_IOSApp: App {
    var sharedModelContainer: ModelContainer = {
        let schema = Schema([Item.self])
        let modelConfiguration = ModelConfiguration(schema: schema, isStoredInMemoryOnly: false)

        do {
            let container = try ModelContainer(for: schema, configurations: [modelConfiguration])
            
            // Insert sample data if empty
            let context = container.mainContext
            let fetchDescriptor = FetchDescriptor<Item>()
            let existingItems = try context.fetch(fetchDescriptor)

            if existingItems.isEmpty {
                let newItem = Item(timestamp: Date())
                context.insert(newItem)
                try context.save()
            }

            return container
        } catch {
            fatalError("Could not create ModelContainer: \(error)")
        }
    }()

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .modelContainer(sharedModelContainer)
    }
}
