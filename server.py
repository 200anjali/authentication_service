from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
import psycopg2
import jwt
from datetime import datetime, timedelta
import redis
from flask_socketio import SocketIO, emit
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from utils import JWT_SECRET_KEY, FLASK_SECRET_KEY, DB_PASSWORD, DB_HOST, DB_NAME,DB_PORT, DB_USER, REDIS_HOST, REDIS_PORT

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
jwt = JWTManager(app)

def generate_jwt_token(username):
    expiration_time = datetime.utcnow() + timedelta(hours=1)
    payload = {'username': username, 'exp': expiration_time}
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
    return token

def connect_to_db():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

def connect_to_redis():
    return redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    if request.method=='POST':
        data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Invalid username or password'}), 400
    conn = connect_to_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE username = %s;", (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            return jsonify({'message': 'Username already exists'}), 400
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING userid;", (username, password))
        user_id=cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return jsonify({'message': 'Registration successful'}), 201

@app.route('/login', methods=['POST'])
def login():
    if request.method=='POST':
        data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'message': 'Invalid username or password'}), 400
    conn = connect_to_db()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM users WHERE username = %s AND password = %s;
        """, (username, password))
        user = cursor.fetchone()
    conn.close()
    if user:
        token = create_access_token(identity=username)
        print(token)
        
        redis_conn = connect_to_redis()
        redis_conn.set(f"online:{username}", "1")

        return jsonify({'message': 'Login Successful','token':token})
    else:
        return jsonify({'message': 'Invalid username or password'}), 401
    
@app.route('/welcome')
def welcome():
    conn = connect_to_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT userid, username FROM users;")
        users = [{'userid': user[0], 'username': user[1]} for user in cursor.fetchall()]
    conn.close()

    redis_conn = connect_to_redis()
    for user in users:
        user['online'] = redis_conn.get(f"online:{user['username']}") is not None
    
    print(users)
    return render_template('welcome.html', users=users)

@app.route('/logout',methods=['POST'])
@jwt_required()
def logout():
    print('logging out')
    data = request.json
    username = data.get('username')
    redis_conn = connect_to_redis()
    redis_conn.delete(f"online:{username}")
    print(redis_conn.get("username"))
    return jsonify({'message': 'Logout successful'})


@socketio.on('message')
def handle_message(data):
    sender_username = data['sender']
    recipient_username = data['recipient']
    message_content = data['message']

    emit('message', {'sender': sender_username, 'message': message_content}, room=recipient_username)
    emit('message', {'sender': sender_username, 'message': message_content}, room=sender_username)

@app.route('/welcome/chat/<username>')
@jwt_required()
def chat(username):
    current_user=get_jwt_identity()
    return render_template('chat.html',current_user=current_user, chat_partner=username)




if __name__ == '__main__':
    app.run(port=9999,debug=True)