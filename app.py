from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from collections import Counter
import json

app = Flask(__name__)

app.secret_key = "secretkey"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mood.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ======================
# Models
# ======================

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


# ======================
# Emotion Colors
# ======================

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

# ======================
# Home
# ======================

@app.route("/")
def home():
    return redirect("/login")



# ======================
# Dashboard
# ======================

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    # 提交心情
    if request.method == "POST":

        if "emotion" in request.form:
            mood = Mood(
                emotion=request.form["emotion"],
                intensity=int(request.form["intensity"]),
                note=request.form["note"],
                user_id=session["user_id"]
            )
            db.session.add(mood)
            db.session.commit()

        if "feedback" in request.form:
            fb = Feedback(
                content=request.form["feedback"],
                user_id=session["user_id"]
            )
            db.session.add(fb)
            db.session.commit()

    moods = Mood.query.filter_by(
        user_id=session["user_id"]
    ).order_by(Mood.date.desc()).all()

    # 默认值
    most_common = None
    background_color = "#f2f4f8"
    low_streak_warning = None
    emotion_labels = []
    emotion_counts = []
    dates = []
    intensities = []

    if moods:

        # 统计
        counter = Counter([m.emotion for m in moods])
        most_common = counter.most_common(1)[0][0]

        emotion_labels = list(counter.keys())
        emotion_counts = list(counter.values())

        dates = [m.date.strftime("%m-%d") for m in reversed(moods)]
        intensities = [m.intensity for m in reversed(moods)]

        # 背景
        background_color = emotion_colors.get(
            moods[0].emotion, "#f2f4f8"
        )

        # 连续低落
        negative = [
            "Sad", "Lonely", "Overwhelmed",
            "Anxious", "Disappointed",
            "Stressed", "Tired"
        ]

        streak = 0
        for m in moods:
            if m.emotion in negative:
                streak += 1
            else:
                break

        if streak >= 3:
            low_streak_warning = (
                "You've recorded negative emotions "
                "3 times in a row. Consider resting "
                "or talking to someone you trust."
            )

    return render_template(
        "dashboard.html",
        moods=moods,
        most_common=most_common,
        background_color=background_color,
        low_streak_warning=low_streak_warning,
        emotion_labels=json.dumps(emotion_labels),
        emotion_counts=json.dumps(emotion_counts),
        dates=json.dumps(dates),
        intensities=json.dumps(intensities)
    )


# ======================
# Admin
# ======================

@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    if user.username != "subhinqilin":
        return "Access Denied"

    moods = db.session.query(Mood, User).join(
        User, Mood.user_id == User.id
    ).order_by(Mood.date.desc()).all()

    feedbacks = db.session.query(Feedback, User).join(
        User, Feedback.user_id == User.id
    ).order_by(Feedback.date.desc()).all()

    return render_template(
        "admin.html",
        moods=moods,
        feedbacks=feedbacks
    )


# ======================
# Logout
# ======================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ======================
# Run
# ======================

