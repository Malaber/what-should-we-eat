import os
import json
from execution.db.database import SessionLocal
from execution.db.models import Recipe, Ingredient, InstructionStep, Tag

def seed_recipes():
    db = SessionLocal()
    
    recipes_data = [
        {
            "name": "Röstkartoffeln mit cremiger Kräuterseitlingsoße",
            "kcal_per_serving": 633,
            "active_cooking_time_min": 15,
            "total_time_min": 40,
            "tags": ["Kartoffeln", "Vegetarisch"],
            "ingredients": [
                {"name": "Kartoffeln", "quantity": 750, "unit": "g"},
                {"name": "Baby-Kräuterseitlinge", "quantity": 100, "unit": "g"},
                {"name": "Babyspinat", "quantity": 50, "unit": "g"},
                {"name": "Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Petersilie", "quantity": 10, "unit": "g"},
                {"name": "Hafer-Cuisine", "quantity": 100, "unit": "ml"},
                {"name": "vegane Mayonnaise", "quantity": 25, "unit": "g"},
                {"name": "Sojasoße", "quantity": 12.5, "unit": "ml"},
                {"name": "Hello Patatas", "quantity": 6, "unit": "g"},
                {"name": "Hello Smoky Paprika", "quantity": 3, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Kartoffeln backen: Kartoffeln in Scheiben schneiden. Mit Hello Patatas, Öl und Pfeffer 25-30 Min. im Ofen backen.", "duration_min": 30},
                {"step_number": 2, "description": "Gemüse vorbereiten: Pilze längs halbieren. Zwiebel, Knoblauch und Petersilie fein hacken.", "duration_min": 5},
                {"step_number": 3, "description": "Dip: Vegane Mayo mit der Hälfte der Petersilie und einem Viertel der Hafer-Cuisine verrühren.", "duration_min": 3},
                {"step_number": 4, "description": "Soße ansetzen: Pilze und Zwiebeln in Öl 3-4 Min. anbraten. Smoky Paprika und Knoblauch 1-2 Min. mitbraten. Ein weiteres Viertel Hafer-Cuisine und Sojasoße zum Ablöschen nutzen.", "duration_min": 7},
                {"step_number": 5, "description": "Soße vollenden: Spinat zugeben und 1-2 Min. köcheln lassen, bis er zusammenfällt.", "duration_min": 2},
                {"step_number": 6, "description": "Anrichten: Kartoffeln mit Soße anrichten. Mit restlicher Petersilie, Spinat und Dip toppen.", "duration_min": None}
            ]
        },
        {
            "name": "Tomaten-Walnuss Gnocchi mit Spinat",
            "kcal_per_serving": 572,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Pasta", "Vegetarisch", "Viel Gemüse", "Schnell"],
            "ingredients": [
                {"name": "frische Gnocchi", "quantity": 400, "unit": "g"},
                {"name": "rote Spitzpaprika", "quantity": 1, "unit": "Stück"},
                {"name": "Babyspinat", "quantity": 50, "unit": "g"},
                {"name": "Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Basilikum", "quantity": 10, "unit": "g"},
                {"name": "Tomatensugo", "quantity": 200, "unit": "g"},
                {"name": "Walnüsse", "quantity": 20, "unit": "g"},
                {"name": "Soja-Kochcrème", "quantity": 100, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Knoblauch abziehen. Zwiebel würfeln. Paprika in 1 cm Stücke. Basilikum hacken.", "duration_min": 5},
                {"step_number": 2, "description": "Soße kochen: Zwiebeln anbraten. Paprikawürfel, Basilikumstiele und Knoblauch 5 Min. anbraten. Mit Tomatensugo und Wasser ablöschen, 4-6 Min. köcheln. Basilikum zugeben.", "duration_min": 15},
                {"step_number": 3, "description": "Gnocchi braten: Walnüsse 1-2 Min. rösten. Gnocchi in Öl 7-8 Min. anbraten.", "duration_min": 10},
                {"step_number": 4, "description": "Soße vollenden: Kochcrème unterrühren. Spinat portionsweise zugeben.", "duration_min": 2},
                {"step_number": 5, "description": "Anrichten: Gnocchi verteilen, mit Petersilien-Walnuss-Öl und Basilikum garnieren.", "duration_min": None}
            ]
        },
        {
            "name": "Süßkartoffel-Eintopf mit Paprika und Mandeln",
            "kcal_per_serving": 648,
            "active_cooking_time_min": 15,
            "total_time_min": 35,
            "tags": ["Vegetarisch", "Viel Gemüse", "Kartoffeln"],
            "ingredients": [
                {"name": "Süßkartoffel", "quantity": 200, "unit": "g"},
                {"name": "Ofenkartoffel", "quantity": 200, "unit": "g"},
                {"name": "Paprika multicolor", "quantity": 1, "unit": "Stück"},
                {"name": "Babyspinat", "quantity": 75, "unit": "g"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Petersilie", "quantity": 10, "unit": "g"},
                {"name": "Tomatenmark", "quantity": 70, "unit": "g"},
                {"name": "saure Sahne", "quantity": 100, "unit": "g"},
                {"name": "Mandeln gehobelt", "quantity": 10, "unit": "g"},
                {"name": "Gemüsebrühepulver", "quantity": 8, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Gemüse schneiden: Zwiebel in Streifen. Kartoffeln und Süßkartoffeln in Würfel. Paprika in 2 cm Würfel. Karotte in Stücke.", "duration_min": 10},
                {"step_number": 2, "description": "Mandeln rösten: Mandeln 1-2 Min. rösten. Petersilie mit saurer Sahne mischen.", "duration_min": 3},
                {"step_number": 3, "description": "Gemüse anbraten: Zwiebeln und Kartoffelwürfel 2-3 Min. braten. Mehl bestäuben. Tomatenmark, Paprikagewürz und Butter zugeben.", "duration_min": 4},
                {"step_number": 4, "description": "Eintopf köcheln: Mit Brühe ablöschen, aufkochen. Süßkartoffel, Paprika, Karotte zugeben, 12-15 Min. köcheln.", "duration_min": 15},
                {"step_number": 5, "description": "Verfeinern: Spinat zugeben bis zusammengefallen.", "duration_min": 2},
                {"step_number": 6, "description": "Anrichten: Eintopf mit Sahne, Mandelblättchen und Öl garnieren.", "duration_min": None}
            ]
        },
        {
            "name": "Hähnchenbrust aus dem Ofen mit Gemüse",
            "kcal_per_serving": 578,
            "active_cooking_time_min": 15,
            "total_time_min": 35,
            "tags": ["Fleisch", "Kartoffeln"],
            "ingredients": [
                {"name": "Hähnchenbrustfilet in Lake", "quantity": 250, "unit": "g"},
                {"name": "Hirtenkäse", "quantity": 100, "unit": "g"},
                {"name": "Ofenkartoffel", "quantity": 200, "unit": "g"},
                {"name": "Champignons", "quantity": 100, "unit": "g"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Naturjoghurt", "quantity": 75, "unit": "g"},
                {"name": "Basilikumpaste", "quantity": 15, "unit": "ml"},
                {"name": "Tomate", "quantity": 1, "unit": "Stück"},
                {"name": "Hello Buon Appetito", "quantity": 4, "unit": "g"},
                {"name": "Hello Paprika", "quantity": 2, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Backofen vorheizen. Kartoffeln schneiden, Champignons halbieren, Tomaten würfeln.", "duration_min": 5},
                {"step_number": 2, "description": "Gemüse verteilen: Kartoffeln, Tomaten, Champignons in Schüssel mit halbem Käse, Knoblauch, Gewürz und Öl mischen.", "duration_min": 5},
                {"step_number": 3, "description": "Gemüse backen: Gemüse 25-30 Min. backen.", "duration_min": 30},
                {"step_number": 4, "description": "Hähnchen backen: Hähnchen mit Paprikagewürz einreiben. In den letzten 16-20 Min. zum Gemüse geben.", "duration_min": 20},
                {"step_number": 5, "description": "Dip: Restlichen Käse, Basilikumpaste und Joghurt verrühren.", "duration_min": 3},
                {"step_number": 6, "description": "Anrichten: Gebackenes Gemüse mit Hähnchen in Scheiben anrichten, mit Dip servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Bacon-Spätzlepfanne mit Spitzkohl",
            "kcal_per_serving": 819,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Pasta", "Fleisch", "Schnell"],
            "ingredients": [
                {"name": "Bacon Scheiben", "quantity": 100, "unit": "g"},
                {"name": "frische Eierspätzle", "quantity": 400, "unit": "g"},
                {"name": "Spitzkohl", "quantity": 0.5, "unit": "Stück"},
                {"name": "Gouda gerieben", "quantity": 50, "unit": "g"},
                {"name": "Kochsahne", "quantity": 75, "unit": "g"},
                {"name": "Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Schnittlauch", "quantity": 10, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Spitzkohl in Rauten, Zwiebel würfeln. Bacon in Streifen.", "duration_min": 5},
                {"step_number": 2, "description": "Spitzkohl braten: Zwiebel und Bacon 2-3 Min. braten. Kohl zugeben, 1-2 Min. braten. Mit Sahne und Wasser ablöschen, 10-15 Min. köcheln.", "duration_min": 17},
                {"step_number": 3, "description": "Spätzle zubereiten: Spätzle in Pfanne 5-7 Min. anbraten.", "duration_min": 7},
                {"step_number": 4, "description": "Spätzlepfanne: Gebratene Spätzle unter das Gemüse heben. Gouda darüber verteilen.", "duration_min": 2},
                {"step_number": 5, "description": "Anrichten: Spätzlepfanne anrichten, mit Schnittlauch bestreuen.", "duration_min": None}
            ]
        },
        {
            "name": "Süßkartoffel-Kokos-Eintopf mit Pfannkuchen",
            "kcal_per_serving": 1032,
            "active_cooking_time_min": 25,
            "total_time_min": 40,
            "tags": ["Vegetarisch", "Viel Gemüse"],
            "ingredients": [
                {"name": "Süßkartoffel", "quantity": 380, "unit": "g"},
                {"name": "schwarze Bohnen", "quantity": 1, "unit": "Dose"},
                {"name": "Avocado", "quantity": 1, "unit": "Stück"},
                {"name": "stückige Tomaten", "quantity": 390, "unit": "g"},
                {"name": "rote Chilischote", "quantity": 1, "unit": "Stück"},
                {"name": "Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Schnittlauch", "quantity": 10, "unit": "g"},
                {"name": "Kokosmilch", "quantity": 250, "unit": "ml"},
                {"name": "Hello Aloha", "quantity": 4, "unit": "g"},
                {"name": "Maisstärke", "quantity": 8, "unit": "g"},
                {"name": "Gemüsebrühepulver", "quantity": 6, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Zwiebel, Knoblauch würfeln. Süßkartoffel in Würfel. Kokosmilch mit Wasser und Brühe mischen.", "duration_min": 5},
                {"step_number": 2, "description": "Gemüse braten: Zwiebel und Knoblauch 3 Min. anschwitzen. Tomaten zugeben, 2 Min. garen.", "duration_min": 5},
                {"step_number": 3, "description": "Eintopf: Bohnen, Süßkartoffeln, Aloha-Gewürz, Kokosmischung zugeben, 20 Min. köcheln.", "duration_min": 20},
                {"step_number": 4, "description": "Pfannkuchenteig: Kräuter hacken, Chili hacken. Mit Kokosmilch, Stärke, Aloha, Mehl, Wasser verrühren.", "duration_min": 5},
                {"step_number": 5, "description": "Pfannkuchen braten: Dünne Pfannkuchen je Seite 2-3 Min ausbacken.", "duration_min": 10},
                {"step_number": 6, "description": "Anrichten: Eintopf mit Petersilie und Avocado toppen. Mit Pfannkuchen servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Hähnchen-Wraps mit Erdnussdip",
            "kcal_per_serving": 1010,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Fleisch", "Schnell", "Tacos"],
            "ingredients": [
                {"name": "Hähnchengeschnetzeltes", "quantity": 250, "unit": "g"},
                {"name": "Weizentortillas", "quantity": 200, "unit": "g"},
                {"name": "Avocado", "quantity": 1, "unit": "Stück"},
                {"name": "Paprika multicolor", "quantity": 1, "unit": "Stück"},
                {"name": "Blattsalatmischung", "quantity": 75, "unit": "g"},
                {"name": "Frühlingszwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Limette", "quantity": 1, "unit": "Stück"},
                {"name": "Erdnussbutter", "quantity": 50, "unit": "g"},
                {"name": "Erdnüsse gesalzen", "quantity": 40, "unit": "g"},
                {"name": "Sojasoße", "quantity": 25, "unit": "ml"},
                {"name": "Naturjoghurt", "quantity": 75, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Frühlingszwiebel in Ringe. Sojadressing aus Zwiebelringen, Limettensaft, Sojasoße, Zucker rühren.", "duration_min": 5},
                {"step_number": 2, "description": "Paprika & Dip: Paprika in Streifen schneiden. Erdnussdip aus Joghurt, Erdnussbutter und etwas Sojadressing rühren.", "duration_min": 4},
                {"step_number": 3, "description": "Fleisch braten: Tortillas erwärmen. Hähnchen 1-2 Min. anbraten, mit etwas Sojadressing 2-3 Min. fertigbraten.", "duration_min": 5},
                {"step_number": 4, "description": "Salat: Avocado in Stücke schneiden. Mit Paprika, Salat und restlichem Sojadressing vermengen.", "duration_min": 3},
                {"step_number": 5, "description": "Anrichten: Tortillas mit Dip bestreichen, mit Salat und Hähnchen belegen. Mit Erdnüssen toppen.", "duration_min": None}
            ]
        },
        {
            "name": "Rigatoni mit Hackfleisch und Champignons",
            "kcal_per_serving": 1039,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Pasta", "Fleisch", "Schnell"],
            "ingredients": [
                {"name": "Rinderhackfleisch", "quantity": 200, "unit": "g"},
                {"name": "Wildpreiselbeerenmarmelade", "quantity": 50, "unit": "g"},
                {"name": "Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Petersilie", "quantity": 10, "unit": "g"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Piment", "quantity": 0.5, "unit": "g"},
                {"name": "Hühnerbrühepulver", "quantity": 6, "unit": "g"},
                {"name": "Rigatoni", "quantity": 270, "unit": "g"},
                {"name": "braune Champignons", "quantity": 100, "unit": "g"},
                {"name": "Worcester Sauce", "quantity": 8, "unit": "ml"},
                {"name": "Senf", "quantity": 5, "unit": "ml"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Wasser kochen. Zwiebel würfeln/Streifen. Champignons halbieren. Kräuter hacken.", "duration_min": 5},
                {"step_number": 2, "description": "Pasta kochen: Rigatoni 9-11 Min. bissfest kochen, abgießen.", "duration_min": 11},
                {"step_number": 3, "description": "Zwiebeln anbraten: Zwiebelstreifen 4-5 Min. anbraten, beiseitestellen.", "duration_min": 5},
                {"step_number": 4, "description": "Ablöschen: Zwiebelwürfel, Fleisch, Champignons 3-4 Min. braten. Mit Wasser ablöschen. Brühepulver einrühren, 4-5 Min. köcheln.", "duration_min": 10},
                {"step_number": 5, "description": "Vollenden: Kochsahne, Worcester Sauce und Senf zugeben, 1-2 Min. köcheln.", "duration_min": 2},
                {"step_number": 6, "description": "Anrichten: Rigatoni zur Soße. Auf Teller mit Zwiebelstreifen, Kräutern und Preiselbeeren toppen.", "duration_min": None}
            ]
        },
        {
            "name": "Süßer Chili-Grill-Tofu mit Jasminreis",
            "kcal_per_serving": 1084,
            "active_cooking_time_min": 20,
            "total_time_min": 30,
            "tags": ["Vegetarisch", "Reis"],
            "ingredients": [
                {"name": "süßer Chili-Grill-Tofu", "quantity": 180, "unit": "g"},
                {"name": "Jasminreis", "quantity": 150, "unit": "g"},
                {"name": "Avocado", "quantity": 1, "unit": "Stück"},
                {"name": "Zucchini", "quantity": 1, "unit": "Stück"},
                {"name": "Frühlingszwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Limette", "quantity": 1, "unit": "Stück"},
                {"name": "Erdnüsse gesalzen", "quantity": 20, "unit": "g"},
                {"name": "Sweet Chili Soße", "quantity": 75, "unit": "g"},
                {"name": "Sojasoße", "quantity": 25, "unit": "ml"},
                {"name": "Panko-Mehl", "quantity": 50, "unit": "g"},
                {"name": "Maisstärke", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Reis kochen: Reis in Salzwasser 10 Min. köcheln, 10 Min. ziehen lassen.", "duration_min": 20},
                {"step_number": 2, "description": "Vorbereitung: Zucchini w Scheiben. Knoblauch, Limette und Erdnüsse hacken/schneiden.", "duration_min": 5},
                {"step_number": 3, "description": "Zucchini braten: Zucchini und Knoblauch 5-6 Min. anbraten.", "duration_min": 6},
                {"step_number": 4, "description": "Soße: Wasser, Stärke, Chili-Soße, Sojasoße, Zucker mischen. Gremolata aus Erdnüssen, Limettenabrieb, Zwiebeln, Limettensaft mischen. Zucchini mit Soße ablöschen.", "duration_min": 5},
                {"step_number": 5, "description": "Tofu frittieren: Tofu halbieren. In Mehlmischung tauchen, in Panko wenden. 2-3 Min je Seite in viel Öl anbraten.", "duration_min": 8},
                {"step_number": 6, "description": "Anrichten: Reis, Zucchini, Avocado, Tofu anrichten. Mit Gremolata toppen.", "duration_min": None}
            ]
        },
        {
            "name": "Pilz-Fiorelli in cremiger Spinatsoße",
            "kcal_per_serving": 992,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Pasta", "Vegetarisch", "Schnell"],
            "ingredients": [
                {"name": "Fiorelli mit Pilzfüllung", "quantity": 450, "unit": "g"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Babyspinat", "quantity": 75, "unit": "g"},
                {"name": "braune Champignons", "quantity": 150, "unit": "g"},
                {"name": "Hartkäse geraspelt", "quantity": 20, "unit": "g"},
                {"name": "Hartkäse gerieben", "quantity": 20, "unit": "g"},
                {"name": "Pinienkerne", "quantity": 10, "unit": "g"},
                {"name": "Hello Muskat", "quantity": 5, "unit": "g"},
                {"name": "milder Chili-Mix", "quantity": 2, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Wasser kochen. Öl mit Chili mischen. Champignons in Scheiben schneiden.", "duration_min": 5},
                {"step_number": 2, "description": "Champignons braten: Pinienkerne 2-3 Min. rösten. Champignons 3-4 Min. braten.", "duration_min": 6},
                {"step_number": 3, "description": "Soße zubereiten: Kochsahne, Wasser, Muskat 1 Min. aufkochen. Hälfte Spinat unterheben. Hartkäse (gerieben) zugeben und pürieren.", "duration_min": 5},
                {"step_number": 4, "description": "Pasta kochen: Fiorelli in kochendem Wasser 5-6 Min. gar ziehen lassen. Abgießen.", "duration_min": 6},
                {"step_number": 5, "description": "Vollenden: Soße aufkochen, restlichen Spinat zugeben. Fiorelli und Champignons untermengen.", "duration_min": 2},
                {"step_number": 6, "description": "Anrichten: Pasta verteilen, mit Chili-Öl, Kernen und geraspeltem Käse toppen.", "duration_min": None}
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
