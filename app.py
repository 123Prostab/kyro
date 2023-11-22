from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

import config
from models import User, Transcription,db
db.init_app(app)

with app.app_context():
    db.create_all()
    # create admin if admin does not exist
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', password='admin')
        db.session.add(admin)
        db.session.commit()

import routes