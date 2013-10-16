# -*- coding: utf-8 -*-
u"""This is the web interface for Argyrodes.
"""

from collections import defaultdict
from flask import Flask, render_template
from pymongo import MongoClient

# Initialize the database
db = MongoClient('localhost', 27017).argyrodes

# Initialize Flask
app = Flask(__name__)
app.config.from_object('default_settings')

@app.route('/', methods=['GET'])
def index():
   # render_nominees = []
   # ns = defaultdict(list)

    for n in db.nominees.find({}, {'nominees' : {'$slice' : -1}, 'questionnaire'  : {'$slice' : -1}}):
        print n
        break
        #ns[x['id']].append(x['timestamp'])

    return 'awer' # render_template('index.html', nominees=, questionnaires=db.questionnaire.find())

if __name__ == '__main__':
    app.run(host=app.config['FLASK_HOST'], port=app.config['FLASK_PORT'])

