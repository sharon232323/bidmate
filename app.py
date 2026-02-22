from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "bidmate_secret_key"

# DATABASE
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bidmate.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# UPLOAD FOLDER
UPLOAD_FOLDER = "static/uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# =========================
# MODELS
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(100))
    year = db.Column(db.String(20))
    department = db.Column(db.String(100))
    id_card = db.Column(db.String(200))
    approved = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default="buyer")
    is_admin = db.Column(db.Boolean, default=False)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    price = db.Column(db.Float)
    image = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =========================
# ADMIN EMAIL (YOU)
# =========================
ADMIN_EMAIL = "thanusreecse2023@gmail.com"


# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    items = Item.query.order_by(Item.created_at.desc()).all()
    return render_template("home.html", items=items)


# =========================
# SIGNUP
# =========================

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        year = request.form["year"]
        department = request.form["department"]

        id_card_file = request.files["id_card"]
        filename = secure_filename(id_card_file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        id_card_file.save(filepath)

        is_admin = False
        approved = False

        if email == ADMIN_EMAIL:
            is_admin = True
            approved = True

        user = User(
            name=name,
            email=email,
            password=password,
            year=year,
            department=department,
            id_card=filename,
            approved=approved,
            is_admin=is_admin
        )

        db.session.add(user)
        db.session.commit()

        flash("Signup successful! Wait for admin approval.")
        return redirect("/login")

    return render_template("signup.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email, password=password).first()

        if user:
            if not user.approved:
                flash("Wait for admin approval.")
                return redirect("/login")

            session["user_id"] = user.id
            session["is_admin"] = user.is_admin
            return redirect("/")

        flash("Invalid credentials")
        return redirect("/login")

    return render_template("login.html")


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# =========================
# PROFILE PAGE
# =========================

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])
    return render_template("profile.html", user=user)


# =========================
# SELL ITEM
# =========================

@app.route("/sell", methods=["GET", "POST"])
def sell():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        category = request.form["category"]
        price = request.form["price"]

        image_file = request.files["image"]
        filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        item = Item(
            title=title,
            description=description,
            category=category,
            price=price,
            image=filename,
            user_id=session["user_id"]
        )

        db.session.add(item)
        db.session.commit()

        flash("Item listed successfully!")
        return redirect("/")

    return render_template("sell.html")


# =========================
# DELETE ITEM
# =========================

@app.route("/delete/<int:item_id>")
def delete(item_id):
    if "user_id" not in session:
        return redirect("/login")

    item = Item.query.get(item_id)

    if item.user_id == session["user_id"] or session.get("is_admin"):
        db.session.delete(item)
        db.session.commit()

    return redirect("/")


# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/admin")
def admin():
    if not session.get("is_admin"):
        return redirect("/")

    pending_users = User.query.filter_by(approved=False).all()
    all_users = User.query.all()
    all_items = Item.query.all()

    return render_template(
        "admin.html",
        pending_users=pending_users,
        all_users=all_users,
        all_items=all_items
    )


# =========================
# APPROVE USER
# =========================

@app.route("/approve/<int:user_id>")
def approve(user_id):
    if not session.get("is_admin"):
        return redirect("/")

    user = User.query.get(user_id)
    user.approved = True
    db.session.commit()

    return redirect("/admin")


# =========================
# REJECT USER
# =========================

@app.route("/reject/<int:user_id>")
def reject(user_id):
    if not session.get("is_admin"):
        return redirect("/")

    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()

    return redirect("/admin")


# =========================
# RUN
# =========================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)