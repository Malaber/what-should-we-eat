import os
import json
from execution.db.database import SessionLocal
from execution.db.models import Recipe, Ingredient, InstructionStep, Tag

def seed_recipes():
    db = SessionLocal()
    
    recipes_data = [
        {
            "name": "Pilzfiorelli mit Zucchini in Bacon-Sahnesoße",
            "kcal_per_serving": 820,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Pasta", "Fleisch", "Schnell", "Viel Gemüse"],
            "ingredients": [
                {"name": "Fiorelli mit Pilzfüllung", "quantity": 300, "unit": "g"},
                {"name": "Bacon Streifen", "quantity": 80, "unit": "g"},
                {"name": "Zucchini", "quantity": 1, "unit": "Stück"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Basilikum", "quantity": 10, "unit": "g"},
                {"name": "Basilikumpaste", "quantity": 15, "unit": "ml"},
                {"name": "Hartkäse gerieben", "quantity": 20, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Gemüse schneiden: Zucchini in Halbmonde. Basilikumblättchen hacken.", "duration_min": 5},
                {"step_number": 2, "description": "Pasta kochen: Fiorelli 5-6 Min. in Salzwasser garen.", "duration_min": 6},
                {"step_number": 3, "description": "Zucchini braten: Bacon und Zucchini in Öl ca. 2 Min. anbraten.", "duration_min": 2},
                {"step_number": 4, "description": "Soße einköcheln: Zucchini mit Sahne und Wasser ablöschen. Basilikumpaste zugeben und 1-2 Min. einköcheln lassen.", "duration_min": 2},
                {"step_number": 5, "description": "Pasta vollenden: Fiorelli in die Pfanne geben, mit Basilikum, Salz und Pfeffer abschmecken.", "duration_min": 2},
                {"step_number": 6, "description": "Anrichten: Pilzfiorelli verteilen und mit Hartkäse bestreuen.", "duration_min": None}
            ]
        },
        {
            "name": "Spätzlepfanne mit Bacon und Porree",
            "kcal_per_serving": 848,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Pasta", "Fleisch", "Schnell"],
            "ingredients": [
                {"name": "frische Eierspätzle", "quantity": 400, "unit": "g"},
                {"name": "Bacon Scheiben", "quantity": 100, "unit": "g"},
                {"name": "Porree", "quantity": 0.5, "unit": "Stück"},
                {"name": "Schalotte", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Tomatenpesto", "quantity": 25, "unit": "g"},
                {"name": "Crème fraîche", "quantity": 100, "unit": "g"},
                {"name": "Hühnerbrühepulver", "quantity": 4, "unit": "g"},
                {"name": "Hartkäse", "quantity": 40, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Schalotte und Knoblauch hacken. Porree in Halbmonde, Bacon in Streifen schneiden.", "duration_min": 5},
                {"step_number": 2, "description": "Spätzle braten: Spätzle 4-6 Min. in Öl knusprig anbraten und beiseitestellen.", "duration_min": 6},
                {"step_number": 3, "description": "Bacon anbraten: Bacon 4-5 Min. braten. Porree und Schalotte zugeben und 5-6 Min. weiterbraten.", "duration_min": 11},
                {"step_number": 4, "description": "Gemüse hinzufügen: Knoblauch zugeben. Mit Crème fraîche, Brühe, Tomatenpesto und Wasser ablöschen.", "duration_min": 3},
                {"step_number": 5, "description": "Spätzle vollenden: Gebratene Spätzle in die Soße geben, 1 Min. köcheln.", "duration_min": 1},
                {"step_number": 6, "description": "Anrichten: Mit Hartkäse bestreuen.", "duration_min": None}
            ]
        },
        {
            "name": "Sriracha-Teriyaki-Burger mit Süßkartoffeln",
            "kcal_per_serving": 1166,
            "active_cooking_time_min": 25,
            "total_time_min": 35,
            "tags": ["Fleisch", "Kartoffeln", "Schnell"],
            "ingredients": [
                {"name": "Rinderhackfleisch", "quantity": 200, "unit": "g"},
                {"name": "Brioche Bun", "quantity": 2, "unit": "Stück"},
                {"name": "Gouda gerieben", "quantity": 50, "unit": "g"},
                {"name": "Süßkartoffel", "quantity": 300, "unit": "g"},
                {"name": "Teriyakisoße", "quantity": 50, "unit": "ml"},
                {"name": "Sriracha Sauce", "quantity": 8, "unit": "ml"},
                {"name": "Mayonnaise", "quantity": 25, "unit": "g"},
                {"name": "Naturjoghurt", "quantity": 75, "unit": "g"},
                {"name": "Limette", "quantity": 1, "unit": "Stück"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "Salatherz", "quantity": 1, "unit": "Stück"},
                {"name": "Sesamsamen", "quantity": 10, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Süßkartoffeln backen: In Spalten schneiden, mit Öl, Salz und Sesam 20-25 Min. backen.", "duration_min": 25},
                {"step_number": 2, "description": "Dip & Soße: Sriracha-Dip aus Mayo, Joghurt und Sriracha rühren. Teriyakisoße mit Honig, Limettensaft und Wasser verrühren.", "duration_min": 5},
                {"step_number": 3, "description": "Salat: Salat in Streifen schneiden. Karotte raspeln. Mit 1 EL Sriracha-Dip, Salz, Pfeffer und Limettensaft vermengen.", "duration_min": 5},
                {"step_number": 4, "description": "Burger braten: Patties formen und 2-3 Min. je Seite anbraten. Mit Teriyakisoße ablöschen, Käse daraufgeben und 1 Min. schmelzen lassen.", "duration_min": 7},
                {"step_number": 5, "description": "Aufbacken: Buns in den letzten 2 Min. zu den Kartoffeln in den Ofen geben.", "duration_min": 2},
                {"step_number": 6, "description": "Anrichten: Buns belegen mit Dip, Patties, Salat. Mit Süßkartoffeln servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Dinkel-Salat mit Hirtenkäse",
            "kcal_per_serving": 608,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Vegetarisch", "Schnell", "Gesund"],
            "ingredients": [
                {"name": "Dinkel vorgekocht", "quantity": 450, "unit": "g"},
                {"name": "Hirtenkäse", "quantity": 100, "unit": "g"},
                {"name": "Salatgurke", "quantity": 1, "unit": "Stück"},
                {"name": "Tomate", "quantity": 1, "unit": "Stück"},
                {"name": "rote Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Oregano", "quantity": 1, "unit": "g"},
                {"name": "Gewürzmischung Hello Souflaki", "quantity": 4, "unit": "g"},
                {"name": "Buttermilch-Zitronen-Dressing", "quantity": 100, "unit": "ml"}
            ],
            "steps": [
                {"step_number": 1, "description": "Gemüse schneiden: Gurke in Halbmonde, Tomate in Spalten, Zwiebel in Streifen. Knoblauch abziehen.", "duration_min": 5},
                {"step_number": 2, "description": "Hirtenkäse marinieren: Käse in Würfel schneiden, in Olivenöl und Hello Souflaki Gewürz marinieren.", "duration_min": 3},
                {"step_number": 3, "description": "Dinkel anbraten: Zwiebel, Oregano und Knoblauch 1-2 Min. anbraten. Dinkel und restliches Gewürz zugeben, 3-5 Min. braten.", "duration_min": 7},
                {"step_number": 4, "description": "Fertigstellen: Dinkel und Dressing zum Salat geben.", "duration_min": 2},
                {"step_number": 5, "description": "Anrichten: Dinkel-Salat auf Teller verteilen, mit mariniertem Hirtenkäse toppen.", "duration_min": None}
            ]
        },
        {
            "name": "Grillkäse-Wraps mit Aioli",
            "kcal_per_serving": 887,
            "active_cooking_time_min": 20,
            "total_time_min": 25,
            "tags": ["Vegetarisch", "Schnell"],
            "ingredients": [
                {"name": "Grillkäse Zypriotischer Art", "quantity": 200, "unit": "g"},
                {"name": "Weizentortillas", "quantity": 200, "unit": "g"},
                {"name": "rote Chilischote", "quantity": 0.5, "unit": "Stück"},
                {"name": "rote Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Gurke", "quantity": 0.5, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Mayonnaise", "quantity": 25, "unit": "g"},
                {"name": "Oregano", "quantity": 2, "unit": "g"},
                {"name": "Zitrone", "quantity": 0.5, "unit": "Stück"},
                {"name": "Rucola", "quantity": 50, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Gurke würfeln, Zitrone in Spalten schneiden. Grillkäse in Stäbchen schneiden.", "duration_min": 5},
                {"step_number": 2, "description": "Zwiebel und Chili schneiden: Zwiebel in Streifen. Knoblauch mit Salz zu Paste zerdrücken. Chili in feine Streifen.", "duration_min": 5},
                {"step_number": 3, "description": "Zwiebeln karamellisieren: Zwiebeln 10 Min. braten. Essig, Zucker, Wasser zugeben und 4-5 Min. braten.", "duration_min": 15},
                {"step_number": 4, "description": "Grillkäse marinieren: Mit Oregano und Öl marinieren. Aioli aus Mayo und Knoblauchpaste mischen.", "duration_min": 3},
                {"step_number": 5, "description": "Grillkäse braten: Käsesticks 3-4 Min. rundherum braten.", "duration_min": 4},
                {"step_number": 6, "description": "Anrichten: Tortillas erwärmen, mit Aioli bestreichen, mit Rucola, Zwiebeln, Käse und Gurke belegen.", "duration_min": None}
            ]
        },
        {
            "name": "Mini-Tortillas mit Kartoffeln, Chorizo und Salsa Verde",
            "kcal_per_serving": 1078,
            "active_cooking_time_min": 15,
            "total_time_min": 35,
            "tags": ["Tacos", "Fleisch", "Kartoffeln"],
            "ingredients": [
                {"name": "Weizentortillas", "quantity": 200, "unit": "g"},
                {"name": "Chorizo", "quantity": 120, "unit": "g"},
                {"name": "Kartoffeln", "quantity": 400, "unit": "g"},
                {"name": "Spitzpaprika", "quantity": 1, "unit": "Stück"},
                {"name": "Jalapeño", "quantity": 1, "unit": "Stück"},
                {"name": "Passionsfrucht", "quantity": 1, "unit": "Stück"},
                {"name": "Frühlingszwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Koriander", "quantity": 20, "unit": "g"},
                {"name": "Crème fraîche", "quantity": 100, "unit": "g"},
                {"name": "Smoky Paprika", "quantity": 3, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Rösten: Kartoffeln und Chorizo in Würfel schneiden. Mit Smoky Paprika und Öl 25-30 Min. im Ofen backen.", "duration_min": 30},
                {"step_number": 2, "description": "Vorbereitung: Passionsfrucht auskratzen, Paprika in Ringe, Kräuter hacken, Frühlingszwiebel und Jalapeño schneiden.", "duration_min": 5},
                {"step_number": 3, "description": "Topping: Paprika, halbe Frühlingszwiebel, Passionsfrucht, halbe Jalapeño, viertel Kräuter mit Essig und Öl marinieren.", "duration_min": 5},
                {"step_number": 4, "description": "Salsa Verde: Crème fraîche, restliche Jalapeño, Kräuter, Frühlingszwiebel und Essig pürieren.", "duration_min": 5},
                {"step_number": 5, "description": "Tortillas aufwärmen: In Pfanne 1-2 Min. rösten.", "duration_min": 2},
                {"step_number": 6, "description": "Anrichten: Tortillas mit Kartoffeln, Chorizo und Topping füllen.", "duration_min": None}
            ]
        },
        {
            "name": "Hähnchengeschnetzeltes mit Madras-Curry und Reis",
            "kcal_per_serving": 682,
            "active_cooking_time_min": 20,
            "total_time_min": 30,
            "tags": ["Fleisch", "Reis", "Viel Gemüse"],
            "ingredients": [
                {"name": "Hähnchengeschnetzeltes mariniert", "quantity": 250, "unit": "g"},
                {"name": "Basmatireis", "quantity": 150, "unit": "g"},
                {"name": "Hühnerbrühepulver", "quantity": 8, "unit": "g"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "rote Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Minze", "quantity": 10, "unit": "g"},
                {"name": "gelbe Currypaste", "quantity": 25, "unit": "g"},
                {"name": "Naturjoghurt", "quantity": 75, "unit": "g"},
                {"name": "Aprikosenchutney", "quantity": 25, "unit": "g"},
                {"name": "Madras-Curry-Pulver", "quantity": 2, "unit": "g"},
                {"name": "Erdnüsse gesalzen", "quantity": 20, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Zwiebel in Streifen und Würfel. Karotten in Halbmonde. Wasser, Brühepulver anrühren.", "duration_min": 5},
                {"step_number": 2, "description": "Zwiebel braten: Zwiebelstreifen, Balsamicoessig und Zucker 3-4 Min. karamellisieren.", "duration_min": 4},
                {"step_number": 3, "description": "Reis ansetzen: Fleisch, Zwiebelwürfel, Karotten 3-4 Min. anbraten. Currypaste und Madras Curry zugeben. Reis und Brühe zugeben, 12 Min. köcheln.", "duration_min": 17},
                {"step_number": 4, "description": "Dip: Joghurt, Chutney, gehackte Minze verrühren. Erdnüsse hacken.", "duration_min": 5},
                {"step_number": 5, "description": "Reis fertigstellen: Reis 10 Min. abgedeckt ziehen lassen.", "duration_min": 10},
                {"step_number": 6, "description": "Anrichten: Reispfanne verteilen, mit Zwiebeln, Erdnüssen und Joghurt toppen.", "duration_min": None}
            ]
        },
        {
            "name": "Brokkoli-Kartoffelsuppe mit Knoblauchbrot",
            "kcal_per_serving": 791,
            "active_cooking_time_min": 15,
            "total_time_min": 35,
            "tags": ["Kartoffeln", "Vegetarisch", "Viel Gemüse"],
            "ingredients": [
                {"name": "Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Gemüsebrühepulver", "quantity": 8, "unit": "g"},
                {"name": "Crème fraîche", "quantity": 100, "unit": "g"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Gewürzmischung Hello Muskat", "quantity": 2.5, "unit": "g"},
                {"name": "Petersilie", "quantity": 10, "unit": "g"},
                {"name": "Pinienkerne", "quantity": 10, "unit": "g"},
                {"name": "Brokkoli", "quantity": 1, "unit": "Stück"},
                {"name": "Ofenkartoffel", "quantity": 150, "unit": "g"},
                {"name": "Ciabattabrötchen", "quantity": 1, "unit": "Stück"},
                {"name": "Gouda gerieben", "quantity": 75, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Wasser kochen. Zwiebel würfeln, Kartoffel in Würfel schneiden, Brokkoli in Röschen.", "duration_min": 10},
                {"step_number": 2, "description": "Brot aufbacken: Ciabatta in Scheiben schneiden. Käse-Petersilien-Knoblauch-Mix auflegen, 6-8 Min. backen.", "duration_min": 8},
                {"step_number": 3, "description": "Pinienkerne: 1-2 Min. rösten.", "duration_min": 2},
                {"step_number": 4, "description": "Suppe kochen: Zwiebel, Kartoffeln, Brokkoli 2-3 Min. anschwitzen. Wasser, Brühe und Muskat zufügen, 15 Min. köcheln.", "duration_min": 18},
                {"step_number": 5, "description": "Pürieren: Crème fraîche zugeben und cremig pürieren. Mit Zitronensaft abschmecken.", "duration_min": 5},
                {"step_number": 6, "description": "Anrichten: Suppe mit restlichem Käse und Pinienkernen toppen. Mit Brot servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Hirtenkäseschiffchen mit Grillbrot und Tzatziki",
            "kcal_per_serving": 797,
            "active_cooking_time_min": 20,
            "total_time_min": 40,
            "tags": ["Vegetarisch", "Gesund"],
            "ingredients": [
                {"name": "Sauerteig", "quantity": 300, "unit": "g"},
                {"name": "Hirtenkäse", "quantity": 200, "unit": "g"},
                {"name": "Spitzpaprika", "quantity": 1, "unit": "Stück"},
                {"name": "Salatgurke", "quantity": 1, "unit": "Stück"},
                {"name": "Tomate", "quantity": 1, "unit": "Stück"},
                {"name": "rote Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Minze", "quantity": 10, "unit": "g"},
                {"name": "Naturjoghurt", "quantity": 150, "unit": "g"},
                {"name": "Oregano", "quantity": 1, "unit": "g"},
                {"name": "Hello Paprika", "quantity": 2, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Hirtenkäse: Aus Alufolie Schiffchen formen. Paprika, Hirtenkäse einlegen. Mit Gewürzen toppen.", "duration_min": 5},
                {"step_number": 2, "description": "Salat: Tomaten, Zwiebel, Kräuter vermengen. Zwiebel vorher anbraten.", "duration_min": 7},
                {"step_number": 3, "description": "Grillbrot: Sauerteig zerteilen, zu Rechteck formen. Im Ofen 15-18 Min. mit Käseschiffchen backen.", "duration_min": 18},
                {"step_number": 4, "description": "Tzatziki: Gurke raspeln, mit Joghurt, Kräutern, Knoblauch, Essig, Honig vermengen.", "duration_min": 5},
                {"step_number": 5, "description": "Anrichten: Grillbrot mit Knoblauch einreiben. Alles zusammen servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Teriyaki-Aubergine mit Reis und Edamame",
            "kcal_per_serving": 626,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Reis", "Vegetarisch", "Viel Gemüse", "Gesund"],
            "ingredients": [
                {"name": "Basmatireis", "quantity": 150, "unit": "g"},
                {"name": "Aubergine", "quantity": 1, "unit": "Stück"},
                {"name": "Edamame", "quantity": 50, "unit": "g"},
                {"name": "Gurke", "quantity": 0.5, "unit": "Stück"},
                {"name": "rote Chilischote", "quantity": 1, "unit": "Stück"},
                {"name": "Limette", "quantity": 1, "unit": "Stück"},
                {"name": "Teriyakisoße", "quantity": 50, "unit": "ml"},
                {"name": "vegane Mayonnaise", "quantity": 25, "unit": "g"},
                {"name": "Sesamöl", "quantity": 10, "unit": "ml"},
                {"name": "Sriracha Sauce", "quantity": 8, "unit": "ml"},
                {"name": "Sweet Chili Soße", "quantity": 50, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Reis kochen: Reis in Salzwasser 10 Min. köcheln lassen. Sesamöl und Edamame zugeben, 10 Min. ziehen lassen.", "duration_min": 20},
                {"step_number": 2, "description": "Aubergine backen: Aubergine in Ecken schneiden. Mit Teriyakisoße, Limettensaft und Öl marinieren. 15-20 Min. backen.", "duration_min": 20},
                {"step_number": 3, "description": "Gurkensalat: Gurke hobeln, mit Sweet-Chili-Soße, Limettensaft, Abrieb und Zucker marinieren.", "duration_min": 5},
                {"step_number": 4, "description": "Toppings: Mayo, Sriracha, Limettensaft verrühren. Zweiter Dip: Sweet-Chili-Soße mit Limettensaft verrühren.", "duration_min": 3},
                {"step_number": 5, "description": "Anrichten: Reis auflockern, mit Aubergine und Gurkensalat anrichten. Mit Dips und Chili toppen.", "duration_min": None}
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
