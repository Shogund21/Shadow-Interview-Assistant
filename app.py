from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import pyaudio
import wave
import numpy as np
from datetime import datetime
import whisper
import pyttsx3
import threading
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///questions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your-secret-key-here'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(100), nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                return jsonify({'message': 'Access forbidden: insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class AudioRecorder:
    def __init__(self):
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.recording = False
        self.frames = []
        self.model = whisper.load_model("base")  # Change model size if needed
        self.engine = pyttsx3.init()

    def start_recording(self):
        self.recording = True
        threading.Thread(target=self._record).start()

    def stop_recording(self):
        self.recording = False

    def _record(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=self.format,
                        channels=self.channels,
                        rate=self.rate,
                        input=True,
                        frames_per_buffer=self.chunk)

        while self.recording:
            data = stream.read(self.chunk)
            self.frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

    def save_recording(self):
        if not self.frames:
            return None

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"recording_{timestamp}.wav"
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        self.frames = []
        return filename

    def transcribe_audio(self, audio_file):
        result = self.model.transcribe(audio_file)
        return result['text']

    def speak_response(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

recorder = AudioRecorder()

@app.route('/')
def hello():
    return jsonify({'message': 'Welcome to the AI-powered interview assistant!'})

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 400
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid username or password'}), 401
    login_user(user)
    return jsonify({'message': 'Logged in successfully'})

@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/add_question', methods=['POST'])
@login_required
@role_required('admin')
def add_question():
    data = request.json
    question_text = data.get('question')
    category = data.get('category')
    new_question = Question(question=question_text, category=category)
    db.session.add(new_question)
    db.session.commit()
    return jsonify({'message': 'Question added successfully'})

@app.route('/get_questions', methods=['GET'])
@login_required
def get_questions():
    questions = Question.query.all()
    results = [
        {
            "id": question.id,
            "question": question.question,
            "category": question.category
        } for question in questions]
    return jsonify(results)

@app.route('/update_profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.json
    user = db.session.get(User, current_user.id)
    user.username = data.get('username', user.username)
    if 'password' in data:
        user.password = generate_password_hash(data['password'])
    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'})

@app.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    user.password = generate_password_hash(data['new_password'])
    db.session.commit()
    return jsonify({'message': 'Password reset successfully'})

@app.route('/promote_user', methods=['POST'])
@login_required
@role_required('admin')
def promote_user():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    user.role = 'admin'
    db.session.commit()
    return jsonify({'message': 'User promoted to admin successfully'})

@app.route('/start_recording', methods=['POST'])
@login_required
def start_recording():
    recorder.start_recording()
    return jsonify({'message': 'Recording started'})

@app.route('/stop_recording', methods=['POST'])
@login_required
def stop_recording():
    recorder.stop_recording()
    filename = recorder.save_recording()
    if filename:
        transcription = recorder.transcribe_audio(filename)
        return jsonify({
            'message': 'Recording saved and transcribed',
            'filename': filename,
            'transcription': transcription
        })
    else:
        return jsonify({'message': 'No audio recorded'}), 400

if __name__ == '__main__':
    app.run(debug=True)
