from flask import Flask, render_template, request
from recipe_scrapers import scrape_html
from curl_cffi import requests as crequests

app = Flask(__name__)

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
            instructions = scraper.instructions_list()

            if not ingredients:
                error = "Site loaded, but no recipe data could be found."


        except Exception as e:
            error = f"Error: {str(e)}"

    return render_template("index.html", ingredients=ingredients, instructions=instructions, error=error)


if __name__ == '__main__':
    app.run(debug=True)