import os
from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "bidmate_secret_key"

# Database Config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bidmate.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "static/uploads"

db = SQLAlchemy(app)

# FIXED ADMIN EMAIL
ADMIN_EMAIL = "thanusreecse2023@gmail.com"

# -----------------------------
# DATABASE MODEL
# -----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20), default="buyer")
    is_admin = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    id_card = db.Column(db.String(200))


# -----------------------------
# HOME
# -----------------------------
@app.route("/")
def home():
    return render_template("home.html")


# -----------------------------
# SIGNUP
# -----------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        id_card_file = request.files["id_card"]

        filename = secure_filename(id_card_file.filename)
        id_card_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        is_admin = True if email == ADMIN_EMAIL else False
        is_approved = True if email == ADMIN_EMAIL else False

        new_user = User(
            name=name,
            email=email,
            password=password,
            id_card=filename,
            is_admin=is_admin,
            is_approved=is_approved
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Signup successful! Wait for admin approval.")
        return redirect("/login")

    return render_template("signup.html")


# -----------------------------
# LOGIN
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email, password=password).first()

        if user:
            if not user.is_approved:
                flash("Waiting for Admin Approval.")
                return redirect("/login")

            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_role"] = user.role
            session["is_admin"] = user.is_admin

            if user.is_admin:
                return redirect("/admin")

            return redirect("/profile")
        else:
            flash("Invalid credentials")

    return render_template("login.html")


# -----------------------------
# PROFILE
# -----------------------------
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])
    return render_template("profile.html", user=user)


# -----------------------------
# ROLE SWITCH
# -----------------------------
@app.route("/switch_role")
def switch_role():
    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    if user.role == "buyer":
        user.role = "seller"
    else:
        user.role = "buyer"

    db.session.commit()
    session["user_role"] = user.role

    return redirect("/profile")


# -----------------------------
# ADMIN DASHBOARD
# -----------------------------
@app.route("/admin")
def admin():
    if "is_admin" not in session or not session["is_admin"]:
        return redirect("/")

    users = User.query.filter_by(is_approved=False).all()
    return render_template("admin.html", users=users)


# -----------------------------
# APPROVE USER
# -----------------------------
@app.route("/approve/<int:user_id>")
def approve(user_id):
    if "is_admin" not in session or not session["is_admin"]:
        return redirect("/")

    user = User.query.get(user_id)
    user.is_approved = True
    db.session.commit()

    return redirect("/admin")


# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)