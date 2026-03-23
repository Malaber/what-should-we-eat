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
            "name": "Überbackener Seelachs mit Kartoffeln und Gurkensalat",
            "kcal_per_serving": 680,
            "active_cooking_time_min": 20,
            "total_time_min": 35,
            "tags": ["Fisch", "Kartoffeln", "Gesund"],
            "ingredients": [
                {"name": "Seelachs", "quantity": 250, "unit": "g"},
                {"name": "mehligkochende Kartoffeln", "quantity": 600, "unit": "g"},
                {"name": "Gurke", "quantity": 1, "unit": "Stück"},
                {"name": "Dill", "quantity": 10, "unit": "g"},
                {"name": "Zwiebel", "quantity": 10, "unit": "g"},
                {"name": "Knoblauchzehe", "quantity": 1, "unit": "Stück"},
                {"name": "Schmand", "quantity": 100, "unit": "g"},
                {"name": "Semmelbrösel", "quantity": 25, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Kartoffeln kochen: Kartoffeln schälen, in Stücke schneiden und in Salzwasser weich kochen.", "duration_min": 20},
                {"step_number": 2, "description": "Fisch vorbereiten: Fisch in Auflaufform geben, salzen und pfeffern.", "duration_min": 5},
                {"step_number": 3, "description": "Kruste machen: Semmelbrösel, gepressten Knoblauch, etwas Öl vermengen und auf dem Fisch verteilen. Im Ofen backen.", "duration_min": 15},
                {"step_number": 4, "description": "Gurkensalat: Gurke hobeln, mit gehacktem Dill, Zwiebeln, etwas Schmand, Salz und Pfeffer vermengen.", "duration_min": 5},
                {"step_number": 5, "description": "Kartoffelstampf: Gekochte Kartoffeln abgießen, mit restlichem Schmand und etwas Butter stampfen.", "duration_min": 5},
                {"step_number": 6, "description": "Anrichten: Fisch mit Kartoffelstampf und Gurkensalat servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Sriracha-Beef-Burger mit Süßkartoffel-Pommes",
            "kcal_per_serving": 950,
            "active_cooking_time_min": 25,
            "total_time_min": 35,
            "tags": ["Fleisch", "Kartoffeln"],
            "ingredients": [
                {"name": "Rinderhackfleisch", "quantity": 200, "unit": "g"},
                {"name": "Brioche Bun", "quantity": 2, "unit": "Stück"},
                {"name": "Gouda gerieben", "quantity": 50, "unit": "g"},
                {"name": "Süßkartoffel", "quantity": 300, "unit": "g"},
                {"name": "Teriyakisoße", "quantity": 50, "unit": "ml"},
                {"name": "Sriracha Sauce", "quantity": 8, "unit": "ml"},
                {"name": "Mayonnaise", "quantity": 25, "unit": "g"},
                {"name": "Naturjoghurt", "quantity": 75, "unit": "g"},
                {"name": "Limette", "quantity": 1, "unit": "Stück"}
            ],
            "steps": [
                {"step_number": 1, "description": "Süßkartoffeln backen: In Stifte schneiden, mit Öl und Salz vermengen. 25 Min backen.", "duration_min": 25},
                {"step_number": 2, "description": "Soßen rühren: Mayo, Joghurt und Sriracha verrühren. Limettensaft hinzugeben.", "duration_min": 5},
                {"step_number": 3, "description": "Patties braten: Hackfleisch zu Patties formen. In Pfanne braten, mit Teriyakisoße ablöschen.", "duration_min": 10},
                {"step_number": 4, "description": "Käse schmelzen: Gouda auf die Patties geben und schmelzen lassen.", "duration_min": 2},
                {"step_number": 5, "description": "Anrichten: Buns rösten, mit Soße bestreichen, Patties darauf legen und mit Pommes servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Gigli-Pasta mit Rindfleisch in Tomaten-Sahnesoße",
            "kcal_per_serving": 820,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Pasta", "Fleisch", "Schnell"],
            "ingredients": [
                {"name": "Rinderhackfleischzubereitung", "quantity": 200, "unit": "g"},
                {"name": "Gigli Nudeln", "quantity": 250, "unit": "g"},
                {"name": "Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauchzehe", "quantity": 1, "unit": "Stück"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Tomatenpesto", "quantity": 25, "unit": "g"},
                {"name": "Hartkäse geraspelt", "quantity": 40, "unit": "g"},
                {"name": "Harissa Gewürz", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Pasta kochen: Gigli in Salzwasser al dente kochen.", "duration_min": 10},
                {"step_number": 2, "description": "Fleisch braten: Hackfleisch mit gehackter Zwiebel und Knoblauch krümelig braten.", "duration_min": 8},
                {"step_number": 3, "description": "Würzen: Harissa-Gewürz zugeben und kurz mitbraten.", "duration_min": 2},
                {"step_number": 4, "description": "Soße kochen: Mit Kochsahne, Tomatenpesto und etwas Nudelwasser ablöschen. Köcheln lassen.", "duration_min": 5},
                {"step_number": 5, "description": "Anrichten: Pasta unterrühren, auf Tellern verteilen und mit Käse bestreuen.", "duration_min": None}
            ]
        },
        {
            "name": "Veganes Filet nach Lachs-Art mit Kartoffelsalat",
            "kcal_per_serving": 710,
            "active_cooking_time_min": 20,
            "total_time_min": 30,
            "tags": ["Vegetarisch", "Kartoffeln", "Gesund"],
            "ingredients": [
                {"name": "Veganes Filet (Vivera)", "quantity": 200, "unit": "g"},
                {"name": "festkochende Kartoffeln", "quantity": 600, "unit": "g"},
                {"name": "Gemüsebrühe", "quantity": 10, "unit": "ml"},
                {"name": "mittelscharfer Senf", "quantity": 10, "unit": "ml"},
                {"name": "Hafer-Cuisine", "quantity": 200, "unit": "ml"},
                {"name": "Petersilie", "quantity": 10, "unit": "g"},
                {"name": "Salatgurke", "quantity": 1, "unit": "Stück"},
                {"name": "Schalotte", "quantity": 1, "unit": "Stück"}
            ],
            "steps": [
                {"step_number": 1, "description": "Kartoffeln kochen: Kartoffeln in Scheiben schneiden und in Brühe kochen.", "duration_min": 15},
                {"step_number": 2, "description": "Dressing mixen: Senf, Hafer-Cuisine, gehackte Schalotte und Petersilie zu einem Dressing verrühren.", "duration_min": 5},
                {"step_number": 3, "description": "Salat zubereiten: Gurke in Scheiben hobeln, zu den abgetropften Kartoffeln geben und mit dem Dressing vermengen.", "duration_min": 5},
                {"step_number": 4, "description": "Filet braten: Veganes Filet in einer Pfanne von beiden Seiten goldbraun anbraten.", "duration_min": 6},
                {"step_number": 5, "description": "Anrichten: Filet mit dem lauwarmen Kartoffel-Gurken-Salat servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Bacon-Tomaten-Wraps mit Salatherzen",
            "kcal_per_serving": 650,
            "active_cooking_time_min": 15,
            "total_time_min": 15,
            "tags": ["Tacos", "Fleisch", "Schnell"],
            "ingredients": [
                {"name": "Weizentortillas", "quantity": 250, "unit": "g"},
                {"name": "Bacon (Scheiben)", "quantity": 100, "unit": "g"},
                {"name": "Tomate", "quantity": 2, "unit": "Stück"},
                {"name": "Salatherz", "quantity": 1, "unit": "Stück"},
                {"name": "Buttermilch-Zitronen-Dressing", "quantity": 50, "unit": "ml"},
                {"name": "Mayonnaise", "quantity": 50, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Bacon braten: Bacon in einer Pfanne ohne Öl knusprig auslassen.", "duration_min": 5},
                {"step_number": 2, "description": "Vorbereitung: Tomaten würfeln, Salat in Streifen schneiden.", "duration_min": 5},
                {"step_number": 3, "description": "Soße mixen: Mayonnaise und Buttermilch-Dressing verrühren.", "duration_min": 2},
                {"step_number": 4, "description": "Wraps erwärmen: Tortillas kurz in Mikrowelle oder Pfanne erwärmen.", "duration_min": 2},
                {"step_number": 5, "description": "Anrichten: Wraps mit Salat, Tomaten, Bacon und Dressing füllen.", "duration_min": None}
            ]
        },
        {
            "name": "Salsiccia-Rigatoni in Gemüse-Sahnesoße",
            "kcal_per_serving": 780,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Pasta", "Fleisch", "Schnell", "Viel Gemüse"],
            "ingredients": [
                {"name": "Salsiccia", "quantity": 100, "unit": "g"},
                {"name": "Rigatoni", "quantity": 270, "unit": "g"},
                {"name": "Mediterraner Gemüsemix", "quantity": 200, "unit": "g"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Hühnerbrühe", "quantity": 4, "unit": "g"},
                {"name": "Hartkäse geraspelt", "quantity": 40, "unit": "g"},
                {"name": "Maisstärke", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Pasta kochen: Rigatoni in kochendem Salzwasser al dente garen.", "duration_min": 11},
                {"step_number": 2, "description": "Salsiccia braten: Wurstbrät aus der Hülle drücken und in einer Pfanne krümelig braten.", "duration_min": 6},
                {"step_number": 3, "description": "Gemüse zugeben: Mediterranen Gemüsemix hinzufügen und mitbraten.", "duration_min": 5},
                {"step_number": 4, "description": "Soße: Brust mit Kochsahne und Brühe ablöschen. Mit Maisstärke andicken und köcheln.", "duration_min": 5},
                {"step_number": 5, "description": "Anrichten: Nudeln mit der Soße vermengen, auf Tellern anrichten und mit Käse bestreuen.", "duration_min": None}
            ]
        },
        {
            "name": "Ofen-Hähnchenbrust mit Aprikosenchutney und Gemüse",
            "kcal_per_serving": 590,
            "active_cooking_time_min": 15,
            "total_time_min": 35,
            "tags": ["Fleisch", "Kartoffeln", "Viel Gemüse"],
            "ingredients": [
                {"name": "Hähnchenbrustfilet", "quantity": 250, "unit": "g"},
                {"name": "Aprikosenchutney", "quantity": 50, "unit": "g"},
                {"name": "rote Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Blumenkohl", "quantity": 1, "unit": "Stück"},
                {"name": "Ofenkartoffel", "quantity": 200, "unit": "g"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "Piri-Piri Gewürz", "quantity": 6, "unit": "g"},
                {"name": "Naturjoghurt", "quantity": 75, "unit": "g"},
                {"name": "Kokos Curry", "quantity": 2, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Gemüse schneiden: Kartoffeln, Karotten, Zwiebeln und Blumenkohl in mundgerechte Stücke schneiden.", "duration_min": 10},
                {"step_number": 2, "description": "Ofengemüse backen: Gemüse mit Öl, Salz und Kokos-Curry auf dem Blech verteilen. 25 Min backen.", "duration_min": 25},
                {"step_number": 3, "description": "Hähnchen braten: Hähnchenbrust mit Piri-Piri würzen und in der Pfanne anbraten.", "duration_min": 10},
                {"step_number": 4, "description": "Dip anrühren: Joghurt leicht salzen und pfeffern.", "duration_min": 2},
                {"step_number": 5, "description": "Anrichten: Hähnchen mit Ofengemüse, Aprikosenchutney und Joghurt servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Pulled Pork Tacos mit Avocado-Salsa",
            "kcal_per_serving": 710,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Tacos", "Fleisch", "Schnell"],
            "ingredients": [
                {"name": "Pulled Pork", "quantity": 250, "unit": "g"},
                {"name": "Weizentortillas", "quantity": 200, "unit": "g"},
                {"name": "Avocado", "quantity": 1, "unit": "Stück"},
                {"name": "Tomate", "quantity": 1, "unit": "Stück"},
                {"name": "rote Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Koriander", "quantity": 10, "unit": "g"},
                {"name": "Limette", "quantity": 1, "unit": "Stück"},
                {"name": "Ketchup", "quantity": 25, "unit": "g"},
                {"name": "Hello Cajun Gewürz", "quantity": 4, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Salsa machen: Avocado würfeln, Tomate und Zwiebel fein hacken. Mit Koriander und Limettensaft mischen.", "duration_min": 10},
                {"step_number": 2, "description": "Pulled Pork erwärmen: Fleisch in einer Pfanne zerzupfen und mit Cajun-Gewürz und Ketchup erhitzen.", "duration_min": 8},
                {"step_number": 3, "description": "Tortillas erwärmen: Tortillas in Pfanne oder Mikrowelle heiß machen.", "duration_min": 2},
                {"step_number": 4, "description": "Anrichten: Tortillas mit heißem Pulled Pork und frischer Avocado-Salsa füllen.", "duration_min": None}
            ]
        },
        {
            "name": "Hähnchengeschnetzeltes mit Penne und Brokkoli",
            "kcal_per_serving": 730,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Pasta", "Fleisch", "Viel Gemüse"],
            "ingredients": [
                {"name": "Hähnchengeschnetzeltes", "quantity": 250, "unit": "g"},
                {"name": "Penne", "quantity": 270, "unit": "g"},
                {"name": "Brokkoli", "quantity": 1, "unit": "Stück"},
                {"name": "Tomate", "quantity": 1, "unit": "Stück"},
                {"name": "Knoblauchzehe", "quantity": 1, "unit": "Stück"},
                {"name": "Hühnerbrühe", "quantity": 4, "unit": "g"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Tomatenmark", "quantity": 17, "unit": "g"},
                {"name": "Hello Buon Appetito Gewürz", "quantity": 2, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Pasta kochen: Penne in Salzwasser kochen, Brokkoliröschen die letzten 5 Min. mitkochen.", "duration_min": 12},
                {"step_number": 2, "description": "Fleisch braten: Hähnchengeschnetzeltes mit Knoblauch anbraten.", "duration_min": 7},
                {"step_number": 3, "description": "Soße ansetzen: Tomatenmark zugeben, mit Kochsahne und Brühe ablöschen. Gewürz unterrühren.", "duration_min": 5},
                {"step_number": 4, "description": "Tomaten zugeben: Gewürfelte Tomaten unterheben und einköcheln.", "duration_min": 3},
                {"step_number": 5, "description": "Anrichten: Penne und Brokkoli unter die Soße mischen und servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Rindfleisch-Burger mit Karotten-Kartoffel-Fritten",
            "kcal_per_serving": 810,
            "active_cooking_time_min": 20,
            "total_time_min": 35,
            "tags": ["Fleisch", "Kartoffeln"],
            "ingredients": [
                {"name": "Rinderhackfleisch", "quantity": 200, "unit": "g"},
                {"name": "Brioche Bun", "quantity": 2, "unit": "Stück"},
                {"name": "Worcester Sauce", "quantity": 8, "unit": "ml"},
                {"name": "Zwiebel", "quantity": 1, "unit": "Stück"},
                {"name": "Tomatenmark", "quantity": 70, "unit": "g"},
                {"name": "Mayonnaise", "quantity": 50, "unit": "g"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "Ofenkartoffel", "quantity": 300, "unit": "g"},
                {"name": "Schnittlauch", "quantity": 10, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Fritten backen: Karotten und Kartoffeln in Stifte schneiden, mit Öl backen.", "duration_min": 25},
                {"step_number": 2, "description": "Patties formen: Hackfleisch mit Worcester Sauce, Salz und Pfeffer mischen, Patties formen.", "duration_min": 5},
                {"step_number": 3, "description": "Zwiebeln braten: Zwiebel in Ringe schneiden und weich karamellisieren.", "duration_min": 10},
                {"step_number": 4, "description": "Patties braten: Burger-Patties in der gleichen Pfanne anbraten.", "duration_min": 6},
                {"step_number": 5, "description": "Anrichten: Buns rösten, mit Mayo, Patties und Zwiebeln belegen. Dazu Fritten servieren.", "duration_min": None}
            ]
        },
        {
            "name": "Seelachs in Dill-Sahne-Soße mit Basmatireis",
            "kcal_per_serving": 560,
            "active_cooking_time_min": 15,
            "total_time_min": 20,
            "tags": ["Fisch", "Reis", "Schnell", "Gesund"],
            "ingredients": [
                {"name": "Seelachs", "quantity": 250, "unit": "g"},
                {"name": "Basmatireis", "quantity": 150, "unit": "g"},
                {"name": "Gurke", "quantity": 1, "unit": "Stück"},
                {"name": "Schalotte", "quantity": 1, "unit": "Stück"},
                {"name": "Zitrone", "quantity": 1, "unit": "Stück"},
                {"name": "Dill", "quantity": 10, "unit": "g"},
                {"name": "Kochsahne", "quantity": 150, "unit": "g"},
                {"name": "Gemüsebrühpulver", "quantity": 4, "unit": "g"},
                {"name": "Senf", "quantity": 10, "unit": "ml"}
            ],
            "steps": [
                {"step_number": 1, "description": "Reis kochen: Basmatireis nach Packungsanweisung in leicht gesalzenem Wasser kochen.", "duration_min": 15},
                {"step_number": 2, "description": "Fisch braten: Seelachs in mundgerechte Stücke schneiden, in Öl braten.", "duration_min": 6},
                {"step_number": 3, "description": "Soße anrühren: Schalotte anschwitzen. Kochsahne, Senf, Brühe und gehackten Dill zufügen.", "duration_min": 5},
                {"step_number": 4, "description": "Gurkensalat: Gurke längs halbieren, Kerne entfernen, hobeln. Mit Zitronensaft anmachen.", "duration_min": 5},
                {"step_number": 5, "description": "Anrichten: Reis mit cremiger Seelachssoße und Gurkensalat servieren.", "duration_min": None}
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
