from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session

from models import db, User,Transcription
import datetime
import re
from app import app
import os
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
from openai import OpenAI
import itertools
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer
client = OpenAI(api_key="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")
#decorator auth_required
def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login',methods = ['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username = username).first()
        print(password)
        if not user:
            flash('User does not exist.')
            return redirect(url_for('login'))
        if not user.check_password(password):
            flash('Incorrect password.')
            return redirect(url_for('login'))
        # login successful
        session['user_id'] = user.id
        #query user table
        user = User.query.get(session['user_id'])
        return redirect('/dashboard')
    return render_template('login.html')

@app.route('/dashboard')
@auth_required
def dashboard():
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html',user = user)

#register
@app.route('/register',methods = ['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username = username).first()
        if user:
            flash('Username already exists')
            return redirect(url_for('register'))
        else:
            new_user = User(username = username, password = password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registered successfully')
            return redirect(url_for('login'))
    return render_template('register.html')

# def translation(text):
#     # Detect language and translate to English
#     result = Translator.detect_language(text)
#     if result.lang != 'en':
#         translation_result = Translator.translate(text, src=result.lang, dest='en').text
#         return translation_result
#     else:
#         return text


@auth_required
@app.route("/input",methods = ['GET','POST'])
def input():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = file.filename
            fpath = os.path.join(app.config['UPLOAD_FOLDER'],file.filename)
            file.save(fpath)
            audio_file= open(fpath, "rb")
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file, response_format="text")
            translated_transcript = client.audio.translations.create(model="whisper-1", file=audio_file,response_format='text')

            try:
                user_id = session['user_id']
                db.session.add(Transcription(user_id=user_id, transcripted_text=transcript,
                                     translated_transcription=translated_transcript))
                db.session.commit()
                flash('Transcription saved and saved to static')
                return redirect('/dashboard')
            except:
                flash('Transcription error.')
    return render_template("input.html",user = user)

#logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

#calculate most frequently used words
@auth_required
@app.route("/words",methods = ['GET','POST'])
def words():
    user = User.query.get(session['user_id'])
    #query the transcription table based on user id and get translated_transcription
    transcriptions = Transcription.query.filter_by(user_id = user.id).all()
    #create a dictionary to store the words and their frequency
    word_freq = {}
    for transcription in transcriptions:
        words = transcription.translated_transcription.split()
        for word in words:
            if word in word_freq:
                word_freq[word] += 1
            else:
                word_freq[word] = 1
        #sort the dictionary by value in descending order
    sorted_word_freq = dict(sorted(word_freq.items(), key=lambda item: item[1], reverse=True))
    #select the top three
    sorted_word_freq = dict(itertools.islice(sorted_word_freq.items(), 3))
    # query the transcription table
    transcriptions_all = Transcription.query.all()
    #create a dictionary to store the words and their frequency
    word_freq_all = {}
    for transcription in transcriptions_all:
        words = transcription.translated_transcription.split()
        for word in words:
            if word in word_freq_all:
                word_freq_all[word] += 1
            else:
                word_freq_all[word] = 1
        #sort the dictionary by value in descending order
    sorted_word_freq_all = dict(sorted(word_freq_all.items(), key=lambda item: item[1], reverse=True))
    #select the top three
    sorted_word_freq_all = dict(itertools.islice(sorted_word_freq_all.items(), 3))
    return render_template("words.html",user = user, sorted_word_freq = sorted_word_freq,sorted_word_freq_all = sorted_word_freq_all)


@app.route('/identify_unique_phrases', methods=['GET'])
@auth_required
def identify_unique_phrases():
    user_id = session['user_id']
    user = User.query.get(user_id)
    user_transcriptions = Transcription.query.filter_by(user_id=user_id).all()

    all_transcriptions = [transcription.translated_transcription.lower() for transcription in user_transcriptions]

    # Tokenize and count phrases
    vectorizer = CountVectorizer(ngram_range=(3, 3))
    X = vectorizer.fit_transform(all_transcriptions)
    phrases = vectorizer.get_feature_names_out()

    # Get top 3 unique phrases
    top_unique_phrases = sorted(zip(phrases, X.sum(axis=0).tolist()[0]), key=lambda x: x[1], reverse=True)[:3]

    return render_template('phrase.html',user = user,top_unique_phrases = top_unique_phrases)



