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
            "name": "Krosser Bacon-Kartoffel-Salat mit Aioli",
            "kcal_per_serving": 871,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Fleisch", "Kartoffeln", "Schnell"],
            "ingredients": [
                {"name": "Bacon (Scheiben)", "quantity": 125, "unit": "g"},
                {"name": "vorgegarte Kartoffelwürfel", "quantity": 400, "unit": "g"},
                {"name": "Salatherz (Romana)", "quantity": 1, "unit": "Stück"},
                {"name": "Aioli", "quantity": 60, "unit": "g"},
                {"name": "mittelscharfer Senf", "quantity": 10, "unit": "ml"},
                {"name": "Naturjoghurt", "quantity": 75, "unit": "g"},
                {"name": "Worcester Sauce", "quantity": 8, "unit": "ml"},
                {"name": "Hartkäse gerieben", "quantity": 20, "unit": "g"},
                {"name": "Tomate", "quantity": 1, "unit": "Stück"},
                {"name": "kleine Salatgurke", "quantity": 1, "unit": "Stück"},
                {"name": "Zitrone", "quantity": 1, "unit": "Stück"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Zitrone für Limonade schneiden. Gurke und Tomaten in Spalten/Monde. Salat in Streifen.", "duration_min": 5},
                {"step_number": 2, "description": "Limonade: Zitronensaft, Wasser und Zucker pürieren. Kaltstellen.", "duration_min": 3},
                {"step_number": 3, "description": "Kartoffeln braten: Kartoffelwürfel 7-8 Min. anbraten, salzen, pfeffern.", "duration_min": 10},
                {"step_number": 4, "description": "Dressing: Senf, Aioli, Joghurt, Worcester Sauce, Käse, Öl, Essig verrühren.", "duration_min": 3},
                {"step_number": 5, "description": "Bacon braten: Bacon 1-2 Min. je Seite kross braten.", "duration_min": 3},
                {"step_number": 6, "description": "Anrichten: Salat mit Kartoffeln, Dressing, Gurke, Tomate und Bacon anrichten.", "duration_min": None}
            ]
        },
        {
            "name": "Honig-Senf-Ofengemüse mit Ziegenkäsetalern",
            "kcal_per_serving": 560,
            "active_cooking_time_min": 10,
            "total_time_min": 35,
            "tags": ["Vegetarisch", "Viel Gemüse", "Kartoffeln", "Gesund"],
            "ingredients": [
                {"name": "Kartoffeln (Drillinge)", "quantity": 400, "unit": "g"},
                {"name": "Kohlrabi", "quantity": 1, "unit": "Stück"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "Ziegenfrischkäsetaler", "quantity": 125, "unit": "g"},
                {"name": "Blattsalatmischung", "quantity": 75, "unit": "g"},
                {"name": "Sonnenblumenkerne", "quantity": 20, "unit": "g"},
                {"name": "mittelscharfer Senf", "quantity": 10, "unit": "ml"},
                {"name": "Sahnejoghurt", "quantity": 75, "unit": "g"},
                {"name": "Schnittlauch/Thymian", "quantity": 10, "unit": "g"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Backofen vorheizen. Kräuter hacken.", "duration_min": 3},
                {"step_number": 2, "description": "Gemüse schneiden: Kohlrabi, Karotten und Drillinge in Stücke/Scheiben schneiden. Knoblauch abziehen.", "duration_min": 8},
                {"step_number": 3, "description": "Gemüse backen: Gemüse mit Öl, Knoblauch, Salz, Pfeffer mischen. 25-30 Min. backen. Sonnenblumenkerne in den letzten 5 Min. dazugeben.", "duration_min": 30},
                {"step_number": 4, "description": "Dip & Dressing: Joghurt, Senf, Honig verrühren. Für Salat mit Essig und Öl strecken. Rest mit Thymian mischen.", "duration_min": 5},
                {"step_number": 5, "description": "Anrichten: Salat anrichten. Ziegenkäse in Kernen wenden. Mit Kartoffeln, Gemüse und Dip servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Curry Peanut Noodles mit Spinat",
            "kcal_per_serving": 1135,
            "active_cooking_time_min": 20,
            "total_time_min": 30,
            "tags": ["Pasta", "Vegetarisch"],
            "ingredients": [
                {"name": "Fettuccine", "quantity": 270, "unit": "g"},
                {"name": "Babyspinat", "quantity": 50, "unit": "g"},
                {"name": "Paprika multicolor", "quantity": 1, "unit": "Stück"},
                {"name": "rote Chilischote", "quantity": 1, "unit": "Stück"},
                {"name": "Limette", "quantity": 1, "unit": "Stück"},
                {"name": "Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch & Ingwer in Öl", "quantity": 30, "unit": "g"},
                {"name": "Kokosmilch", "quantity": 250, "unit": "ml"},
                {"name": "Erdnussbutter", "quantity": 40, "unit": "g"},
                {"name": "Erdnüsse gesalzen", "quantity": 25, "unit": "g"},
                {"name": "Madras-Curry-Pulver", "quantity": 4, "unit": "g"},
                {"name": "Gemüsebrühepulver", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Nudeln: Fettuccine 11-12 Min. kochen, Kochwasser auffangen.", "duration_min": 15},
                {"step_number": 2, "description": "Vorbereitung: Paprika, Chili und Zwiebel schneiden. Limette vierteln.", "duration_min": 5},
                {"step_number": 3, "description": "Erdnüsse kandieren: Erdnüsse mit Hälfte Chili, Öl, Zucker anbraten.", "duration_min": 3},
                {"step_number": 4, "description": "Soße: Ingwer-Knoblauch, Zwiebel, Chili anbraten. Madras-Curry, Brühe, Erdnussbutter zufügen. Mit Limettensaft, Kokosmilch und Kochwasser ablöschen.", "duration_min": 6},
                {"step_number": 5, "description": "Vollenden: Spinat und Nudeln in die Soße geben.", "duration_min": 3},
                {"step_number": 6, "description": "Anrichten: Mit kandierten Erdnüssen toppen.", "duration_min": None}
            ]
        },
        {
            "name": "Tomaten-Paprika-Suppe mit Käse-Ciabatta",
            "kcal_per_serving": 803,
            "active_cooking_time_min": 15,
            "total_time_min": 35,
            "tags": ["Vegetarisch", "Gesund"],
            "ingredients": [
                {"name": "Ciabatta-Brot", "quantity": 250, "unit": "g"},
                {"name": "Mozzarella", "quantity": 125, "unit": "g"},
                {"name": "rote Spitzpaprika", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Basilikum", "quantity": 10, "unit": "g"},
                {"name": "Crème fraîche", "quantity": 75, "unit": "g"},
                {"name": "Hartkäse geraspelt", "quantity": 20, "unit": "g"},
                {"name": "milder Chili-Mix", "quantity": 2, "unit": "g"},
                {"name": "Gemüsebrühepulver", "quantity": 4, "unit": "g"},
                {"name": "Gehackte Tomaten mit Knoblauch", "quantity": 390, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Brot: Ciabatta 8-10 Min. aufbacken.", "duration_min": 10},
                {"step_number": 2, "description": "Suppe ansetzen: Paprika anbraten. Mit Tomaten und Brühe ablöschen. 10-15 Min. köcheln.", "duration_min": 20},
                {"step_number": 3, "description": "Brot überbacken: Knoblauch hacken, Mozzarella schneiden. Ciabatta mit Knoblauch und Öl einreiben, mit Käse 3 Min. überbacken.", "duration_min": 5},
                {"step_number": 4, "description": "Suppe pürieren: Crème fraîche einrühren und Suppe pürieren.", "duration_min": 3},
                {"step_number": 5, "description": "Anrichten: Suppe mit Hartkäse und Basilikum bestreuen. Mit Ciabatta servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Harissa-Hack auf Ciabatta mit Salat",
            "kcal_per_serving": 542,
            "active_cooking_time_min": 20,
            "total_time_min": 30,
            "tags": ["Fleisch", "Schnell"],
            "ingredients": [
                {"name": "Rinderhackfleischzubereitung", "quantity": 200, "unit": "g"},
                {"name": "Ciabattabrötchen", "quantity": 150, "unit": "g"},
                {"name": "Blattsalatmischung", "quantity": 50, "unit": "g"},
                {"name": "Frühlingszwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Minze/Petersilie", "quantity": 10, "unit": "g"},
                {"name": "Tomatensugo", "quantity": 200, "unit": "g"},
                {"name": "Naturjoghurt", "quantity": 100, "unit": "g"},
                {"name": "Hello Harissa", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Hack anbraten: Hackfleisch, weiße Frühlingszwiebel und Hello Harissa 3-4 Min. braten.", "duration_min": 5},
                {"step_number": 2, "description": "Soße: Tomatensugo zufügen, 2-3 Min. köchelnlassen.", "duration_min": 5},
                {"step_number": 3, "description": "Dip: Joghurt, grüne Frühlingszwiebel, Hälfte der Kräuter, Essig verrühren. Salat mit etwas Dip mischen.", "duration_min": 5},
                {"step_number": 4, "description": "Brötchen: Brötchenhälften 1-2 Min. rösten.", "duration_min": 3},
                {"step_number": 5, "description": "Anrichten: Hackfleischsoße, Salat und Brötchen anrichten. Mit Rest Dip und Kräutern garnieren.", "duration_min": None}
            ]
        },
        {
            "name": "Schweinelachssteaks mit Ofenkartoffeln und Zaziki",
            "kcal_per_serving": 605,
            "active_cooking_time_min": 20,
            "total_time_min": 35,
            "tags": ["Fleisch", "Kartoffeln", "Gesund"],
            "ingredients": [
                {"name": "Schweinelachssteaks", "quantity": 250, "unit": "g"},
                {"name": "Ofenkartoffel", "quantity": 250, "unit": "g"},
                {"name": "Hirtenkäse", "quantity": 100, "unit": "g"},
                {"name": "Gurke", "quantity": 1, "unit": "Stück"},
                {"name": "rote Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Tomate", "quantity": 1, "unit": "Stück"},
                {"name": "Naturjoghurt", "quantity": 100, "unit": "g"},
                {"name": "Dill/Petersilie", "quantity": 10, "unit": "g"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Hello Paprika", "quantity": 4, "unit": "g"},
                {"name": "Hello Buon Appetito", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Kartoffeln: Kartoffeln vierteln, mit Paprika und Öl 25-30 Min. backen.", "duration_min": 30},
                {"step_number": 2, "description": "Salat: Gurke, Tomate, Zwiebel stückeln. Hirtenkäse zerbröseln. Mit Kräutern, Essig, Öl mischen.", "duration_min": 5},
                {"step_number": 3, "description": "Zaziki: Gurke reiben, ausdrücken. Mit Joghurt, Dill und Knoblauch mischen.", "duration_min": 5},
                {"step_number": 4, "description": "Vorbereitung Fleisch: Fleisch in Streifen, mit Hello Buon Appetito marinieren. Zwiebel marinieren.", "duration_min": 5},
                {"step_number": 5, "description": "Fleisch braten: Fleisch 4-6 Min. scharf anbraten.", "duration_min": 6},
                {"step_number": 6, "description": "Anrichten: Fleisch mit Kartoffeln, Salat und Zaziki servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Linguine mit Brokkoli, Kokos und Panko",
            "kcal_per_serving": 829,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Pasta", "Vegetarisch", "Viel Gemüse"],
            "ingredients": [
                {"name": "frische Linguine", "quantity": 250, "unit": "g"},
                {"name": "Porree", "quantity": 0.5, "unit": "Stück"},
                {"name": "Brokkoli", "quantity": 1, "unit": "Stück"},
                {"name": "rote Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Zitrone", "quantity": 1, "unit": "Stück"},
                {"name": "Kokosmilch", "quantity": 250, "unit": "ml"},
                {"name": "Hefeflocken", "quantity": 5, "unit": "g"},
                {"name": "Panko-Mehl", "quantity": 12.5, "unit": "g"},
                {"name": "Kampot-Pfeffer", "quantity": 1, "unit": "g"},
                {"name": "Hello Smoky Paprika", "quantity": 3, "unit": "g"},
                {"name": "Gemüsebrühepulver", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Topping: Panko, Knoblauch und Kampot-Pfeffer 1-2 Min. rösten.", "duration_min": 5},
                {"step_number": 2, "description": "Pasta & Brokkoli: Brokkoli 6 Min. in Wasser garen, in den letzten 3 Min. Linguine zugeben.", "duration_min": 10},
                {"step_number": 3, "description": "Soße: Zwiebel und Porree 3-4 Min. braten. Knoblauch und Smoky Paprika 1 Min. mitrösten. Mit Kokosmilch und Brühe ablöschen.", "duration_min": 8},
                {"step_number": 4, "description": "Vollenden: Linguine, Hefeflocken, Zitronensaft in die Soße geben.", "duration_min": 2},
                {"step_number": 5, "description": "Anrichten: Mit Topping bestreuen.", "duration_min": None}
            ]
        },
        {
            "name": "Pilz-Stroganoff mit Reis",
            "kcal_per_serving": 583,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Vegetarisch", "Reis"],
            "ingredients": [
                {"name": "Basmatireis", "quantity": 150, "unit": "g"},
                {"name": "Portobello-Pilze", "quantity": 200, "unit": "g"},
                {"name": "braune Champignons", "quantity": 150, "unit": "g"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "Babyspinat", "quantity": 100, "unit": "g"},
                {"name": "Petersilie", "quantity": 10, "unit": "g"},
                {"name": "Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Sojasoße", "quantity": 25, "unit": "ml"},
                {"name": "Hello Paprika", "quantity": 4, "unit": "g"},
                {"name": "Gemüsebrühepulver", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Reis: Karotte raspeln. Mit Reis in Butter anschwitzen, mit Wasser 10 Min. köcheln.", "duration_min": 15},
                {"step_number": 2, "description": "Pilze braten: Zwiebel 3-4 Min. braten. Pilze und Knoblauch 5-8 Min. mitbraten. Hello Paprika zugeben.", "duration_min": 12},
                {"step_number": 3, "description": "Stroganoff vollenden: Kochsahne, Sojasoße, Brühe zugeben. Spinat einrühren.", "duration_min": 5},
                {"step_number": 4, "description": "Anrichten: Reis mit Petersilie mischen, Stroganoff dazu anrichten.", "duration_min": None}
            ]
        },
        {
            "name": "Conchiglie in cremiger Tomatensoße",
            "kcal_per_serving": 597,
            "active_cooking_time_min": 10,
            "total_time_min": 15,
            "tags": ["Pasta", "Vegetarisch", "Schnell"],
            "ingredients": [
                {"name": "vorgekochte Conchiglie", "quantity": 400, "unit": "g"},
                {"name": "Babyspinat", "quantity": 50, "unit": "g"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "Schalotte", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Basilikum", "quantity": 10, "unit": "g"},
                {"name": "Tomatenpesto", "quantity": 50, "unit": "g"},
                {"name": "Frischecreme", "quantity": 100, "unit": "g"},
                {"name": "Hartkäse gerieben", "quantity": 20, "unit": "g"},
                {"name": "Gemüsebrühepulver", "quantity": 6, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Karotte schälen. Schalotte, Knoblauch, Basilikum schneiden.", "duration_min": 5},
                {"step_number": 2, "description": "Soße: Schalotte und Knoblauch 1-2 Min. braten. Karotte reinraspeln. Mit Wasser und Brühe ablöschen.", "duration_min": 5},
                {"step_number": 3, "description": "Pasta fertigstellen: Frischecreme und Pesto einrühren. Spinat und Pasta unterheben, 2 Min. köcheln.", "duration_min": 4},
                {"step_number": 4, "description": "Anrichten: Mit Basilikum und Käse garnieren.", "duration_min": None}
            ]
        },
        {
            "name": "Hähnchen-Couscous mit Slaw und Avocado",
            "kcal_per_serving": 985,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Fleisch", "Schnell"],
            "ingredients": [
                {"name": "Couscous", "quantity": 150, "unit": "g"},
                {"name": "Coleslaw-Mix", "quantity": 200, "unit": "g"},
                {"name": "Hähnchengeschnetzeltes", "quantity": 250, "unit": "g"},
                {"name": "Naturjoghurt", "quantity": 100, "unit": "g"},
                {"name": "Hühnerbrühepulver", "quantity": 4, "unit": "g"},
                {"name": "Sweet Chili Soße", "quantity": 25, "unit": "g"},
                {"name": "Koriander/Minze", "quantity": 10, "unit": "g"},
                {"name": "Avocado", "quantity": 1, "unit": "Stück"},
                {"name": "Limette", "quantity": 1, "unit": "Stück"}
            ],
            "steps": [
                {"step_number": 1, "description": "Couscous & Slaw: Couscous mit Brühe und Wasser quellen lassen. Slaw mit heißem Wasser übergießen, abgießen.", "duration_min": 8},
                {"step_number": 2, "description": "Limonade: Limettensaft, Minze, Zucker, Wasser mixen.", "duration_min": 3},
                {"step_number": 3, "description": "Dressing: Sweet Chili Soße, Limettensaft, Joghurt, Öl verrühren.", "duration_min": 2},
                {"step_number": 4, "description": "Fleisch: Hähnchen 3 Min. braten.", "duration_min": 4},
                {"step_number": 5, "description": "Anrichten: Couscous (mit Butter) und Slaw anrichten. Fleisch, Avocado, Koriander dazugeben. Dressing drüberträufeln.", "duration_min": None}
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
