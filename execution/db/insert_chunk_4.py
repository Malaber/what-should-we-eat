import os
import json
from execution.db.database import SessionLocal
from execution.db.models import Recipe, Ingredient, InstructionStep, Tag

def seed_recipes():
    db = SessionLocal()
    
    recipes_data = [
        {
            "name": "Hähnchenbrustfilet mit Gnocchi in Tomaten-Sahnesoße",
            "kcal_per_serving": 716,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Pasta", "Fleisch", "Schnell", "Viel Gemüse"],
            "ingredients": [
                {"name": "Hähnchenbrustfilet in Lake", "quantity": 250, "unit": "g"},
                {"name": "frische Gnocchi", "quantity": 400, "unit": "g"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Tomatenpesto", "quantity": 50, "unit": "g"},
                {"name": "Hühnerbrühepulver", "quantity": 4, "unit": "g"},
                {"name": "rote Kirschtomaten", "quantity": 125, "unit": "g"},
                {"name": "Babyspinat", "quantity": 50, "unit": "g"},
                {"name": "Hartkäse gerieben", "quantity": 20, "unit": "g"},
                {"name": "Sonnenblumenkerne", "quantity": 20, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Soße vorbereiten: Kochsahne, Tomatenpesto, Brühepulver und Wasser verrühren.", "duration_min": 3},
                {"step_number": 2, "description": "Vorbereitung: Kirschtomaten halbieren. Hähnchen waagerecht einschneiden, aufklappen, salzen und pfeffern.", "duration_min": 5},
                {"step_number": 3, "description": "Gnocchi braten: Sonnenblumenkerne anrösten. Hähnchen 3-4 Min. je Seite anbraten, herausnehmen. Gnocchi und Tomaten 2-3 Min. braten.", "duration_min": 10},
                {"step_number": 4, "description": "Vollenden: Mit Soße ablöschen. Hähnchen zugeben, 2 Min. köcheln. Babyspinat zugeben.", "duration_min": 3},
                {"step_number": 5, "description": "Anrichten: Gnocchi und Hähnchen anrichten. Mit Käse und Kernen toppen.", "duration_min": None}
            ]
        },
        {
            "name": "Hähnchenpfanne mit Champignons und Reis",
            "kcal_per_serving": 594,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Fleisch", "Reis", "Schnell"],
            "ingredients": [
                {"name": "Hähnchenbrustfilet in Lake", "quantity": 250, "unit": "g"},
                {"name": "Schnittlauch", "quantity": 10, "unit": "g"},
                {"name": "Zwiebel", "quantity": 0.5, "unit": "Stück"},
                {"name": "Ketchup", "quantity": 34, "unit": "ml"},
                {"name": "Sojasoße", "quantity": 25, "unit": "ml"},
                {"name": "Aprikosenchutney", "quantity": 50, "unit": "g"},
                {"name": "Sesamsamen", "quantity": 10, "unit": "g"},
                {"name": "Maisstärke", "quantity": 8, "unit": "g"},
                {"name": "Hühnerbrühepulver", "quantity": 4, "unit": "g"},
                {"name": "braune Champignons", "quantity": 150, "unit": "g"},
                {"name": "Basmatireis", "quantity": 150, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Wasser kochen. Hähnchen in Stücke schneiden und in Stärke wenden.", "duration_min": 5},
                {"step_number": 2, "description": "Reis kochen: Reis in Salzwasser 10 Min. köcheln, 10 Min. ziehen lassen.", "duration_min": 20},
                {"step_number": 3, "description": "Sesam rösten: Sesam 1 Min. ohne Fett rösten.", "duration_min": 2},
                {"step_number": 4, "description": "Zwischendurch: Schnittlauch in Ringe, Zwiebel in Spalten, Champignons vierteln. Soße aus Ketchup, Chutney, Sojasoße, Brühe, Wasser, Essig, Zucker mischen.", "duration_min": 5},
                {"step_number": 5, "description": "Abschmecken: Zwiebel und Hähnchen 2-3 Min. braten. Champignons zufügen, 3-4 Min. mitbraten. Soße unterrühren, 5 Min. köcheln.", "duration_min": 12},
                {"step_number": 6, "description": "Anrichten: Reis und Hähnchen anrichten. Mit Schnittlauch und Sesam garnieren.", "duration_min": None}
            ]
        },
        {
            "name": "Zitronen-Hähnchengeschnetzeltes mit Risotto",
            "kcal_per_serving": 870,
            "active_cooking_time_min": 15,
            "total_time_min": 30,
            "tags": ["Fleisch", "Reis"],
            "ingredients": [
                {"name": "Hähnchengeschnetzeltes", "quantity": 250, "unit": "g"},
                {"name": "Risottoreis", "quantity": 225, "unit": "g"},
                {"name": "Rucola", "quantity": 50, "unit": "g"},
                {"name": "Tomate", "quantity": 1, "unit": "Stück"},
                {"name": "Schalotte", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Hartkäse gerieben", "quantity": 40, "unit": "g"},
                {"name": "Hello Buon Appetito", "quantity": 2, "unit": "g"},
                {"name": "Hühnerbrühepulver", "quantity": 8, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Schalotte und Knoblauch fein würfeln/hacken.", "duration_min": 5},
                {"step_number": 2, "description": "Hähnchen braten: Hähnchen 1-2 Min. scharf anbraten. Reis, Schalotte, Knoblauch, Gewürz zugeben und 1 Min. anschwitzen.", "duration_min": 4},
                {"step_number": 3, "description": "Risotto ansetzen: Mit Wasser ablöschen. Brühepulver und Salz einrühren, 20-25 Min. köcheln lassen.", "duration_min": 25},
                {"step_number": 4, "description": "Salat: Zitrone reiben und in Spalten schneiden. Tomaten würfeln, Rucola hacken. Beides mit Zitronensaft, Öl, Salz, Pfeffer marinieren.", "duration_min": 5},
                {"step_number": 5, "description": "Vollenden: Käse, Zitronenabrieb, Butter ins Risotto rühren.", "duration_min": 2},
                {"step_number": 6, "description": "Anrichten: Risotto anrichten, mit Salat toppen.", "duration_min": None}
            ]
        },
        {
            "name": "Tortellini-Tomaten-Suppe mit Kürbiskernen",
            "kcal_per_serving": 855,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Pasta", "Vegetarisch", "Schnell", "Gesund"],
            "ingredients": [
                {"name": "frische Tortellini", "quantity": 400, "unit": "g"},
                {"name": "Tomatensugo", "quantity": 300, "unit": "g"},
                {"name": "Kürbiskerne", "quantity": 20, "unit": "g"},
                {"name": "Hartkäse geraspelt", "quantity": 20, "unit": "g"},
                {"name": "Gemüsebrühepulver", "quantity": 4, "unit": "g"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Basilikum", "quantity": 10, "unit": "g"},
                {"name": "rote Chilischote", "quantity": 0.5, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Paprika multicolor", "quantity": 1, "unit": "Stück"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Wasser kochen. Paprika in Streifen, Knoblauch fein hacken.", "duration_min": 5},
                {"step_number": 2, "description": "Kerne rösten: Kürbiskerne 1-2 Min. anrösten.", "duration_min": 2},
                {"step_number": 3, "description": "Suppe: Paprika 2-3 Min. braten. Knoblauch zugeben. Mit Wasser und Sugo ablöschen, Brühepulver einrühren. Basilikum zugeben, 5 Min. köcheln.", "duration_min": 10},
                {"step_number": 4, "description": "Nudeln kochen: Tortellini zugeben und 2-3 Min. köcheln lassen.", "duration_min": 3},
                {"step_number": 5, "description": "Toppings: Chili in Streifen, Basilikum hacken. Sahne zur Suppe geben, 1 Min. köcheln.", "duration_min": 3},
                {"step_number": 6, "description": "Anrichten: Suppe verteilen, mit Toppings garnieren.", "duration_min": None}
            ]
        },
        {
            "name": "Perlencouscous mit Coleslaw und Hirtenkäse",
            "kcal_per_serving": 643,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Vegetarisch", "Gesund", "Schnell"],
            "ingredients": [
                {"name": "Perlencouscous", "quantity": 150, "unit": "g"},
                {"name": "Avocado", "quantity": 1, "unit": "Stück"},
                {"name": "Hirtenkäse", "quantity": 100, "unit": "g"},
                {"name": "Naturjoghurt", "quantity": 100, "unit": "g"},
                {"name": "Coleslaw-Mix", "quantity": 200, "unit": "g"},
                {"name": "Gurke", "quantity": 0.5, "unit": "Stück"},
                {"name": "rote Kirschtomaten", "quantity": 125, "unit": "g"},
                {"name": "Dill/Petersilie", "quantity": 10, "unit": "g"},
                {"name": "Hello Souflaki", "quantity": 8, "unit": "g"},
                {"name": "Gemüsebrühepulver", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Couscous kochen: Brühe und Hello Souflaki aufkochen. Couscous einrühren, 12 Min. köcheln, ausdampfen lassen.", "duration_min": 15},
                {"step_number": 2, "description": "Beilagen: Coleslaw-Mix mit Wasser 2-3 Min. dünsten. Kräuter hacken, Gurke in Halbmonde. Kirschtomaten halbieren. Avocado in Streifen.", "duration_min": 7},
                {"step_number": 3, "description": "Letzte Schritte: Joghurt, Kräuter, Essig, Öl zu Coleslaw-Mix geben und vermengen.", "duration_min": 3},
                {"step_number": 4, "description": "Anrichten: Couscous verteilen, Coleslaw darauf. Mit Tomaten, Avocado und Hirtenkäse toppen.", "duration_min": None}
            ]
        },
        {
            "name": "Rigatoni-Auflauf mit Rinderhackfleisch",
            "kcal_per_serving": 1634,
            "active_cooking_time_min": 20,
            "total_time_min": 35,
            "tags": ["Pasta", "Fleisch", "Viel Gemüse"],
            "ingredients": [
                {"name": "Rinderhackfleisch", "quantity": 300, "unit": "g"},
                {"name": "Rigatoni", "quantity": 360, "unit": "g"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "Basilikum", "quantity": 10, "unit": "g"},
                {"name": "Büffelmozzarella", "quantity": 125, "unit": "g"},
                {"name": "Tomatensugo", "quantity": 300, "unit": "g"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Gouda gerieben", "quantity": 75, "unit": "g"},
                {"name": "Panko-Mehl", "quantity": 25, "unit": "g"},
                {"name": "Hello Buon Appetito", "quantity": 6, "unit": "g"},
                {"name": "Rinderbrühe", "quantity": 10, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Wasser kochen, Backofen vorheizen. Karotten raspeln, Basilikum in Streifen.", "duration_min": 5},
                {"step_number": 2, "description": "Pasta kochen: Rigatoni 10-11 Min. bissfest garen. Wasser auffangen, abgießen.", "duration_min": 12},
                {"step_number": 3, "description": "Soße ansetzen: Hackfleisch und Karotten 3-4 Min. scharf anbraten.", "duration_min": 5},
                {"step_number": 4, "description": "Vollenden: Brühe, Gewürz, Essig zufügen. Sugo, Kochsahne und Pastawasser zufügen, 3-4 Min. köcheln.", "duration_min": 5},
                {"step_number": 5, "description": "Auflauf: Pasta zur Soße geben, in Auflaufform füllen. Mit Gouda, Mozzarella und Panko 15-20 Min. backen.", "duration_min": 20},
                {"step_number": 6, "description": "Anrichten: Mit Basilikum garnieren.", "duration_min": None}
            ]
        },
        {
            "name": "Zucchini-Paccheri mit Zitronen-Gremolata",
            "kcal_per_serving": 780,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Pasta", "Vegetarisch", "Gesund"],
            "ingredients": [
                {"name": "frische Paccheri", "quantity": 250, "unit": "g"},
                {"name": "Zucchini", "quantity": 1, "unit": "Stück"},
                {"name": "Rosmarin getrocknet", "quantity": 1, "unit": "g"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Zitrone", "quantity": 1, "unit": "Stück"},
                {"name": "Kochsahne", "quantity": 225, "unit": "g"},
                {"name": "Pistazien", "quantity": 10, "unit": "g"},
                {"name": "Hartkäse gerieben", "quantity": 40, "unit": "g"},
                {"name": "Gemüsebrühepulver", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Wasser aufkochen. Zucchini in Stifte schneiden, Knoblauch abziehen. Zitrone reiben und spalten.", "duration_min": 5},
                {"step_number": 2, "description": "Nudeln: Paccheri 3-5 Min. bissfest garen. In Pfanne Zucchini 3-5 Min. anbraten.", "duration_min": 8},
                {"step_number": 3, "description": "Ablöschen: Nudeln abgießen, Pastawasser auffangen. Zucchini mit Pastawasser und Zitronensaft ablöschen.", "duration_min": 2},
                {"step_number": 4, "description": "Gremolata: Pistazien rösten, hacken. Mit Rosmarin, Zitronenabrieb, Saft, Knoblauch und Öl vermengen.", "duration_min": 5},
                {"step_number": 5, "description": "Soße: Brühe, Zitronenabrieb, Sahne und halben Käse zur Zucchini geben, 2-3 Min. köcheln. Paccheri 1 Min. mitkochen.", "duration_min": 4},
                {"step_number": 6, "description": "Anrichten: Paccheri mit Soße anrichten, mit Restkäse und Gremolata toppen.", "duration_min": None}
            ]
        },
        {
            "name": "Linguine mit Brokkoli und Panko-Kampot-Topping",
            "kcal_per_serving": 827,
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
                {"name": "Panko-Mehl", "quantity": 18, "unit": "g"},
                {"name": "Kampot-Pfeffer", "quantity": 1, "unit": "g"},
                {"name": "Hello Smoky Paprika", "quantity": 3, "unit": "g"},
                {"name": "Gemüsebrühepulver", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Topping: Kampot-Pfeffer, Knoblauch hacken. Panko 1-2 Min. rösten. Knoblauch, Pfeffer zugeben, 1 Min. rösten, salzen.", "duration_min": 5},
                {"step_number": 2, "description": "Vorbereitung: Zwiebel und Porree schneiden, Brokkoli in Röschen, Zitrone vierteln.", "duration_min": 5},
                {"step_number": 3, "description": "Zwischendurch: Zwiebel und Lauch 3-4 Min. glasig anschwitzen. Knoblauch und Smoky Paprika 1 Min. anrösten.", "duration_min": 6},
                {"step_number": 4, "description": "Pasta: Brokkoli in kochendem Salzwasser 6 Min. garen, Linguine in letzten 3 Min. bissfest garen. Abgießen.", "duration_min": 10},
                {"step_number": 5, "description": "Soße: Pfanne mit Kokosmilch, Kochwasser, Brühepulver ablöschen. Linguine, Brokkoli, Hefeflocken, Zitronensaft, Margarine 1 Min. köcheln.", "duration_min": 5},
                {"step_number": 6, "description": "Anrichten: Pasta verteilen, mit Topping bestreuen.", "duration_min": None}
            ]
        },
        {
            "name": "Schweinelachssteaks mit Kartoffeln und Bohnen",
            "kcal_per_serving": 664,
            "active_cooking_time_min": 15,
            "total_time_min": 35,
            "tags": ["Fleisch", "Kartoffeln", "Gesund"],
            "ingredients": [
                {"name": "Schweinelachssteaks", "quantity": 250, "unit": "g"},
                {"name": "Kartoffeln (Drillinge)", "quantity": 600, "unit": "g"},
                {"name": "Buschbohnen", "quantity": 200, "unit": "g"},
                {"name": "Tomate", "quantity": 1, "unit": "Stück"},
                {"name": "Petersilie", "quantity": 10, "unit": "g"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Hello Patatas", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Kartoffeln: Kartoffeln vierteln, mit Hello Patatas und Öl mischen. 25-30 Min. backen.", "duration_min": 30},
                {"step_number": 2, "description": "Bohnen: Bohnen 8-9 Min. in Salzwasser kochen, abschrecken.", "duration_min": 10},
                {"step_number": 3, "description": "Steaks anbraten: Steaks salzen/pfeffern. In Öl ca. 3-5 Min. je Seite braten.", "duration_min": 10},
                {"step_number": 4, "description": "Kräuterbutter: Kräuter hacken. Mit Butter, Salz, Pfeffer mischen.", "duration_min": 3},
                {"step_number": 5, "description": "Bohnen anbraten: Bohnen 2 Min. braten. Knoblauch 1 Min., Tomatenwürfel 1 Min. mitbraten. Kräuter unterrühren.", "duration_min": 5},
                {"step_number": 6, "description": "Anrichten: Mit Kräuterbutter auf den Steaks servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Orangen-Hähnchengeschnetzeltes mit Reis",
            "kcal_per_serving": 646,
            "active_cooking_time_min": 15,
            "total_time_min": 30,
            "tags": ["Fleisch", "Reis", "Viel Gemüse"],
            "ingredients": [
                {"name": "Hähnchengeschnetzeltes", "quantity": 250, "unit": "g"},
                {"name": "Jasminreis", "quantity": 150, "unit": "g"},
                {"name": "Orange", "quantity": 0.5, "unit": "Stück"},
                {"name": "Zucchini", "quantity": 0.5, "unit": "Stück"},
                {"name": "Karotte", "quantity": 0.5, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Frühlingszwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Sweet Chili Soße", "quantity": 50, "unit": "g"},
                {"name": "Sojasoße", "quantity": 25, "unit": "ml"},
                {"name": "Maisstärke", "quantity": 6, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Reis kochen: Reis in Salzwasser 10 Min. köcheln, 10 Min. ziehen lassen.", "duration_min": 25},
                {"step_number": 2, "description": "Gemüse: Frühlingszwiebel, Karotte und Zucchini in Stücke schneiden. Knoblauch hacken.", "duration_min": 5},
                {"step_number": 3, "description": "Soße: Orangensaft auspressen. Mit Sweet Chili Sauce, Sojasoße, Stärke, Wasser, Zucker und Pfeffer mischen.", "duration_min": 5},
                {"step_number": 4, "description": "Hähnchen anbraten: Hähnchen 3-6 Min. scharf braten, herausnehmen.", "duration_min": 6},
                {"step_number": 5, "description": "Fertigstellen: Karotten, Zucchini, Knoblauch, weiße Frühlingszwiebel 3-6 Min. braten. Soße zufügen, 1-2 Min. köcheln. Hähnchen untermischen.", "duration_min": 8},
                {"step_number": 6, "description": "Anrichten: Mit grüner Frühlingszwiebel garnieren.", "duration_min": None}
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
