import re
from like_yandex import search
from flask import Flask
from flask import url_for, render_template, request, redirect

app = Flask(__name__)


@app.route('/')
def index():
    if request.args:
        mode = request.args['search_mode']
        req = request.args['search_for']
        options = {'ii': 'Обратный индекс', 'w2v': 'Word2Vec', 'd2v': 'Doc2Vec'}
        results = search(req, mode)

        return render_template('results.html', results=results,
                                               req=req,
                                               mode=options[mode])

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
