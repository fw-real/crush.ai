from flask import Flask, request, redirect, url_for, render_template, flash, abort
from flask_socketio import SocketIO, emit
from flask_toastr import Toastr
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
import requests, os
from characterai import PyCAI
import psycopg2
import dotenv

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['TOASTR_TIMEOUT'] = 5000
app.config['TOASTR_POSITION_CLASS'] = 'toast-top-left'
socketio = SocketIO(app)
toastr = Toastr(app)
bcrypt = Bcrypt(app)
dotenv.load_dotenv()

token = str(os.getenv("TOKEN"))
charid = str(os.getenv("CHAR_ID"))
url = str(os.getenv("POSTGRES_URL"))

login_manager = LoginManager()
login_manager.init_app(app)


def connect(postgres_url):
    return psycopg2.connect(postgres_url)

def insert_user(username, password, chat_id):
    conn = connect(url)
    cur = conn.cursor()
    cur.execute("insert into users(username, password, chat_id) values(%s, %s, %s)", (username, password, chat_id))
    conn.commit()
    conn.close()

def get_user(username):
    conn = connect(url)
    cur = conn.cursor()
    cur.execute("select * from users where username=%s", (username,))
    user = cur.fetchone()
    conn.close()
    return user

def chat_response(char_id, chat_id, message):
    response = requests.get("https://c-ai-api.onrender.com/chat", params={"char_id": char_id, "chat_id": chat_id, "message": message})
    return response.json()["detail"]

def get_chats(chat_id):
    response = requests.get("https://c-ai-api.onrender.com/chats", params={"chatid": chat_id})
    e = response.json()["detail"]
    for i in e:
        if i["author"] == "Touka Kirishima":
            i["author"] = "Touka"
    return e


def migrate(chat_id):
    requests.get("https://c-ai-api.onrender.com/migrate", params={"chat_id": chat_id})

class User(UserMixin):
    def __init__(self, username, password, chat_id):
        self.username = username
        self.password = password
        self.chat_id = chat_id

    def get_id(self):
        return self.username

@login_manager.user_loader
def load_user(username):
    user = get_user(username)
    if user:
        return User(user[0], user[1], user[2])
    return None

@login_manager.unauthorized_handler
def unauthorized_callback():
    flash("Kindly login to access that page!", "error")
    return redirect(url_for('home'))

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            flash("Username and Password are required!", "error")
            return redirect(url_for('register'))
        user = get_user(username)
        if user:
            flash("Username already exists!", "error")
            return redirect(url_for('register'))
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        client = PyCAI(token)
        new = client.chat.new_chat(charid)
        chat_id = new["external_id"]
        migrate(chat_id)
        insert_user(username, hashed_password, chat_id)
        flash("Successfully registered, kindly login now!", 'success')
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    if not request.is_json:
        abort(400)
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        abort(400)
    conn = connect(url)
    cur = conn.cursor()
    cur.execute("select * from users where username=%s", (username,))
    user = cur.fetchone()
    conn.close()
    if not user or not bcrypt.check_password_hash(user[1], password):
        abort(401)
    login_user(User(user[0], user[1], user[2]))
    flash('Logged in successfully!', 'uccess')
    return redirect(url_for('chat'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/chat')
@login_required
def chat():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    print(current_user.chat_id)
    try:
        messages = get_chats(current_user.chat_id)
    except Exception as err:
        print(err)
        messages = []
    emit('messages', messages)

@socketio.on('message')
def handle_message(message):
    print('Received message:', message)
    if message == "newchatweeitherrealingornothinglilbro9090$":
        client = PyCAI(token)
        new = client.chat.new_chat(charid)
        current_user.chat_id = new["external_id"]
        conn = connect(url)
        cur = conn.cursor()
        cur.execute("update users set chat_id=%s where username=%s", (current_user.chat_id, current_user.username))
        conn.commit()
        conn.close()
        migrate(current_user.chat_id)
        emit('newchat_notification', 'New chat created successfully!')      
    elif message == "logoutweeitherrealingornothinglilbro9090$":
        emit('logout_notification', "Logged out successfully")
        return redirect(url_for('home'))
    else:
        response = chat_response(charid, current_user.chat_id, message)
        emit('response', response)

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, host='0.0.0.0')
