from dotenv import load_dotenv
from app import app
from os import getenv

# config
load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
app.config['SECRET_KEY'] = getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = 'static'

