from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import requests
app = Flask(__name__)
@app.route('/',methods=['GET','POST'])
def index():
    if request.method == 'POST':
        url_form_btn = request.form.get('recipe_url')
        print({url_form_btn})
        response = requests.get(url_form_btn)
        soup = BeautifulSoup(response.text, 'html.parser')
        full_text = soup.get_text()

        return f"clicked url: {full_text}"
    else: return render_template('templates.html')
if __name__ == '__main__':
    app.run(debug=True)


