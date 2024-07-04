import unittest
import json
from app import app, db, User, Question
from flask_login import current_user
from unittest.mock import patch
import os
import logging

# Suppress comtypes debug messages
logging.getLogger('comtypes').setLevel(logging.ERROR)

class APITestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_hello(self):
        response = self.client.get('/')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Welcome to the AI-powered interview assistant!')

    def test_register(self):
        response = self.client.post('/register', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'User registered successfully')

    def test_register_existing_username(self):
        # Register a user
        self.client.post('/register', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        # Try to register the same username again
        response = self.client.post('/register', json={
            'username': 'testuser',
            'password': 'anotherpass'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['message'], 'Username already exists')

    def test_login(self):
        # First register a user
        self.client.post('/register', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        # Then try to log in
        response = self.client.post('/login', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Logged in successfully')

    def test_login_failure(self):
        response = self.client.post('/login', json={
            'username': 'nonexistent',
            'password': 'wrongpass'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(data['message'], 'Invalid username or password')

    def test_logout(self):
        # First register and log in a user
        self.client.post('/register', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        self.client.post('/login', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        # Then logout
        response = self.client.get('/logout')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Logged out successfully')

    def test_add_question(self):
        # First register and log in as an admin user
        self.client.post('/register', json={
            'username': 'admin',
            'password': 'adminpass',
            'role': 'admin'
        })
        self.client.post('/login', json={
            'username': 'admin',
            'password': 'adminpass'
        })
        # Then try to add a question
        response = self.client.post('/add_question', json={
            'question': 'What is your greatest strength?',
            'category': 'General'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Question added successfully')

    def test_add_question_without_admin(self):
        # Register and log in as a regular user
        self.client.post('/register', json={
            'username': 'regularuser',
            'password': 'regularpass'
        })
        self.client.post('/login', json={
            'username': 'regularuser',
            'password': 'regularpass'
        })
        # Try to add a question
        response = self.client.post('/add_question', json={
            'question': 'What is your greatest weakness?',
            'category': 'General'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(data['message'], 'Access forbidden: insufficient permissions')

    def test_get_questions(self):
        # Add a question first
        self.test_add_question()
        # Then try to get questions
        response = self.client.get('/get_questions')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['question'], 'What is your greatest strength?')

    def test_update_profile(self):
        # First register and log in a user
        self.client.post('/register', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        self.client.post('/login', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        # Then try to update the profile
        response = self.client.put('/update_profile', json={
            'username': 'updateduser',
            'password': 'newpass'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Profile updated successfully')

    def test_reset_password(self):
        # First register a user
        self.client.post('/register', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        # Then reset the password
        response = self.client.post('/reset_password', json={
            'username': 'testuser',
            'new_password': 'newtestpass'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Password reset successfully')
        # Try to log in with the new password
        login_response = self.client.post('/login', json={
            'username': 'testuser',
            'password': 'newtestpass'
        })
        login_data = json.loads(login_response.data)
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_data['message'], 'Logged in successfully')

    def test_reset_password_nonexistent_user(self):
        response = self.client.post('/reset_password', json={
            'username': 'nonexistent',
            'new_password': 'newpass'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['message'], 'User not found')

    def test_promote_user(self):
        with app.app_context():
            # First register and log in as an admin user
            self.client.post('/register', json={
                'username': 'admin',
                'password': 'adminpass',
                'role': 'admin'
            })
            self.client.post('/login', json={
                'username': 'admin',
                'password': 'adminpass'
            })
            # Then promote a user
            self.client.post('/register', json={
                'username': 'testuser',
                'password': 'testpass'
            })
            response = self.client.post('/promote_user', json={
                'username': 'testuser'
            })
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['message'], 'User promoted to admin successfully')

    def test_promote_nonexistent_user(self):
        # First register and log in as an admin user
        self.client.post('/register', json={
            'username': 'admin',
            'password': 'adminpass',
            'role': 'admin'
        })
        self.client.post('/login', json={
            'username': 'admin',
            'password': 'adminpass'
        })
        # Try to promote a non-existent user
        response = self.client.post('/promote_user', json={
            'username': 'nonexistent'
        })
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['message'], 'User not found')

    @patch('app.recorder.start_recording')
    def test_start_recording(self, mock_start_recording):
        self.test_login()  # Ensure we're logged in
        response = self.client.post('/start_recording')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Recording started')
        mock_start_recording.assert_called_once()

    @patch('app.recorder.stop_recording')
    @patch('app.recorder.save_recording')
    @patch('app.recorder.transcribe_audio')
    def test_stop_recording_with_transcription(self, mock_transcribe, mock_save, mock_stop):
        self.test_login()  # Ensure we're logged in
        mock_save.return_value = 'test_recording.wav'
        mock_transcribe.return_value = 'This is a test transcription.'

        response = self.client.post('/stop_recording')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Recording saved and transcribed')
        self.assertEqual(data['filename'], 'test_recording.wav')
        self.assertEqual(data['transcription'], 'This is a test transcription.')

        mock_stop.assert_called_once()
        mock_save.assert_called_once()
        mock_transcribe.assert_called_once_with('test_recording.wav')

if __name__ == '__main__':
    unittest.main()

