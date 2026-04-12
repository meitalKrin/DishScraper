from flask import Flask, render_template, request, redirect, url_for
from recipe_scrapers import scrape_html
from curl_cffi import requests as crequests
import pymongo
import os
import certifi
import gc

app = Flask(__name__)

ca = certifi.where()
MONGO_URI = os.environ.get("MONGO_URI",
                           "mongodb+srv://km:km@cluster0.0kvlnbn.mongodb.net/MyFullDB?retryWrites=true&w=majority")

try:
    myclient = pymongo.MongoClient(MONGO_URI, tlsCAFile=ca)
    myDB = myclient["MyFullDB"]
    mycol = myDB["recipes"]
    myclient.admin.command('ping')
except Exception as e:
    print(f"Connection Error: {e}")


@app.route('/', methods=['GET', 'POST'])
def get_recipe():
    ingredients, instructions, error, msg = None, None, "", None

    if request.method == 'POST':
        url = request.form.get('recipe_url')
        res = None
        try:
            res = crequests.get(url, impersonate="chrome110", timeout=15)
            res.raise_for_status()

            try:
                scraper = scrape_html(html=res.text, org_url=url)

                def safe_get(func, default):
                    try:
                        return func() or default
                    except Exception:
                        return default

                title = safe_get(scraper.title, "Untitled Recipe")
                img = safe_get(scraper.image, "/static/place_holder.png")
                category = safe_get(scraper.category, "Uncategorized")
                cook = safe_get(scraper.cook_time, 0)
                prep = safe_get(scraper.prep_time, 0)
                total_cooking_time = cook + prep

                try:
                    raw_ingredients = scraper.ingredients()
                    ingredients = "\n".join([f"• {item}" for item in raw_ingredients if
                                             item]) if raw_ingredients else "No ingredients found."
                except Exception:
                    ingredients = "No ingredients found."

                try:
                    raw_instructions = scraper.instructions_list()
                    instructions = "\n".join([f"{i + 1}. {step}" for i, step in enumerate(raw_instructions) if
                                              step]) if raw_instructions else "No instructions found."
                except Exception:
                    instructions = "No instructions found."

                if ingredients == "No ingredients found." or instructions == "No instructions found.":
                    error = "Website is not supported or lacks recipe data."
                else:
                    result = mycol.update_one(
                        {"url": url},
                        {"$set": {
                            "img": img,
                            "title": title,
                            "cook_time": total_cooking_time,
                            "category": category,
                            "ingredients": ingredients,
                            "instructions": instructions
                        }},
                        upsert=True
                    )
                    msg = f"Saved: {title}" if result.matched_count == 0 else f"Updated: {title}"

                del scraper

            except Exception:
                error = "This website is not currently supported by the scraper."

        except Exception as e:
            error = f"Connection failed: {str(e)}"

        finally:
            if res:
                del res
            gc.collect()

    return render_template("index.html", msg=msg, error=error)


@app.route('/get_full_data', methods=['GET'])
def get_full_data():
    search_query = request.args.get('search')
    if search_query:
        regex_query = {"$regex": search_query, "$options": "i"}
        query = {"$or": [{"title": regex_query}, {"ingredients": regex_query}, {"category": regex_query}]}
        recipes = list(mycol.find(query))
    else:
        recipes = list(mycol.find({}))
    return render_template("full_list.html", recipes=recipes)


@app.route('/back_page', methods=['GET'])
def back_page():
    return redirect(url_for('get_recipe'))


@app.route('/delete_recipe')
def delete_recipe():
    url_to_delete = request.args.get('url')
    if url_to_delete:
        mycol.delete_one({"url": url_to_delete})
    return redirect(url_for('get_full_data'))


@app.route('/move_to_add_manual', methods=['GET'])
def move_to_add_manual():
    return render_template("add_manual.html")


@app.route('/add_manual', methods=['GET', 'POST'])
def add_manual():
    error, msg = None, None
    if request.method == 'POST':
        try:
            url = request.form.get('url') or "Manual Entry"
            img = request.form.get('img') or "/static/place_holder.png"
            title = request.form.get('title') or "Untitled Recipe"
            cook_time = request.form.get('cook_time') or 0
            category = request.form.get('category') or "Uncategorized"

            raw_ingredients = request.form.get('ingredients')
            if raw_ingredients:
                raw_ingredients = raw_ingredients.replace('  ', '\n')
                ing_list = [i.strip() for i in raw_ingredients.split('\n') if i.strip()]
                ingredients = "\n".join([f"• {item}" for item in ing_list])
            else:
                ingredients = "No ingredients found."

            raw_instructions = request.form.get('instructions')
            if raw_instructions:
                raw_instructions = raw_instructions.replace('  ', '\n')
                ins_list = [s.strip() for s in raw_instructions.split('\n') if s.strip()]
                instructions = "\n".join([f"{i + 1}. {step}" for i, step in enumerate(ins_list)])
            else:
                instructions = "No instructions found."

            result = mycol.update_one(
                {"url": url},
                {"$set": {"img": img, "title": title, "cook_time": cook_time, "category": category,
                          "ingredients": ingredients, "instructions": instructions}},
                upsert=True
            )
            msg = f"Saved: {title}" if result.matched_count == 0 else f"Updated: {title}"

        except Exception as e:
            error = f"Failed to save: {str(e)}"
    return render_template("add_manual.html", msg=msg, error=error)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)