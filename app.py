from flask import Flask, render_template, request
from recipe_scrapers import scrape_html
from curl_cffi import requests as crequests
import pymongo

app = Flask(__name__)
try:
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    myDB = myclient["MyFullDB"]
    mycol = myDB["recipes"]
    myclient.server_info()
except Exception as e:
    print(f"MongoDB Connection Error: {e}")
@app.route('/', methods=['GET', 'POST'])
def get_recipe():
    ingredients, instructions, error = None, None, None


    if request.method == 'POST':
        url = request.form.get('recipe_url')
        try:

            res = crequests.get(url, impersonate="chrome110", timeout=15)
            res.raise_for_status()


            scraper = scrape_html(html=res.text, org_url=url)


            ingredients = scraper.ingredients()
            title  = scraper.title()
            instructions = scraper.instructions_list()


            if not ingredients or not instructions :
                error = "Site loaded, but no recipe data could be found."
            else: x = mycol.insert_one({
                "url": url,
                "title": title,
                "ingredients": ingredients,
                "instructions": instructions
            })


        except Exception as e:
            error = f"Error: {str(e)}"



    return render_template("index.html", error=error)
@app.route('/get_full_data', methods=['GET', 'POST'])
def get_full_data():
    titles= mycol.distinct("title")
    return render_template("full_list.html",title=titles)



if __name__ == '__main__':
    app.run(debug=True)