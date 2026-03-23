import os
import json
from execution.db.database import SessionLocal
from execution.db.models import Recipe, Ingredient, InstructionStep, Tag, Household

def seed_recipes():
    db = SessionLocal()
    household = db.query(Household).first()
    if not household:
        household = Household(name='Demo')
        db.add(household); db.commit(); db.refresh(household)
    
    recipes_data = [
        {
            "name": "Orzotto mit Bifteki und Spinat",
            "kcal_per_serving": 875,
            "active_cooking_time_min": 25,
            "total_time_min": 35,
            "tags": ["Reis", "Fleisch", "Schnell"], # Orzo is pasta, but often used like Reis. Let's use Pasta
            "ingredients": [
                {"name": "gemischte Hackfleischzubereitung", "quantity": 250, "unit": "g"},
                {"name": "Orzo-Nudeln", "quantity": 180, "unit": "g"},
                {"name": "Hirtenkäse", "quantity": 100, "unit": "g"},
                {"name": "Karotte", "quantity": 50, "unit": "g"},
                {"name": "Babyspinat", "quantity": 50, "unit": "g"},
                {"name": "Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauchzehe", "quantity": 1, "unit": "Stück"},
                {"name": "Ajvar", "quantity": 25, "unit": "g"},
                {"name": "Hartkäse ital. Art", "quantity": 20, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Für die Bifteki: Hirtenkäse bröseln. Mit Hackfleisch, Gewürz, Oregano, Salz und Pfeffer kneten. Frikadellen formen.", "duration_min": None},
                {"step_number": 2, "description": "Orzo braten: Zwiebelstreifen anbraten. Ajvar, Oregano, Orzo, Karotten und Knoblauch zugeben und 2-3 Min. braten. Mit Wasser und Brühe ablöschen und 10-12 Min. köcheln lassen.", "duration_min": 15},
                {"step_number": 3, "description": "Bifteki braten: In Pfanne Öl erhitzen und Frikadellen je Seite 6-7 Min. anbraten.", "duration_min": 14},
                {"step_number": 4, "description": "Vorbereitung: Knoblauch hacken, Zwiebel in Streifen schneiden. Karotte in Halbmonde schneiden.", "duration_min": 5},
                {"step_number": 5, "description": "Orzo verfeinern: Spinat unter die Orzo heben. Käse einrühren, würzen. Bifteki zum Erwärmen 1-2 Min. in die Pfanne geben.", "duration_min": 2},
                {"step_number": 6, "description": "Anrichten: Orzotto auf Teller verteilen und Bifteki darauf anrichten.", "duration_min": None}
            ]
        },
        {
            "name": "Harissa Cenaschew-Pilaf mit Cranberries",
            "kcal_per_serving": 879,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Reis", "Viel Gemüse", "Vegetarisch"],
            "ingredients": [
                {"name": "Basmatireis", "quantity": 150, "unit": "g"},
                {"name": "Zucchini", "quantity": 1, "unit": "Stück"},
                {"name": "Buschbohnen", "quantity": 200, "unit": "g"},
                {"name": "Cranberries", "quantity": 20, "unit": "g"},
                {"name": "Cashewkerne", "quantity": 40, "unit": "g"},
                {"name": "Petersilie", "quantity": 10, "unit": "g"},
                {"name": "Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Zitrone", "quantity": 1, "unit": "Stück"},
                {"name": "Crème fraîche", "quantity": 100, "unit": "g"},
                {"name": "Tomatenmark", "quantity": 35, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Zucchini in Streifen, Bohnen halbieren. Zwiebel würfeln. Zitrone vierteln.", "duration_min": 5},
                {"step_number": 2, "description": "Gemüse anbraten: Zwiebel anbraten, dann Gemüse und Tomatenmark mitbraten.", "duration_min": 4},
                {"step_number": 3, "description": "Reis garen: Harissa, Brühe, Cranberries und Reis unterrühren, mit Wasser ablöschen. 12 Min. köcheln lassen.", "duration_min": 12},
                {"step_number": 4, "description": "Gremolata: Cashews und Petersilie hacken, mit Olivenöl und Zitronensaft vermengen.", "duration_min": 5},
                {"step_number": 5, "description": "Pilaf vollenden: Reis 10 Min. quellen lassen. Crème fraîche unterrühren.", "duration_min": 10},
                {"step_number": 6, "description": "Anrichten: Pilaf verteilen, Gremolata darüber geben.", "duration_min": None}
            ]
        },
        {
            "name": "Harissa Grillkäse mit Kartoffelcroûtons",
            "kcal_per_serving": 647,
            "active_cooking_time_min": 20,
            "total_time_min": 35,
            "tags": ["Kartoffeln", "Vegetarisch"],
            "ingredients": [
                {"name": "Grillkäse Zypriotischer Art", "quantity": 200, "unit": "g"},
                {"name": "Ofenkartoffel", "quantity": 200, "unit": "g"},
                {"name": "Spitzpaprika", "quantity": 1, "unit": "Stück"},
                {"name": "Gurke", "quantity": 0.5, "unit": "Stück"},
                {"name": "Salatherz", "quantity": 1, "unit": "Stück"},
                {"name": "rote Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauchzehe", "quantity": 1, "unit": "Stück"},
                {"name": "Senf", "quantity": 10, "unit": "ml"},
                {"name": "Naturjoghurt", "quantity": 75, "unit": "g"},
                {"name": "Aprikosenchutney", "quantity": 25, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Kartoffeln rösten: Backofen vorheizen. Kartoffeln in Würfel schneiden, mit Öl, Knoblauch, Harissa, Sesam würzen. 20-25 Min. backen.", "duration_min": 25},
                {"step_number": 2, "description": "Dressing: Joghurt, Chutney, Senf, Essig, Wasser, Salz und Pfeffer verrühren.", "duration_min": 5},
                {"step_number": 3, "description": "Gemüse vorbereiten: Gurke, Paprika, Salat schneiden und mit Dressing marinieren.", "duration_min": 5},
                {"step_number": 4, "description": "Grillkäse braten: Grillkäse in Würfel und Zwiebel in Streifen braten. Harissa und Sesam dazugeben.", "duration_min": 5},
                {"step_number": 5, "description": "Anrichten: Salat toppen mit Kartoffeln und Käse.", "duration_min": None}
            ]
        },
        {
            "name": "One-Pot Gigli mit Rinderhackfleisch",
            "kcal_per_serving": 1012,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Pasta", "Fleisch", "Schnell"],
            "ingredients": [
                {"name": "Rinderhackfleisch", "quantity": 200, "unit": "g"},
                {"name": "Gigli Nudeln", "quantity": 250, "unit": "g"},
                {"name": "Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Basilikum", "quantity": 10, "unit": "g"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Tomatenpesto", "quantity": 25, "unit": "g"},
                {"name": "Hartkäse", "quantity": 40, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Wasser kochen, Kräuter hacken, Zwiebel hacken.", "duration_min": 5},
                {"step_number": 2, "description": "Anbraten: Knoblauch, Hackfleisch, Zwiebel 2-3 Min. braten.", "duration_min": 3},
                {"step_number": 3, "description": "Pasta kochen: Sahne, Wasser, Brühe, Harissa, Nudeln zugeben. 11-13 Min. köcheln.", "duration_min": 13},
                {"step_number": 4, "description": "Vollenden: Tomatenpesto und Käse unterrühren.", "duration_min": 2},
                {"step_number": 5, "description": "Anrichten: Auf tiefen Tellern mit restlichem Käse servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Spätzlepfanne mit Bacon und Birne",
            "kcal_per_serving": 843,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Schnell", "Fleisch", "Kartoffeln"],
            "ingredients": [
                {"name": "frische Eierspätzle", "quantity": 400, "unit": "g"},
                {"name": "Bacon Streifen", "quantity": 80, "unit": "g"},
                {"name": "Birne", "quantity": 1, "unit": "Stück"},
                {"name": "Babyspinat", "quantity": 50, "unit": "g"},
                {"name": "Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Gouda gerieben", "quantity": 50, "unit": "g"},
                {"name": "Hartkäse geraspelt", "quantity": 20, "unit": "g"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Birne schälen und würfeln, Zwiebel in Streifen schneiden.", "duration_min": 5},
                {"step_number": 2, "description": "Birne anbraten: Bacon, Zwiebel, Birne 5-7 Min. anbraten.", "duration_min": 7},
                {"step_number": 3, "description": "Spätzle anbraten: Spätzle 7 Min. in Öl anbraten.", "duration_min": 7},
                {"step_number": 4, "description": "Soße: Zur Birnenpfanne Kochsahne und Wasser geben, 3 Min. köcheln. Gouda zugeben.", "duration_min": 4},
                {"step_number": 5, "description": "Vollenden: Spinat unter die Soße geben, gebratene Spätzle unterheben.", "duration_min": 2}
            ]
        },
        {
            "name": "Strozzapreti mit Brokkoli in Sahnesoße",
            "kcal_per_serving": 680,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Pasta", "Viel Gemüse", "Vegetarisch"],
            "ingredients": [
                {"name": "Strozzapreti", "quantity": 250, "unit": "g"},
                {"name": "Brokkoli", "quantity": 1, "unit": "Stück"},
                {"name": "Zitrone", "quantity": 1, "unit": "Stück"},
                {"name": "Basilikum", "quantity": 10, "unit": "g"},
                {"name": "Basilikumpaste", "quantity": 15, "unit": "ml"},
                {"name": "Knoblauch & Zwiebel gehackt", "quantity": 35, "unit": "g"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Gouda", "quantity": 50, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Gemüse schneiden: Brokkoliröschen schneiden, Stiele in Scheiben.", "duration_min": 5},
                {"step_number": 2, "description": "Brokkoli kochen: Brokkolistiele 4-5 Min. kochen. Strozzapreti und Röschen zugeben, 4-5 Min. kochen.", "duration_min": 10},
                {"step_number": 3, "description": "Soße: Knoblauch und Zwiebel anschwitzen. Sahne, Gemüsebrühe, Käse und Wasser zugeben, 5 Min. köcheln.", "duration_min": 7},
                {"step_number": 4, "description": "Fertigstellen: Brokkoli und Pasta zur Soße geben. Mit Zitronensaft abschmecken.", "duration_min": 2}
            ]
        },
        {
            "name": "Käsefritten mit Süßkartoffeln",
            "kcal_per_serving": 1142,
            "active_cooking_time_min": 15,
            "total_time_min": 35,
            "tags": ["Kartoffeln", "Vegetarisch"],
            "ingredients": [
                {"name": "Grillkäse Zypriotischer Art", "quantity": 200, "unit": "g"},
                {"name": "Süßkartoffel", "quantity": 300, "unit": "g"},
                {"name": "Mayonnaise", "quantity": 40, "unit": "ml"},
                {"name": "Semmelbrösel", "quantity": 50, "unit": "g"},
                {"name": "Sesamsamen", "quantity": 10, "unit": "g"},
                {"name": "BBQ-Soße", "quantity": 60, "unit": "ml"},
                {"name": "Hoisinsoße", "quantity": 50, "unit": "ml"},
                {"name": "Senf", "quantity": 8, "unit": "g"},
                {"name": "Gurke", "quantity": 0.5, "unit": "Stück"},
                {"name": "Zitrone", "quantity": 1, "unit": "Stück"}
            ],
            "steps": [
                {"step_number": 1, "description": "Süßkartoffel backen: Halbieren, in Halbmonde schneiden. Mit Sesam, Öl im Ofen 25-30 Min. garen.", "duration_min": 30},
                {"step_number": 2, "description": "Käsefritten: Grillkäse in Stifte schneiden, mit Mayonnaise und Semmelbröseln panieren.", "duration_min": 10},
                {"step_number": 3, "description": "Gurkenstifte: Gurke, Zitronenabrieb, Zitronensaft, Honig vermengen und marinieren lassen.", "duration_min": 5},
                {"step_number": 4, "description": "Dips: Senf mit Honig; BBQ-Soße; Hoisinsoße in Schüsseln anrichten.", "duration_min": 2},
                {"step_number": 5, "description": "Käsefritten anbraten: In sehr viel Öl 4-6 Min. rundum braten.", "duration_min": 6}
            ]
        },
        {
            "name": "Linguine alla Foriana mit Tomaten und Nüssen",
            "kcal_per_serving": 921,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Pasta", "Vegetarisch", "Schnell", "Gesund"],
            "ingredients": [
                {"name": "frische Linguine", "quantity": 375, "unit": "g"},
                {"name": "Pinienkerne", "quantity": 10, "unit": "g"},
                {"name": "Hefeflocken", "quantity": 5, "unit": "g"},
                {"name": "Kirschtomaten", "quantity": 125, "unit": "g"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Rucola", "quantity": 50, "unit": "g"},
                {"name": "Balsamicocreme", "quantity": 12, "unit": "g"},
                {"name": "Mandeln gehobelt", "quantity": 30, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Tomaten halbieren, Knoblauch abziehen. Zitrone reiben.", "duration_min": 5},
                {"step_number": 2, "description": "Nüsse rösten: Pinienkerne und Mandeln 2-3 Min. rösten.", "duration_min": 3},
                {"step_number": 3, "description": "Pesto: Hefeflocken, Knoblauch, Zitrone, Öl, Nüsse pürieren.", "duration_min": 5},
                {"step_number": 4, "description": "Pasta kochen: Linguine 3 Min. kochen, Kochwasser auffangen.", "duration_min": 3},
                {"step_number": 5, "description": "Soße: Pesto mit Kochwasser pürieren. Kirschtomaten anbraten. Pasta und Soße hinzugeben.", "duration_min": 4}
            ]
        },
        {
            "name": "Curry-Aprikosen-Hähnchen vom Blech",
            "kcal_per_serving": 467,
            "active_cooking_time_min": 10,
            "total_time_min": 35,
            "tags": ["Fleisch", "Gesund", "Viel Gemüse"],
            "ingredients": [
                {"name": "Hähnchenbrustfilet", "quantity": 250, "unit": "g"},
                {"name": "Aprikosenchutney", "quantity": 50, "unit": "g"},
                {"name": "rote Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Blumenkohl", "quantity": 0.5, "unit": "Stück"},
                {"name": "Ofenkartoffel", "quantity": 150, "unit": "g"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "Naturjoghurt", "quantity": 75, "unit": "g"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Zwiebel in Spalten, Karotte in Scheiben, Kartoffel in Würfel schneiden.", "duration_min": 10},
                {"step_number": 2, "description": "Blumenkohl: In dicke Scheiben schneiden.", "duration_min": 2},
                {"step_number": 3, "description": "Backen: Gemüse mit Öl und Gewürz vermengen, 25-30 Min. backen.", "duration_min": 30},
                {"step_number": 4, "description": "Fleisch: Hähnchen mit Aprikosenchutney in den letzten 15 Min. zum Gemüse geben.", "duration_min": 15},
                {"step_number": 5, "description": "Dip: Joghurt mit Kokos Curry und Gewürzen anrühren.", "duration_min": 3}
            ]
        },
        {
            "name": "Sloppy Joe Burger mit Kartoffelchips",
            "kcal_per_serving": 1008,
            "active_cooking_time_min": 20,
            "total_time_min": 35,
            "tags": ["Fleisch", "Schnell", "Kartoffeln"],
            "ingredients": [
                {"name": "Rinderhackfleisch", "quantity": 200, "unit": "g"},
                {"name": "Brioche Bun", "quantity": 2, "unit": "Stück"},
                {"name": "Worcester Sauce", "quantity": 8, "unit": "ml"},
                {"name": "Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Tomatenmark", "quantity": 70, "unit": "g"},
                {"name": "Mayonnaise", "quantity": 50, "unit": "g"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "Ofenkartoffel", "quantity": 200, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Kartoffeln: In Scheiben schneiden, mit Öl backen (25-30 Min.). Buns am Ende 5 Min. aufbacken.", "duration_min": 30},
                {"step_number": 2, "description": "Soße: Zwiebel anschwitzen, Hackfleisch mitbraten.", "duration_min": 7},
                {"step_number": 3, "description": "Soße verfeinern: Tomatenmark, Worcester, Wasser, Zucker, Essig zugeben. 5 Min. köcheln.", "duration_min": 5},
                {"step_number": 4, "description": "Slaw: Karotten reiben, mit Mayo und Essig verrühren.", "duration_min": 5},
                {"step_number": 5, "description": "Vollenden: Buns mit Sloppy Joe und Slaw füllen.", "duration_min": None}
            ]
        }
    ]

    all_tags = {}
    for r in recipes_data:
        for t_name in r["tags"]:
            if t_name not in all_tags:
                tag = db.query(Tag).filter(Tag.name == t_name).first()
                if not tag:
                    tag = Tag(name=t_name)
                    db.add(tag)
                    db.commit()
                    db.refresh(tag)
                all_tags[t_name] = tag

    for r_data in recipes_data:
        recipe = db.query(Recipe).filter(Recipe.name == r_data["name"]).first()
        if not recipe:
            recipe = Recipe(
                household_id=household.id,
                name=r_data["name"],
                kcal_per_serving=r_data["kcal_per_serving"],
                active_cooking_time_min=r_data["active_cooking_time_min"],
                total_time_min=r_data["total_time_min"]
            )
            db.add(recipe)
            db.commit()
            db.refresh(recipe)
            
            recipe.tags = [all_tags[t] for t in r_data["tags"]]
            
            for ing_data in r_data["ingredients"]:
                ing = Ingredient(
                    recipe_id=recipe.id,
                    name=ing_data["name"],
                    quantity=ing_data["quantity"],
                    unit=ing_data["unit"]
                )
                db.add(ing)
                
            for step_data in r_data["steps"]:
                step = InstructionStep(
                    recipe_id=recipe.id,
                    step_number=step_data["step_number"],
                    description=step_data["description"],
                    duration_min=step_data["duration_min"]
                )
                db.add(step)
            
            db.commit()
            print(f"Added {recipe.name}")

if __name__ == "__main__":
    seed_recipes()
