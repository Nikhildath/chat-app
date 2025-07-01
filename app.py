# Basic Chat App like WhatsApp using Flask (Python) + HTML + JS + MongoDB

from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta
from threading import Thread
import os
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MongoDB Atlas connection (reads from environment)
mongo_uri = os.environ.get("MONGO_URI")
client = MongoClient(mongo_uri)
db = client['chatapp']
messages_col = db['messages']

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat/<number>')
def chat(number):
    return render_template('chat.html', number=number)

@app.route('/send', methods=['POST'])
def send():
    data = request.json
    messages_col.insert_one({
        'number': data['number'],
        'message': data['message'],
        'timestamp': datetime.utcnow()
    })
    return jsonify({'status': 'sent'})

@app.route('/get/<number>', methods=['GET'])
def get(number):
    two_days_ago = datetime.utcnow() - timedelta(days=2)
    msgs = messages_col.find({
        'number': number,
        'timestamp': {'$gte': two_days_ago}
    }).sort('timestamp')
    result = [{'message': m['message'], 'time': m['timestamp'].strftime('%Y-%m-%d %H:%M')} for m in msgs]
    return jsonify(result)

@app.route('/upload/<number>', methods=['POST'])
def upload(number):
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        messages_col.insert_one({
            'number': number,
            'message': f"[image]{filename}",
            'timestamp': datetime.utcnow()
        })
    return jsonify({'status': 'uploaded'})

def delete_old_messages():
    while True:
        cutoff = datetime.utcnow() - timedelta(days=2)
        messages_col.delete_many({'timestamp': {'$lt': cutoff}})
        time.sleep(3600)  # Run every hour

Thread(target=delete_old_messages, daemon=True).start()

if __name__ == '__main__':
    app.run(debug=True)
