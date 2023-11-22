from flask_sqlalchemy import SQLAlchemy
from app import app
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
db = SQLAlchemy()

## models

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable = False)
    passhash = db.Column(db.String(512), nullable = False)
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.passhash, password)
    
#transcription table
class Transcription(db.Model):
    __tablename__ = 'transcription'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    transcripted_text = db.Column(db.Text, nullable = False)
    translated_transcription = db.Column(db.Text, nullable = False)

