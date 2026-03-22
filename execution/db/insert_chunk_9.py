import os
import json
from execution.db.database import SessionLocal
from execution.db.models import Recipe, Ingredient, InstructionStep, Tag

def seed_recipes():
    db = SessionLocal()
    
    recipes_data = [
        {
            "name": "Panierter Camembert auf Salat mit Äpfeln",
            "kcal_per_serving": 1074,
            "active_cooking_time_min": 15,
            "total_time_min": 25,
            "tags": ["Vegetarisch", "Schnell"],
            "ingredients": [
                {"name": "Camembert", "quantity": 250, "unit": "g"},
                {"name": "Apfel", "quantity": 1, "unit": "Stück"},
                {"name": "Salatherz (Romana)", "quantity": 120, "unit": "g"},
                {"name": "Karotte", "quantity": 1, "unit": "Stück"},
                {"name": "Kräuter-Croûtons", "quantity": 40, "unit": "g"},
                {"name": "Buttermilch-Zitronen-Dressing", "quantity": 50, "unit": "ml"},
                {"name": "Wildpreiselbeermarmelade", "quantity": 50, "unit": "g"},
                {"name": "Semmelbrösel", "quantity": 50, "unit": "g"},
                {"name": "mittelscharfer Senf", "quantity": 5, "unit": "ml"},
                {"name": "Mehl", "quantity": 50, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Vorbereitung: Karotte raspeln. Salat in dicke Streifen schneiden.", "duration_min": 5},
                {"step_number": 2, "description": "Apfel braten: Apfel achteln und 2-3 Min. in der Pfanne anbraten.", "duration_min": 4},
                {"step_number": 3, "description": "Camembert panieren: Mehl mit Wasser und Salz verrühren. Käse durch den flüssigen Teig ziehen und in Semmelbröseln wenden.", "duration_min": 5},
                {"step_number": 4, "description": "Salat: Buttermilch-Dressing mit Senf mischen. Mit Salat und Karotte vermengen.", "duration_min": 3},
                {"step_number": 5, "description": "Käse braten: Panierte Camemberts 2 Min. pro Seite in Öl goldbraun braten.", "duration_min": 5},
                {"step_number": 6, "description": "Anrichten: Salat mit Croûtons, Camembert und Apfelstücken anrichten. Preiselbeermarmelade dazu reichen.", "duration_min": None}
            ]
        },
        {
            "name": "Veganes Filet nach Lachs-Art mit Kräuterkartoffeln",
            "kcal_per_serving": 783,
            "active_cooking_time_min": 15,
            "total_time_min": 30,
            "tags": ["Vegetarisch", "Fisch", "Kartoffeln", "Gesund"],
            "ingredients": [
                {"name": "Veganes Filet nach Lachs-Art", "quantity": 200, "unit": "g"},
                {"name": "vorwiegend festkochende Kartoffeln", "quantity": 600, "unit": "g"},
                {"name": "kleine Salatgurke", "quantity": 1, "unit": "Stück"},
                {"name": "Schalotte", "quantity": 1, "unit": "Stück"},
                {"name": "Hafer-Cuisine", "quantity": 200, "unit": "ml"},
                {"name": "Kräftige vegane Gemüsebrühe", "quantity": 25, "unit": "g"},
                {"name": "mittelscharfer Senf", "quantity": 10, "unit": "ml"},
                {"name": "Petersilie glatt/Schnittlauch", "quantity": 10, "unit": "g"}
            ],
            "steps": [
                {"step_number": 1, "description": "Kartoffeln: Kartoffeln vierteln, in Salzwasser 15-18 Min. garen.", "duration_min": 20},
                {"step_number": 2, "description": "Vorbereitung: Kräuter hacken. Gurke in Halbmonde. Schalotte in kleine Würfel.", "duration_min": 5},
                {"step_number": 3, "description": "Gurkensalat: Gurke mit Essig, 1 EL Hafer-Cuisine, Hälfte Kräuter, Zucker, Salz, Pfeffer mischen.", "duration_min": 3},
                {"step_number": 4, "description": "Veganes Filet: Lachs-Alternative 2 Min. pro Seite anbraten, herausnehmen.", "duration_min": 5},
                {"step_number": 5, "description": "Soße: Schalotte anschwitzen. Hafer-Cuisine, Senf, Brühe und Wasser einrühren. 2-3 Min. köcheln.", "duration_min": 5},
                {"step_number": 6, "description": "Anrichten: Kartoffeln abgießen, mit Margarine und Rest-Kräutern mischen. Mit Salat, Soße und veganem Fisch anrichten.", "duration_min": None}
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
