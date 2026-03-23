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
            "name": "Paccheri in würziger Paprika-Rahmsoße",
            "kcal_per_serving": 727,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Pasta", "Vegetarisch"],
            "ingredients": [
                {"name": "frische Paccheri", "quantity": 375, "unit": "g"},
                {"name": "rote Spitzpaprika", "quantity": 1, "unit": "Stück"},
                {"name": "Babyspinat", "quantity": 50, "unit": "g"},
                {"name": "rote Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Soja-Kochcrème", "quantity": 125, "unit": "g"},
                {"name": "Tomatenmark", "quantity": 35, "unit": "g"},
                {"name": "Ajvar", "quantity": 25, "unit": "g"},
                {"name": "Balsamicoessig", "quantity": 12, "unit": "ml"},
                {"name": "Hello Piri-Piri", "quantity": 4, "unit": "g"},
                {"name": "Hello Paprika", "quantity": 2, "unit": "g"},
                {"name": "Gemüsebrühepulver", "quantity": 6, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Backofen vorheizen. Paprika und Zwiebel in Würfel. Knoblauch abziehen.", "duration_min": 5},
                {"step_number": 2, "description": "Gemüse backen: Paprika, Zwiebel und Knoblauch mit Öl und Hello Paprika 15 Min. backen.", "duration_min": 15},
                {"step_number": 3, "description": "Pasta: Paccheri 4-5 Min. bissfest garen. Spinat mit Balsamico und Öl mischen.", "duration_min": 6},
                {"step_number": 4, "description": "Soße: Gebackenes Gemüse mit Brühe, Ajvar, Soja-Kochcrème, Tomatenmark, Hello Piri Piri und Rest Balsamico pürieren.", "duration_min": 4},
                {"step_number": 5, "description": "Vollenden: Soße in Topf geben, mit Paccheri vermengen.", "duration_min": 2},
                {"step_number": 6, "description": "Anrichten: Pasta verteilen, mit Spinatsalat toppen.", "duration_min": None}
            ]
        },
        {
            "name": "Sigara Börek mit Bulgursalat",
            "kcal_per_serving": 975,
            "active_cooking_time_min": 20,
            "total_time_min": 35,
            "tags": ["Vegetarisch"],
            "ingredients": [
                {"name": "Filoteig", "quantity": 150, "unit": "g"},
                {"name": "Hirtenkäse", "quantity": 100, "unit": "g"},
                {"name": "Bulgur", "quantity": 150, "unit": "g"},
                {"name": "Paprika multicolor", "quantity": 1, "unit": "Stück"},
                {"name": "Gurke", "quantity": 0.5, "unit": "Stück"},
                {"name": "Frühlingszwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Petersilie", "quantity": 10, "unit": "g"},
                {"name": "Zitrone", "quantity": 1, "unit": "Stück"},
                {"name": "Sahnejoghurt", "quantity": 75, "unit": "g"},
                {"name": "Tomatenmark", "quantity": 35, "unit": "g"},
                {"name": "Kumin", "quantity": 1, "unit": "g"},
                {"name": "Gemüsebrühepulver", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Bulgur: In Brühe und Kumin aufkochen, 15 Min. köcheln. Tomatenmark einrühren, ziehen lassen.", "duration_min": 20},
                {"step_number": 2, "description": "Vorbereitung: Paprika und Gurke in Würfel. Frühlingszwiebel in Ringe. Petersilie hacken.", "duration_min": 5},
                {"step_number": 3, "description": "Hirtenkäse: Zerbröseln, mit Petersilie und grüner Frühlingszwiebel mischen.", "duration_min": 3},
                {"step_number": 4, "description": "Börek: Filoteig in Dreiecke schneiden. Käsemischung darauf, zu Röllchen aufrollen.", "duration_min": 10},
                {"step_number": 5, "description": "Braten: Börek in Öl rundherum 30-60 Sek. knusprig braten.", "duration_min": 4},
                {"step_number": 6, "description": "Anrichten: Bulgursalat mischen mit Gemüse und Zitronensaft. Dip aus Sahnejoghurt anrühren. Anrichten.", "duration_min": None}
            ]
        },
        {
            "name": "Hähnchen-Curry mit Buschbohnen",
            "kcal_per_serving": 701,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Fleisch", "Reis"],
            "ingredients": [
                {"name": "Hähnchenbrustfilet in Lake", "quantity": 250, "unit": "g"},
                {"name": "Basmatireis", "quantity": 150, "unit": "g"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "Buschbohnen", "quantity": 150, "unit": "g"},
                {"name": "Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Tomatenmark", "quantity": 35, "unit": "g"},
                {"name": "Mandeln gehobelt", "quantity": 10, "unit": "g"},
                {"name": "Hello Curry", "quantity": 2, "unit": "g"},
                {"name": "Hühnerbrühepulver", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Reis: Karotte raspeln. Mit Reis in Wasser 10 Min. köcheln, 10 Min ziehen lassen.", "duration_min": 20},
                {"step_number": 2, "description": "Bohnen: Enden abschneiden. Bohnen in Salzwasser 9-10 Min. kochen, mit Butter mischen.", "duration_min": 15},
                {"step_number": 3, "description": "Mandeln & Hähnchen: Mandeln rösten. Hähnchen 2-3 Min. je Seite anbraten, dann herausnehmen.", "duration_min": 6},
                {"step_number": 4, "description": "Soße: Zwiebelstreifen glasig dünsten. Tomatenmark anrösten. Mit Sahne und Wasser ablöschen, Brühe und Curry einrühren.", "duration_min": 5},
                {"step_number": 5, "description": "Vollenden: Hähnchen in der Soße 5-7 Min. fertig köcheln.", "duration_min": 7},
                {"step_number": 6, "description": "Anrichten: Reis, Bohnen, Hähnchen anrichten. Mit Mandelblättchen toppen.", "duration_min": None}
            ]
        },
        {
            "name": "Beef Udon mit Pak Choi",
            "kcal_per_serving": 746,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Pasta", "Fleisch", "Schnell"],
            "ingredients": [
                {"name": "Rinderhackfleischzubereitung", "quantity": 200, "unit": "g"},
                {"name": "Udon-Nudeln", "quantity": 440, "unit": "g"},
                {"name": "Pak Choi", "quantity": 200, "unit": "g"},
                {"name": "Champignons", "quantity": 100, "unit": "g"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Sojasoße", "quantity": 25, "unit": "ml"},
                {"name": "Sweet Chili Soße", "quantity": 50, "unit": "ml"},
                {"name": "Sesamsamen", "quantity": 25, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Pak Choi in Streifen. Champignons in Scheiben.", "duration_min": 3},
                {"step_number": 2, "description": "Gemüse braten: Champignons und Pak Choi in Öl 4-5 Min. anbraten.", "duration_min": 5},
                {"step_number": 3, "description": "Hack anbraten: Hackfleisch 4-5 Min. krümelig braten.", "duration_min": 5},
                {"step_number": 4, "description": "Vollenden: Hack und Knoblauch zum Gemüse geben. Sojasoße, Sweet Chili Soße, Zucker und Essig einrühren.", "duration_min": 2},
                {"step_number": 5, "description": "Nudeln: Udon-Nudeln zugeben und 2 Min. erhitzen.", "duration_min": 3},
                {"step_number": 6, "description": "Anrichten: Beef Udon anrichten und mit Sesam garnieren.", "duration_min": None}
            ]
        },
        {
            "name": "Smashed Potatoes mit Jalapeño-Käsesoße",
            "kcal_per_serving": 854,
            "active_cooking_time_min": 15,
            "total_time_min": 30,
            "tags": ["Kartoffeln", "Vegetarisch"],
            "ingredients": [
                {"name": "Kartoffeln (Drillinge)", "quantity": 600, "unit": "g"},
                {"name": "Avocado", "quantity": 1, "unit": "Stück"},
                {"name": "Tomate", "quantity": 1, "unit": "Stück"},
                {"name": "Jalapeño", "quantity": 1, "unit": "Stück"},
                {"name": "rote Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Limette", "quantity": 1, "unit": "Stück"},
                {"name": "Koriander", "quantity": 10, "unit": "g"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Gouda gerieben", "quantity": 75, "unit": "g"},
                {"name": "Hello Patatas", "quantity": 4, "unit": "g"},
                {"name": "Gemüsebrühepulver", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Kartoffeln: Drillinge 12-15 Min. in Salzwasser garen. Auf Blech verteilen und platt drücken. Mit Hello Patatas und Öl 6-8 Min. knusprig backen.", "duration_min": 25},
                {"step_number": 2, "description": "Salsa: Tomatenwürfel, Koriander, Hälfte Zwiebel, Limettensaft, Öl mischen.", "duration_min": 5},
                {"step_number": 3, "description": "Käsesoße: Rest Zwiebel, Knoblauch, Jalapeño 2-3 Min. anschwitzen. Kochsahne, Wasser, Brühe und Rest Hello Patatas einrühren. Gouda darin schmelzen.", "duration_min": 6},
                {"step_number": 4, "description": "Anrichten: Kartoffeln mit Käsesoße toppen. Avocado in Würfel. Mit Salsa und Avocado servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Hähnchenbrust aus dem Ofen mit Senfbröseln",
            "kcal_per_serving": 677,
            "active_cooking_time_min": 15,
            "total_time_min": 35,
            "tags": ["Fleisch", "Kartoffeln", "Gesund"],
            "ingredients": [
                {"name": "Hähnchenbrustfilet in Lake", "quantity": 250, "unit": "g"},
                {"name": "Kartoffeln (Drillinge)", "quantity": 400, "unit": "g"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "Babyspinat", "quantity": 75, "unit": "g"},
                {"name": "Schalotte", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "körniger Senf", "quantity": 17, "unit": "g"},
                {"name": "Panko-Mehl", "quantity": 25, "unit": "g"},
                {"name": "Hühnerbrühepulver", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Gemüse backen: Kartoffeln vierteln, mit Öl 25-30 Min. backen. Karottenstifte die letzten 18-20 Min. mitbacken.", "duration_min": 30},
                {"step_number": 2, "description": "Senfbrösel: Panko, Senf und weiche Butter verkneten.", "duration_min": 3},
                {"step_number": 3, "description": "Hähnchen braten: Hähnchen 3-4 Min. je Seite anbraten. In Auflaufform geben, Senfbrösel daraufdrücken. 12-14 Min. im Ofen mitbacken.", "duration_min": 18},
                {"step_number": 4, "description": "Soße: Schalotte und Knoblauch anschwitzen. Kochsahne, Wasser und Brühe einrühren. Babyspinat zugeben.", "duration_min": 5},
                {"step_number": 5, "description": "Anrichten: Hähnchen mit Gemuese und Rahmspinat servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Bacon-Wraps mit Tomaten und Salat",
            "kcal_per_serving": 1037,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Fleisch", "Schnell", "Tacos"],
            "ingredients": [
                {"name": "Weizentortillas", "quantity": 250, "unit": "g"},
                {"name": "Bacon (Scheiben)", "quantity": 50, "unit": "g"},
                {"name": "Tomate", "quantity": 1, "unit": "Stück"},
                {"name": "Salatherz (Romana)", "quantity": 1, "unit": "Stück"},
                {"name": "Buttermilch-Zitronen-Dressing", "quantity": 50, "unit": "ml"},
                {"name": "Mayonnaise", "quantity": 50, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Tomate in Scheiben, Salatherz in Streifen. Mayo und Dressing mischen. Salat damit marinieren.", "duration_min": 5},
                {"step_number": 2, "description": "Bacon braten: Bacon mit Zucker in Pfanne geben und 3-4 Min. pro Seite karamellisieren.", "duration_min": 8},
                {"step_number": 3, "description": "Wraps erwärmen: Wraps in der Pfanne 1-2 Min. erwärmen.", "duration_min": 2},
                {"step_number": 4, "description": "Anrichten: Wrap mit Bacon, Tomate und Salat belegen, dann einrollen.", "duration_min": None}
            ]
        },
        {
            "name": "Penne-Bowl mit Ofengemüse und Mozzarella",
            "kcal_per_serving": 1098,
            "active_cooking_time_min": 15,
            "total_time_min": 30,
            "tags": ["Pasta", "Vegetarisch", "Viel Gemüse"],
            "ingredients": [
                {"name": "Penne", "quantity": 270, "unit": "g"},
                {"name": "Büffelmozzarella", "quantity": 125, "unit": "g"},
                {"name": "Tomate", "quantity": 1, "unit": "Stück"},
                {"name": "Zucchini", "quantity": 1, "unit": "Stück"},
                {"name": "rote Spitzpaprika", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Basilikum", "quantity": 10, "unit": "g"},
                {"name": "Basilikumpaste", "quantity": 15, "unit": "ml"},
                {"name": "Hartkäse gerieben", "quantity": 20, "unit": "g"},
                {"name": "Sonnenblumenkerne", "quantity": 20, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Gemüse backen: Zucchini, Paprika, Knoblauch mit Öl 10-15 Min. backen. Kerne die letzten 5 Min. mitgaren.", "duration_min": 15},
                {"step_number": 2, "description": "Nudeln: Penne 10-12 Min. garen.", "duration_min": 12},
                {"step_number": 3, "description": "Pesto: Gebackenen Knoblauch mit Kernen, Käse, Basilikum, Paste, Öl und Wasser pürieren.", "duration_min": 5},
                {"step_number": 4, "description": "Tomatensalat: Tomate in Spalten, mit Essig, Öl, Zucker und Basilikum marinieren.", "duration_min": 3},
                {"step_number": 5, "description": "Vollenden: Gemüse mit Balsamico mischen. Penne mit halbem Pesto mischen.", "duration_min": 2},
                {"step_number": 6, "description": "Anrichten: Penne mit Gemüse und Salat in Bowl anrichten. Mozzarella daraufsetzen. Rest Pesto dazu reichen.", "duration_min": None}
            ]
        },
        {
            "name": "Zucchinipuffer mit Salat und Kräuterschmand",
            "kcal_per_serving": 640,
            "active_cooking_time_min": 20,
            "total_time_min": 30,
            "tags": ["Vegetarisch", "Gesund"],
            "ingredients": [
                {"name": "Zucchini", "quantity": 1, "unit": "Stück"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "Gurke", "quantity": 0.5, "unit": "Stück"},
                {"name": "Pflücksalat", "quantity": 75, "unit": "g"},
                {"name": "Limette", "quantity": 1, "unit": "Stück"},
                {"name": "Frühlingszwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Dill/Petersilie", "quantity": 10, "unit": "g"},
                {"name": "Buttermilch-Zitronen-Dressing", "quantity": 50, "unit": "ml"},
                {"name": "Schmand", "quantity": 100, "unit": "g"},
                {"name": "Haselnüsse", "quantity": 20, "unit": "g"},
                {"name": "Hello Patatas", "quantity": 4, "unit": "g"},
                {"name": "Gouda gerieben", "quantity": 50, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Gemüse reiben: Zucchini und Karotte reiben. Zucchini gut ausdrücken. Frühlingszwiebel in Ringe.", "duration_min": 6},
                {"step_number": 2, "description": "Teig: Mehl und Ei verrühren. Geraspeltes Gemüse, weiße Zwiebelringe, Käse und Hello Patatas untermischen.", "duration_min": 5},
                {"step_number": 3, "description": "Nüsse: Haselnüsse 2-3 Min. rösten, dann hacken.", "duration_min": 3},
                {"step_number": 4, "description": "Puffer braten: Puffer aus dem Teig ca. 3 Min. pro Seite goldbraun braten.", "duration_min": 12},
                {"step_number": 5, "description": "Dip & Salat: Kräuter in den Schmand rühren. Pflücksalat und Gurke mit Dressing mischen.", "duration_min": 4},
                {"step_number": 6, "description": "Anrichten: Salat mit Haselnüssen, Puffer und Dip servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Süßkartoffelgnocchi mit Bacon-Sahne-Soße",
            "kcal_per_serving": 744,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Pasta", "Fleisch", "Schnell"],
            "ingredients": [
                {"name": "Süßkartoffelgnocchi", "quantity": 400, "unit": "g"},
                {"name": "Bacon Streifen", "quantity": 80, "unit": "g"},
                {"name": "Porree", "quantity": 1, "unit": "Stück"},
                {"name": "Basilikum", "quantity": 10, "unit": "g"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Hartkäse geraspelt", "quantity": 10, "unit": "g"},
                {"name": "milder Chili-Mix", "quantity": 2, "unit": "g"},
                {"name": "Gemüsebrühepulver", "quantity": 4, "unit": "g"},
                {"name": "Champignons", "quantity": 125, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Champignons in Scheiben, Porree in Streifen.", "duration_min": 4},
                {"step_number": 2, "description": "Anbraten: Gnocchi mit Bacon in Öl 2 Min. braten.", "duration_min": 3},
                {"step_number": 3, "description": "Gemüse: Porree und Champignons zufügen, 3 Min. mitbraten.", "duration_min": 4},
                {"step_number": 4, "description": "Soße: Mit Sahne und Wasser ablöschen. Chili-Mix und Brühe einrühren. 3-5 Min. einköcheln.", "duration_min": 5},
                {"step_number": 5, "description": "Anrichten: Mit Käse und Basilikum garnieren.", "duration_min": None}
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
