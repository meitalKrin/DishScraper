from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import requests
app = Flask(__name__)
@app.route('/',methods=['GET','POST'])
def index():
    if request.method == 'POST':
        url_form_btn = request.form.get('recipe_url')
        print(f"clicked url: {url_form_btn}")
        return f"im going to use this later  {url_form_btn}"
    else: return render_template('templates.html')
if __name__ == '__main__':
    app.run(debug=True)