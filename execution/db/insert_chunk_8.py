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
            "name": "Perlencouscous-Salat mit Ziegenfrischkäse",
            "kcal_per_serving": 886,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Vegetarisch", "Gesund"],
            "ingredients": [
                {"name": "Perlencouscous", "quantity": 150, "unit": "g"},
                {"name": "Kichererbsen", "quantity": 380, "unit": "g"},
                {"name": "Gurke", "quantity": 1, "unit": "Stück"},
                {"name": "Ziegenfrischkäse-Crumble mit Honig", "quantity": 100, "unit": "g"},
                {"name": "Cranberries", "quantity": 40, "unit": "g"},
                {"name": "Tomatenpesto", "quantity": 25, "unit": "g"},
                {"name": "Buttermilch-Zitronen-Dressing", "quantity": 50, "unit": "ml"},
                {"name": "Balsamicocreme", "quantity": 12, "unit": "g"},
                {"name": "Petersilie", "quantity": 10, "unit": "g"},
                {"name": "Hello Mezze", "quantity": 2, "unit": "g"},
                {"name": "Gemüsebrühepulver", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Couscous kochen: Perlencouscous in Brühe 12 Min. köcheln lassen, dann ausdampfen lassen.", "duration_min": 15},
                {"step_number": 2, "description": "Kichererbsen braten: Kichererbsen mit Hello Mezze 4-5 Min. braten. Tomatenpesto unterrühren.", "duration_min": 6},
                {"step_number": 3, "description": "Gemüse vorbereiten: Gurke in Halbmonde. Petersilie hacken.", "duration_min": 4},
                {"step_number": 4, "description": "Marinieren: Gurke mit Cranberries (Hälfte) und Dressing marinieren.", "duration_min": 3},
                {"step_number": 5, "description": "Vollenden: Couscous und Petersilie zur Gurke geben. Vermengen.", "duration_min": 2},
                {"step_number": 6, "description": "Anrichten: Salat mit Ziegenkäse, Kichererbsen, Cranberries toppen. Balsamicocreme darüber.", "duration_min": None}
            ]
        },
        {
            "name": "Hähnchengeschnetzeltes mit Avocado-Tomaten-Salat",
            "kcal_per_serving": 526,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Fleisch", "Gesund", "Schnell"],
            "ingredients": [
                {"name": "Hähnchengeschnetzeltes, mariniert", "quantity": 250, "unit": "g"},
                {"name": "Avocado", "quantity": 1, "unit": "Stück"},
                {"name": "Salatherz (Romana)", "quantity": 1, "unit": "Stück"},
                {"name": "Tomate", "quantity": 1, "unit": "Stück"},
                {"name": "rote Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Naturjoghurt", "quantity": 150, "unit": "g"},
                {"name": "Sonnenblumenkerne", "quantity": 20, "unit": "g"},
                {"name": "süßer Senf", "quantity": 15, "unit": "ml"},
                {"name": "körniger Senf", "quantity": 17, "unit": "g"},
                {"name": "mittelscharfer Senf", "quantity": 10, "unit": "ml"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Zwiebel in Streifen. Kerne rösten. Hähnchen 3-4 Min. braten, Zwiebel 1-2 Min. mitbraten.", "duration_min": 8},
                {"step_number": 2, "description": "Dressing: Senfsorten, Joghurt, Öl, Honig, Essig verrühren.", "duration_min": 4},
                {"step_number": 3, "description": "Salat: Tomate in Halbmonde, Salat in Streifen, Avocado in Streifen schneiden.", "duration_min": 5},
                {"step_number": 4, "description": "Anrichten: Tomate, Salat und Hähnchen mit Dressing mischen. Mit Avocado und Kernen toppen.", "duration_min": None}
            ]
        },
        {
            "name": "Pulled Pork Tacos mit Tomatensalsa",
            "kcal_per_serving": 744,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Fleisch", "Tacos", "Schnell"],
            "ingredients": [
                {"name": "Pulled Pork", "quantity": 250, "unit": "g"},
                {"name": "Weizentortillas", "quantity": 200, "unit": "g"},
                {"name": "Avocado", "quantity": 1, "unit": "Stück"},
                {"name": "Tomate", "quantity": 1, "unit": "Stück"},
                {"name": "rote Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Koriander/Minze", "quantity": 10, "unit": "g"},
                {"name": "Limette", "quantity": 1, "unit": "Stück"},
                {"name": "Ketchup", "quantity": 25, "unit": "g"},
                {"name": "Hello Cajun", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Salsa: Tomaten und Zwiebel würfeln, mit Limettensaft, Zucker, Salz, Pfeffer marinieren.", "duration_min": 5},
                {"step_number": 2, "description": "Soße & Tacos: Ketchup, Cajun, Limettensaft und Wasser verrühren. Tortillas 30 Sek. pro Seite erhitzen.", "duration_min": 5},
                {"step_number": 3, "description": "Pulled Pork: Fleisch 2-3 Min. braten. Soße zufügen und 1-2 Min. köcheln.", "duration_min": 5},
                {"step_number": 4, "description": "Vollenden: Avocado würfeln, Kräuter hacken.", "duration_min": 3},
                {"step_number": 5, "description": "Anrichten: Tacos mit Pulled Pork, Salsa, Avocado und Kräutern belegen.", "duration_min": None}
            ]
        },
        {
            "name": "Knuspriger Tofu mit Ofengemüse und Bulgur",
            "kcal_per_serving": 785,
            "active_cooking_time_min": 15,
            "total_time_min": 35,
            "tags": ["Vegetarisch", "Gesund"],
            "ingredients": [
                {"name": "Tofu Natur", "quantity": 180, "unit": "g"},
                {"name": "Bulgur", "quantity": 150, "unit": "g"},
                {"name": "braune Champignons", "quantity": 100, "unit": "g"},
                {"name": "Tomate", "quantity": 1, "unit": "Stück"},
                {"name": "Rucola", "quantity": 50, "unit": "g"},
                {"name": "rote Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Sultaninen", "quantity": 1, "unit": "g"},
                {"name": "Hello Souflaki", "quantity": 4, "unit": "g"},
                {"name": "Hello Paprika", "quantity": 4, "unit": "g"},
                {"name": "Maisstärke", "quantity": 8, "unit": "g"},
                {"name": "Sahnejoghurt", "quantity": 75, "unit": "g"},
                {"name": "Buttermilch-Zitronen-Dressing", "quantity": 50, "unit": "ml"},
                {"name": "Gemüsebrühepulver", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Tofu: In Würfel schneiden. Mit Hello Souflaki, Maisstärke, Zucker, Öl marinieren. 25-30 Min. backen.", "duration_min": 30},
                {"step_number": 2, "description": "Bulgur: Mit Brühe und Sultaninen 15 Min. köcheln, 10 Min. quellen.", "duration_min": 25},
                {"step_number": 3, "description": "Gemüse: Pilze und Zwiebeln schneiden, mit Öl mischen und die letzten 15-20 Min. zum Tofu aufs Blech geben.", "duration_min": 20},
                {"step_number": 4, "description": "Tomaten: In Spalten schneiden.", "duration_min": 2},
                {"step_number": 5, "description": "Dressing: Joghurt, Buttermilch-Dressing, Hello Paprika, Essig, Öl verrühren.", "duration_min": 3},
                {"step_number": 6, "description": "Anrichten: Bulgur mit Gemüse, Rucola, Tomaten und Tofu anrichten. Dressing darüber.", "duration_min": None}
            ]
        },
        {
            "name": "Portobello-Teriyaki-Bowl mit Reise",
            "kcal_per_serving": 540,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Vegetarisch", "Reis"],
            "ingredients": [
                {"name": "Basmatireis", "quantity": 150, "unit": "g"},
                {"name": "Portobello-Pilze", "quantity": 150, "unit": "g"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "kleine Salatgurke", "quantity": 1, "unit": "Stück"},
                {"name": "Avocado", "quantity": 1, "unit": "Stück"},
                {"name": "Limette", "quantity": 1, "unit": "Stück"},
                {"name": "Koriander/Minze", "quantity": 10, "unit": "g"},
                {"name": "Teriyakisoße", "quantity": 50, "unit": "ml"},
                {"name": "Sweet Chili Soße", "quantity": 25, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Reis: 10 Min. köcheln, 10 Min. ziehen lassen.", "duration_min": 20},
                {"step_number": 2, "description": "Portobello: Vierteln, 0,5 cm Scheiben, 4-5 Min. braten. Mit Teriyakisoße ablöschen.", "duration_min": 8},
                {"step_number": 3, "description": "Salat: Karotte raspeln, mit Minze und Limettensaft mischen. Gurkenstifte mit Limettenabrieb und Saft mischen.", "duration_min": 6},
                {"step_number": 4, "description": "Avocado: In feine Streifen schneiden.", "duration_min": 2},
                {"step_number": 5, "description": "Anrichten: Reis, Portobello, Salate und Avocado anrichten. Sweet Chili Soße darüber.", "duration_min": None}
            ]
        },
        {
            "name": "Sweet Chili Tofu mit Pak-Choi-Salat",
            "kcal_per_serving": 705,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Vegetarisch", "Reis"],
            "ingredients": [
                {"name": "süßer Chili-Grill-Tofu", "quantity": 180, "unit": "g"},
                {"name": "Basmatireis", "quantity": 150, "unit": "g"},
                {"name": "Pak Choi", "quantity": 200, "unit": "g"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "kleine Salatgurke", "quantity": 1, "unit": "Stück"},
                {"name": "Limette", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch-Ingwer-Paste in Öl", "quantity": 30, "unit": "g"},
                {"name": "Agavendicksaft", "quantity": 20, "unit": "ml"},
                {"name": "Sojasoße", "quantity": 50, "unit": "ml"},
                {"name": "Sesamöl", "quantity": 10, "unit": "ml"},
                {"name": "Sesamsamen", "quantity": 10, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Reis: 10 Min. köcheln, 10 Min. ziehen lassen.", "duration_min": 20},
                {"step_number": 2, "description": "Gemüse: Karotte, Gurke und Pak Choi schneiden.", "duration_min": 5},
                {"step_number": 3, "description": "Dressing: Sesamöl, Agavendicksaft, Sojasoße, Ingwer-Knoblauch-Paste, Limettensaft pürieren.", "duration_min": 4},
                {"step_number": 4, "description": "Tofu & Sesam: Sesam rösten. Tofu trocken tupfen, würfeln und 6-7 Min. braten.", "duration_min": 9},
                {"step_number": 5, "description": "Vollenden: Gemüse mit Dressing mischen. Reis mit Limettenabrieb lockern.", "duration_min": 3},
                {"step_number": 6, "description": "Anrichten: Reis, Salat und Tofu anrichten. Sesam darüber.", "duration_min": None}
            ]
        },
        {
            "name": "Hähnchen-Penne mit Brokkoli",
            "kcal_per_serving": 881,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Pasta", "Fleisch", "Schnell"],
            "ingredients": [
                {"name": "Hähnchengeschnetzeltes", "quantity": 250, "unit": "g"},
                {"name": "Penne", "quantity": 270, "unit": "g"},
                {"name": "Brokkoli", "quantity": 1, "unit": "Stück"},
                {"name": "Tomate", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Hartkäse gerieben", "quantity": 20, "unit": "g"},
                {"name": "Tomatenmark", "quantity": 17.5, "unit": "g"},
                {"name": "Hello Buon Appetito", "quantity": 2, "unit": "g"},
                {"name": "Hühnerbrühepulver", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Brokkoli in Röschen, Tomate würfeln, Knoblauch hacken.", "duration_min": 5},
                {"step_number": 2, "description": "Pürieren: Sahne, Brühe, Buon Appetito, Tomatenmark, Tomate, Wasser fein pürieren.", "duration_min": 3},
                {"step_number": 3, "description": "Pasta: Penne 10-11 Min. garen, Brokkoli in den letzten 3-5 Min. mitkochen.", "duration_min": 12},
                {"step_number": 4, "description": "Fleisch: Hähnchen und Knoblauch 4-5 Min. anbraten.", "duration_min": 6},
                {"step_number": 5, "description": "Soße: Sahnemix aufkochen, andicken lassen. Hartkäse (Hälfte) einrühren.", "duration_min": 5},
                {"step_number": 6, "description": "Anrichten: Pasta, Brokkoli, Soße mischen. Mit Hähnchen und Käse toppen.", "duration_min": None}
            ]
        },
        {
            "name": "Chili-Nudeln mit Champignons",
            "kcal_per_serving": 779,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Pasta", "Vegetarisch", "Schnell"],
            "ingredients": [
                {"name": "Chili-Nudeln", "quantity": 200, "unit": "g"},
                {"name": "braune Champignons", "quantity": 150, "unit": "g"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "Schalotte", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "rote Chilischote", "quantity": 1, "unit": "Stück"},
                {"name": "Limette", "quantity": 1, "unit": "Stück"},
                {"name": "Kokosmilch", "quantity": 250, "unit": "ml"},
                {"name": "Ingwerpaste", "quantity": 5, "unit": "g"},
                {"name": "Sojasoße", "quantity": 25, "unit": "ml"},
                {"name": "Sesamöl", "quantity": 20, "unit": "ml"},
                {"name": "Sesamsamen", "quantity": 10, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Schalotte in Streifen, Karotte & Champignons in Scheiben. Limettenabrieb.", "duration_min": 5},
                {"step_number": 2, "description": "Nudeln: Chilinudeln 5 Min. im Wasser gar ziehen lassen.", "duration_min": 6},
                {"step_number": 3, "description": "Soßenbasis: Sesam rösten. Knoblauch, Schalotte, Ingwer in Sesamöl 1 Min. anbraten.", "duration_min": 4},
                {"step_number": 4, "description": "Gemüse: Karotten und Champignons 3-5 Min. mitbraten. Mit Sojasoße und Kokosmilch ablöschen. Limettenschale einrühren.", "duration_min": 6},
                {"step_number": 5, "description": "Anrichten: Nudeln in der Pfanne mischen. Mit Sesam, Chili und Limette anrichten.", "duration_min": None}
            ]
        },
        {
            "name": "Käsesoßen-Bacon-Burger mit Wedges",
            "kcal_per_serving": 1672,
            "active_cooking_time_min": 25,
            "total_time_min": 35,
            "tags": ["Fleisch", "Kartoffeln"],
            "ingredients": [
                {"name": "Rinderhackfleischzubereitung", "quantity": 300, "unit": "g"},
                {"name": "Bacon (Scheiben)", "quantity": 125, "unit": "g"},
                {"name": "Kartoffeln", "quantity": 600, "unit": "g"},
                {"name": "Brioche Bun", "quantity": 160, "unit": "g"},
                {"name": "Salatherz (Romana)", "quantity": 1, "unit": "Stück"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "rote Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Gouda gerieben", "quantity": 75, "unit": "g"},
                {"name": "Aioli", "quantity": 60, "unit": "g"},
                {"name": "Hello Patatas", "quantity": 6, "unit": "g"},
                {"name": "Hühnerbrühepulver", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Kartoffeln: Kartoffelspalten mit Öl und Hello Patatas 25-30 Min. backen.", "duration_min": 30},
                {"step_number": 2, "description": "Käsesoße: Zwiebel anschwitzen, Sahne, Brühe, Hello Patatas zugeben. Gouda darin schmelzen.", "duration_min": 6},
                {"step_number": 3, "description": "Bacon: Mit Zucker die letzten 15 Min. im Ofen backen.", "duration_min": 15},
                {"step_number": 4, "description": "Slaw: Aioli-Dressing mischen. Karotte raspeln, Zwiebel und Salat zufügen, marinieren.", "duration_min": 5},
                {"step_number": 5, "description": "Burger: Patties formen, braten (3-4 Min. pro Seite). Buns toasten.", "duration_min": 10},
                {"step_number": 6, "description": "Anrichten: Bun mit Aioli, Slaw, Patty, Käsesoße und Bacon belegen. Wedges dazu.", "duration_min": None}
            ]
        },
        {
            "name": "Gratinierte Nektarinen mit Bulgursalat",
            "kcal_per_serving": 618,
            "active_cooking_time_min": 15,
            "total_time_min": 30,
            "tags": ["Vegetarisch", "Gesund"],
            "ingredients": [
                {"name": "Bulgur", "quantity": 150, "unit": "g"},
                {"name": "Hirtenkäse", "quantity": 100, "unit": "g"},
                {"name": "Nektarine", "quantity": 1, "unit": "Stück"},
                {"name": "Tomate", "quantity": 1, "unit": "Stück"},
                {"name": "Gurke", "quantity": 1, "unit": "Stück"},
                {"name": "Rucola", "quantity": 50, "unit": "g"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Zitrone", "quantity": 1, "unit": "Stück"},
                {"name": "Sahnejoghurt", "quantity": 75, "unit": "g"},
                {"name": "Hello Harissa", "quantity": 6, "unit": "g"},
                {"name": "Gemüsebrühepulver", "quantity": 6, "unit": "g"},
                {"name": "Balsamicocreme", "quantity": 12, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Bulgur: Mit Knoblauch anschwitzen, Wasser, Brühe und Harissa (Teil) zugeben. 15 Min. köcheln, 10 Min. quellen.", "duration_min": 25},
                {"step_number": 2, "description": "Nektarinen: Halbieren, mit Zucker und Hirtenkäse belegen, 3-5 Min. gratinieren.", "duration_min": 8},
                {"step_number": 3, "description": "Gemüse: Gurke und Tomate würfeln.", "duration_min": 3},
                {"step_number": 4, "description": "Salat & Dip: Joghurt mit Zitronenschale und -saft mischen. Bulgur mit Gemüse und Dressing mischen.", "duration_min": 5},
                {"step_number": 5, "description": "Anrichten: Rucola mit Dip mischen, Bulgur darauf, Nektarinen obendrauf. Mit Balsamico garnieren.", "duration_min": None}
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
