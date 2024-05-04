from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit
from characterai import PyCAI
import requests, os, dotenv

app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app)
dotenv.load_dotenv()

token = str(os.getenv("TOKEN"))
charid = str(os.getenv("CHAR_ID"))

def chat_response(char_id, chat_id, message):
    response = requests.get("https://c-ai-api.onrender.com/chat", params={"char_id": char_id, "chat_id": chat_id, "message": message})
    return response.json()["detail"]

def migrate(chat_id):
    requests.get("https://c-ai-api.onrender.com/migrate", params={"chat_id": chat_id})

@app.route("/")
def home():
    base_url = request.base_url
    return {"message": f"Welcome to the Character AI API. To start a chat, go to {base_url}chat"}
@app.route('/chat')
def index():
    global chat_id
    client = PyCAI(token)
    new = client.chat.new_chat(charid)
    chat_id = new["external_id"]
    migrate(chat_id)
    session['chat_id'] = chat_id
    return render_template('index.html')

@socketio.on('message')
def handle_message(message):
    print('Received message:', message)
    chat_id = session.get('chat_id')  # Retrieve chat_id from session
    if chat_id:
        response = chat_response(charid, chat_id, message)
        emit('response', response)
    else:
        # Handle the case when chat_id is not found in session
        emit('response', "Error: Chat ID not found in session")

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, host='0.0.0.0')
