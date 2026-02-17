from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from collections import Counter
import json
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Render 必须这样写数据库
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mood.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =========================
# Models
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

class Mood(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emotion = db.Column(db.String(100))
    intensity = db.Column(db.Integer)
    note = db.Column(db.String(300))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer)

# =========================
# Emotion Colors
# =========================

emotion_colors = {
    "Happy": "#FFF9D6",
    "Sad": "#EEF2F7",
    "Lonely": "#EEF2F7",
    "Overwhelmed": "#F3E8FF",
    "Anxious": "#E6FAF7",
    "Disappointed": "#EEF2F7",
    "Stressed": "#F3E8FF",
    "Tired": "#F4F4F4"
}

# =========================
# Home
# =========================

@app.route("/")
def home():
    return redirect("/login")

# =========================
# Register
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            return "Username already exists"

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect("/login")

    return render_template("register.html")

# =========================
# Login
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session["user_id"] = user.id
            return redirect("/dashboard")
        else:
            return "Invalid credentials"

    return render_template("login.html")

# =========================
# Dashboard
# =========================

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        emotion = request.form["emotion"]
        intensity = int(request.form["intensity"])
        note = request.form["note"]

        new_mood = Mood(
            emotion=emotion,
            intensity=intensity,
            note=note,
            user_id=session["user_id"]
        )

        db.session.add(new_mood)
        db.session.commit()
        return redirect("/dashboard")

    moods = Mood.query.filter_by(user_id=session["user_id"]).order_by(Mood.date.desc()).all()

    emotion_counter = Counter([m.emotion for m in moods])
    emotion_labels = list(emotion_counter.keys())
    emotion_counts = list(emotion_counter.values())

    dates = [m.date.strftime("%m-%d") for m in reversed(moods)]
    intensities = [m.intensity for m in reversed(moods)]

    most_common = None
    background_color = "#F4F4F4"
    low_streak_warning = None

    if moods:
        most_common = max(emotion_counter, key=emotion_counter.get)
        background_color = emotion_colors.get(moods[0].emotion, "#F4F4F4")

        negative = ["Sad", "Lonely", "Overwhelmed", "Anxious", "Disappointed", "Stressed", "Tired"]
        streak = 0

        for m in moods:
            if m.emotion in negative:
                streak += 1
            else:
                break

        if streak >= 3:
            low_streak_warning = "You've recorded negative emotions 3 times in a row. Consider resting or talking to someone you trust."

    return render_template(
    "dashboard.html",
    moods=moods,
    most_common=most_common,
    background_color=background_color,
    low_streak_warning=low_streak_warning,
    emotion_labels=emotion_labels,
    emotion_counts=emotion_counts,
    dates=dates,
    intensities=intensities

    )

# =========================
# Feedback
# =========================

@app.route("/feedback", methods=["POST"])
def feedback():
    if "user_id" not in session:
        return redirect("/login")

    content = request.form["feedback"]

    new_feedback = Feedback(
        content=content,
        user_id=session["user_id"]
    )

    db.session.add(new_feedback)
    db.session.commit()

    return redirect("/dashboard")

# =========================
# Admin
# =========================

@app.route("/admin")
def admin():
    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    if user.username != "admin":
        return "Access Denied"

    moods = db.session.query(Mood, User)\
        .join(User, Mood.user_id == User.id)\
        .order_by(Mood.date.desc()).all()

    feedbacks = db.session.query(Feedback, User)\
        .join(User, Feedback.user_id == User.id)\
        .order_by(Feedback.date.desc()).all()

    return render_template("admin.html", moods=moods, feedbacks=feedbacks)

# =========================
# Logout
# =========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# =========================
# Run (Render Compatible)
# =========================

import os

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


