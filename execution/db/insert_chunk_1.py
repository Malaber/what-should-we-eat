import os
import json
from execution.db.database import SessionLocal
from execution.db.models import Recipe, Ingredient, InstructionStep, Tag

def seed_recipes():
    db = SessionLocal()
    
    recipes_data = [
        {
            "name": "Schweinefilet mit Aprikosensoße",
            "kcal_per_serving": 514,
            "active_cooking_time_min": 15,
            "total_time_min": 35,
            "tags": ["Fleisch", "Kartoffeln", "Viel Gemüse"],
            "ingredients": [
                {"name": "Schweinefilet", "quantity": 250, "unit": "g"},
                {"name": "Ofenkartoffel", "quantity": 250, "unit": "g"},
                {"name": "Karotte", "quantity": 120, "unit": "g"},
                {"name": "Salatherz", "quantity": 1, "unit": "Stück"},
                {"name": "rote Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Aprikosenkonfitüre", "quantity": 50, "unit": "g"},
                {"name": "Senf", "quantity": 5, "unit": "ml"},
                {"name": "Maisstärke", "quantity": 4, "unit": "g"},
                {"name": "Gemüsebrühepulver", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Gemüse rösten: Karotten und Kartoffeln in Scheiben, Zwiebel in Spalten schneiden. Mit Öl, Hello Patatas, Salz und Pfeffer 20-25 Min. backen.", "duration_min": 25},
                {"step_number": 2, "description": "Vorbereitung: Brühe aus Wasser, Brühepulver und Maisstärke vorbereiten. Schweinefilet in Medaillons schneiden.", "duration_min": 5},
                {"step_number": 3, "description": "Schweinefilet anbraten: Medaillons 2-3 Min. je Seite braten. Auf das Backblech geben und 8-10 Min. im Ofen garen.", "duration_min": 13},
                {"step_number": 4, "description": "Salat: Romanasalat in Streifen schneiden. Dressing aus Senf, Öl, Honig, Balsamicoessig, Wasser, Salz und Pfeffer anrühren.", "duration_min": 5},
                {"step_number": 5, "description": "Soße: Zwiebel und Knoblauch anschwitzen. Aprikosenkonfitüre und Essig einrühren. Mit Brühe ablöschen, 1-2 Min. köcheln. Butter einrühren.", "duration_min": 5},
                {"step_number": 6, "description": "Anrichten: Ofengemüse, Salat und Schweinefilet verteilen. Mit Soße servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Gemüse Gyoza mit Chili-Nudeln",
            "kcal_per_serving": 967,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Pasta", "Vegetarisch", "Schnell", "Viel Gemüse"],
            "ingredients": [
                {"name": "Gemüse Gyoza", "quantity": 200, "unit": "g"},
                {"name": "Chili-Nudeln", "quantity": 200, "unit": "g"},
                {"name": "Spitzpaprika", "quantity": 1, "unit": "Stück"},
                {"name": "Limette", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauch", "quantity": 1, "unit": "Stück"},
                {"name": "Erdnussbutter", "quantity": 50, "unit": "g"},
                {"name": "Sesamöl", "quantity": 20, "unit": "ml"},
                {"name": "Sojasoße", "quantity": 50, "unit": "ml"}
            ],
            "steps": [
                {"step_number": 1, "description": "Nudeln einweichen: Nudeln in heißem Wasser 3-5 Min. einweichen, abgießen und abschrecken.", "duration_min": 5},
                {"step_number": 2, "description": "Gemüse: Spitzpaprika in Streifen schneiden. Knoblauch abziehen. Limette vierteln.", "duration_min": 5},
                {"step_number": 3, "description": "Soße zubereiten: Sesamöl, Sojasoße, Chili-Mix, Erdnussbutter, Brühe, Limettensaft, Zucker, Wasser vermengen. Knoblauch dazupressen.", "duration_min": 5},
                {"step_number": 4, "description": "Gyoza braten: Spitzpaprika und Gyoza 5-7 Min. anbraten.", "duration_min": 7},
                {"step_number": 5, "description": "Chili-Nudeln anbraten: Gekochte Nudeln mit Soße in die Pfanne geben, 1-2 Min. einkochen.", "duration_min": 2},
                {"step_number": 6, "description": "Anrichten: Nudeln und Gyoza auf Tellern anrichten, mit Limette servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Perlencouscous mit Walnüssen und Zucchini",
            "kcal_per_serving": 576,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Vegetarisch", "Gesund"],
            "ingredients": [
                {"name": "Perlencouscous", "quantity": 150, "unit": "g"},
                {"name": "Zucchini", "quantity": 1, "unit": "Stück"},
                {"name": "Babyspinat", "quantity": 50, "unit": "g"},
                {"name": "Getrocknete Tomaten", "quantity": 75, "unit": "g"},
                {"name": "Sahnejoghurt", "quantity": 75, "unit": "g"},
                {"name": "Wildpreiselbeermarmelade", "quantity": 25, "unit": "g"},
                {"name": "Walnüsse", "quantity": 20, "unit": "g"},
                {"name": "Zitrone", "quantity": 1, "unit": "Stück"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Knoblauch farblos anschwitzen, Brühe und Mezze Gewürz zugeben. Mit Wasser ablöschen, salzen und aufkochen.", "duration_min": 3},
                {"step_number": 2, "description": "Couscous kochen: Perlencouscous ins kochende Wasser rühren und 12 Min. abgedeckt köcheln. Walnüsse 1-2 Min. anrösten.", "duration_min": 12},
                {"step_number": 3, "description": "Letzte Schritte: Zitrone abreiben und in Spalten schneiden. Tomaten, Petersilie und Minze hacken.", "duration_min": 5},
                {"step_number": 4, "description": "Zucchini schmoren: Zucchiniwürfel 2-3 Min. scharf anbraten. Knoblauch und Mezze Gewürz zufügen. Mit Wasser ablöschen und schmoren.", "duration_min": 6},
                {"step_number": 5, "description": "Dressing: Preiselbeermarmelade, Zitronensaft, Öl, Wasser verrühren. Spinat marinieren. Dann Spinat, Zitrone, Petersilie, Tomaten zu Couscous geben.", "duration_min": 5},
                {"step_number": 6, "description": "Anrichten: Couscous verteilen. Geschmorte Zucchini und Walnüsse darauf. Mit Joghurt servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Mexikanischer Bohnen-Mais-Auflauf",
            "kcal_per_serving": 802,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Tacos", "Vegetarisch", "Viel Gemüse"],
            "ingredients": [
                {"name": "Weizentortillas", "quantity": 200, "unit": "g"},
                {"name": "Kidneybohnen", "quantity": 390, "unit": "g"},
                {"name": "Avocado", "quantity": 1, "unit": "Stück"},
                {"name": "Mais", "quantity": 150, "unit": "g"},
                {"name": "Chilischote", "quantity": 0.5, "unit": "Stück"},
                {"name": "Limette", "quantity": 1, "unit": "Stück"},
                {"name": "saure Sahne", "quantity": 100, "unit": "g"},
                {"name": "Tomatenpesto", "quantity": 25, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Backofen vorheizen. Petersilie hacken. Chili in Streifen schneiden.", "duration_min": 5},
                {"step_number": 2, "description": "Bohnen backen: Bohnen und Mais abspülen. Mit Öl, Tomatenpesto, Paprika, Kumin 15 Min. backen.", "duration_min": 15},
                {"step_number": 3, "description": "Weiter geht's: Limette in Spalten schneiden. Avocado in Streifen schneiden und mit Limettensaft beträufeln.", "duration_min": 5},
                {"step_number": 4, "description": "Dip: Saure Sahne mit Limettensaft verrühren.", "duration_min": 3},
                {"step_number": 5, "description": "Tortillas aufbacken: In den letzten 2-3 Min. Tortillas mit in den Ofen geben.", "duration_min": 3},
                {"step_number": 6, "description": "Anrichten: Tortillas mit Dip und Bohnen bestreichen, mit Avocado toppen.", "duration_min": None}
            ]
        },
        {
            "name": "Gnocchi mit Blauschimmelkäse und Birne",
            "kcal_per_serving": 747,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Pasta", "Vegetarisch", "Schnell", "Kartoffeln"],
            "ingredients": [
                {"name": "frische Gnocchi", "quantity": 400, "unit": "g"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Blauschimmelkäse", "quantity": 150, "unit": "g"},
                {"name": "Birne", "quantity": 1, "unit": "Stück"},
                {"name": "Schnittlauch", "quantity": 10, "unit": "g"},
                {"name": "Babyspinat", "quantity": 50, "unit": "g"},
                {"name": "Walnüsse", "quantity": 20, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Birne würfeln/schneiden, Knoblauch hacken, Blauschimmelkäse in Stücke schneiden.", "duration_min": 5},
                {"step_number": 2, "description": "Walnüsse rösten: Walnüsse 1-2 Min. anrösten.", "duration_min": 2},
                {"step_number": 3, "description": "Gnocchi braten: Gnocchi 2-3 Min. braten. Thymian, Knoblauch und Birnenwürfel zugeben, 2-3 Min. braten.", "duration_min": 6},
                {"step_number": 4, "description": "Soße vollenden: Mit Sahne, Muskat, Wasser ablöschen. Blauschimmelkäse zugeben und 2-3 Min. köcheln bis geschmolzen.", "duration_min": 4},
                {"step_number": 5, "description": "Anrichten: Spinat unterheben, Gnocchi auf Teller verteilen. Mit Birnenscheiben und Walnüssen garnieren.", "duration_min": None}
            ]
        },
        {
            "name": "Gebratener Seelachs mit Gurkensalat",
            "kcal_per_serving": 602,
            "active_cooking_time_min": 15,
            "total_time_min": 30,
            "tags": ["Fisch", "Reis", "Gesund"],
            "ingredients": [
                {"name": "Seelachs", "quantity": 250, "unit": "g"},
                {"name": "Basmatireis", "quantity": 150, "unit": "g"},
                {"name": "Gurke", "quantity": 1, "unit": "Stück"},
                {"name": "Schalotte", "quantity": 1, "unit": "Stück"},
                {"name": "Zitrone", "quantity": 1, "unit": "Stück"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Senf", "quantity": 10, "unit": "ml"}
            ],
            "steps": [
                {"step_number": 1, "description": "Reis kochen: Reis in kochendes Wasser geben und 15 Min. köcheln. 10 Min. ziehen lassen.", "duration_min": 25},
                {"step_number": 2, "description": "Vorbereitung: Gurke hobeln, Kräuter hacken, Schalotte würfeln, Limette abreiben.", "duration_min": 5},
                {"step_number": 3, "description": "Salat: Kochsahne, Essig, Zitronensaft, Zucker, Kräuter verrühren. Gurkenscheiben hinzufügen.", "duration_min": 3},
                {"step_number": 4, "description": "Seelachs anbraten: Fisch auf Hautseite mit Schalotten 1-2 Min. anbraten.", "duration_min": 2},
                {"step_number": 5, "description": "Soße kochen: Fisch wenden, mit Brühe, Senf, Sahne, Kräutern und Wasser ablöschen, 2-3 Min. köcheln.", "duration_min": 3},
                {"step_number": 6, "description": "Anrichten: Reis auflockern. Alles auf Tellern anrichten.", "duration_min": None}
            ]
        },
        {
            "name": "Rigatoni mit Salsiccia und Mediterranem Mix",
            "kcal_per_serving": 995,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Pasta", "Fleisch", "Schnell"],
            "ingredients": [
                {"name": "Salsiccia", "quantity": 100, "unit": "g"},
                {"name": "Rigatoni", "quantity": 270, "unit": "g"},
                {"name": "Mediterraner Mix", "quantity": 200, "unit": "g"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Hartkäse gerieben", "quantity": 40, "unit": "g"},
                {"name": "Maisstärke", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Pasta kochen: Rigatoni in Salzwasser 11-12 Min. bissfest garen.", "duration_min": 12},
                {"step_number": 2, "description": "Vorbereitung: Wasser, Kochsahne, Brühe, Stärke und Pfeffer glatt rühren.", "duration_min": 3},
                {"step_number": 3, "description": "Salsiccia braten: Salsiccia aus Darm lösen und 2-3 Min. anbraten bis gebräunt. Beiseite stellen.", "duration_min": 3},
                {"step_number": 4, "description": "Mix braten: Mediterranen Mix 3-4 Min. anbraten. Mit Sahnemix ablöschen, aufkochen. Käse einrühren.", "duration_min": 5},
                {"step_number": 5, "description": "Anrichten: Rigatoni in Soße geben. Auf Teller verteilen, mit Salsiccia und Käse toppen.", "duration_min": None}
            ]
        },
        {
            "name": "Dukkah Ofengemüse mit Couscous",
            "kcal_per_serving": 731,
            "active_cooking_time_min": 15,
            "total_time_min": 35,
            "tags": ["Vegetarisch", "Viel Gemüse"],
            "ingredients": [
                {"name": "Couscous", "quantity": 150, "unit": "g"},
                {"name": "Hirtenkäse", "quantity": 100, "unit": "g"},
                {"name": "Paprika multicolor", "quantity": 1, "unit": "Stück"},
                {"name": "Zucchini", "quantity": 1, "unit": "Stück"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "Tomate", "quantity": 1, "unit": "Stück"},
                {"name": "Sahnejoghurt", "quantity": 150, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Paprika, Zucchini, Karotten in Stücke schneiden. Backofen vorheizen.", "duration_min": 10},
                {"step_number": 2, "description": "Tomaten/Kräuter: Tomaten würfeln, Zitrone achteln, Kräuter hacken.", "duration_min": 5},
                {"step_number": 3, "description": "Gemüse backen: Gemüse mit Öl, Dukkah, Salz und Pfeffer 20-25 Min. backen.", "duration_min": 25},
                {"step_number": 4, "description": "Couscous quellen: Zwiebel und Knoblauch anbraten, mit Wasser und Brühe ablöschen. Couscous zugeben, 5-8 Min. quellen.", "duration_min": 10},
                {"step_number": 5, "description": "Dip: Joghurt abschmecken. Tomaten mit Zitronensaft, Öl, Salz, Pfeffer marinieren.", "duration_min": 4},
                {"step_number": 6, "description": "Anrichten: Couscous auflockern, Kräuter untermischen. Gemüse, Käse, Tomaten darauf verteilen.", "duration_min": None}
            ]
        },
        {
            "name": "Aubergine Milanese mit Gnocchi in Tomatensoße",
            "kcal_per_serving": 637,
            "active_cooking_time_min": 25,
            "total_time_min": 35,
            "tags": ["Pasta", "Vegetarisch"],
            "ingredients": [
                {"name": "frische Gnocchi", "quantity": 400, "unit": "g"},
                {"name": "Aubergine", "quantity": 1, "unit": "Stück"},
                {"name": "Kirschtomaten Dose", "quantity": 400, "unit": "g"},
                {"name": "Rucola", "quantity": 50, "unit": "g"},
                {"name": "Panko-Mehl", "quantity": 50, "unit": "g"},
                {"name": "Balsamicocreme", "quantity": 12, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Aubergine in Scheiben schneiden. Petersilie und Knoblauch hacken.", "duration_min": 5},
                {"step_number": 2, "description": "Soße kochen: Petersilienstiele, Chili und Knoblauch anschwitzen. Mit Kirschtomaten und Wasser ablöschen, würzen, köcheln lassen.", "duration_min": 15},
                {"step_number": 3, "description": "Gnocchi braten: Gnocchi in Öl 6-8 Min. goldbraun anbraten.", "duration_min": 8},
                {"step_number": 4, "description": "Aubergine panieren/frittieren: Auberginenscheiben mehlieren, in Wasser tauchen, in Panko wenden. 2-3 Min. pro Seite in viel Öl frittieren.", "duration_min": 10},
                {"step_number": 5, "description": "Vollenden: Gnocchi zur Soße geben.", "duration_min": 2},
                {"step_number": 6, "description": "Anrichten: Gnocchi verteilen, Rucola und Balsamicocreme darüber. Aubergine darauf anrichten.", "duration_min": None}
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
