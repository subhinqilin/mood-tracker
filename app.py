from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mood.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"],
            password=request.form["password"]
        ).first()
        if user:
            session["user_id"] = user.id
            return redirect("/dashboard")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = User(
            username=request.form["username"],
            password=request.form["password"]
        )
        db.session.add(user)
        db.session.commit()
        return redirect("/login")
    return render_template("register.html")

# 情绪 → 浅色背景映射
emotion_colors = {
    "Happy": "#FFF9D6",
    "Excited": "#FFF9D6",
    "Calm": "#E6F2FF",
    "Relaxed": "#E6F2FF",
    "Grateful": "#FFEFD8",
    "Motivated": "#FFEFD8",
    "Proud": "#FFE6F0",
    "Loved": "#FFE6F0",
    "Sad": "#EEF2F7",
    "Lonely": "#EEF2F7",
    "Angry": "#FFE5E5",
    "Stressed": "#F3E8FF",
    "Overwhelmed": "#F3E8FF",
    "Anxious": "#E6FAF7",
    "Tired": "#F4F4F4",
    "Bored": "#F4F4F4",
    "Confused": "#F4F4F4",
    "Okay": "#F4F4F4",
    "Frustrated": "#FFE5E5",
    "Disappointed": "#EEF2F7"
}

@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    return redirect("/login")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        new_mood = Mood(
            emotion=request.form["emotion"],
            intensity=int(request.form["intensity"]),
            note=request.form["note"],
            user_id=session["user_id"]
        )
        db.session.add(new_mood)
        db.session.commit()

    moods = Mood.query.filter_by(user_id=session["user_id"]).order_by(Mood.date.desc()).all()

    most_common = None
    advice = "Keep tracking your emotions."
    background_color = "#f2f4f8"
    low_streak_warning = None

    if moods:
        # 最常见情绪
        emotion_count = {}
        for m in moods:
            emotion_count[m.emotion] = emotion_count.get(m.emotion, 0) + 1
        most_common = max(emotion_count, key=emotion_count.get)

        # 背景颜色
        background_color = emotion_colors.get(moods[0].emotion, "#f2f4f8")

        # 连续低落检测
        negative_emotions = ["Sad", "Lonely", "Overwhelmed", "Anxious", "Disappointed"]
        streak = 0
        for m in moods:
            if m.emotion in negative_emotions:
                streak += 1
            else:
                break

        if streak >= 3:
            low_streak_warning = "You've recorded negative emotions 3 times in a row. Consider resting, going outside, or talking to someone you trust."

    return render_template(
        "dashboard.html",
        moods=moods,
        most_common=most_common,
        advice=advice,
        background_color=background_color,
        low_streak_warning=low_streak_warning
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)

