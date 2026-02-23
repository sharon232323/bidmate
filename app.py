import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from extensions import db, login_manager
from models import User, Item, Bid

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager.init_app(app)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        year = request.form["year"]
        department = request.form["department"]
        id_card_file = request.files["id_card"]

        filename = secure_filename(id_card_file.filename)
        id_card_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        user = User(
            name=name,
            email=email,
            password=password,
            year=year,
            department=department,
            id_card=filename
        )

        # YOU = SUPER ADMIN
        if email == app.config["SUPER_ADMIN_EMAIL"]:
            user.is_admin = True
            user.is_approved = True

        db.session.add(user)
        db.session.commit()

        flash("Signup successful. Await admin approval.")
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if not user.is_approved:
                flash("Account awaiting admin approval.")
                return redirect(url_for("login"))

            login_user(user)
            return redirect(url_for("home"))

        flash("Invalid credentials")

    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if not user.is_approved:
                flash("Account awaiting admin approval.")
                return redirect(url_for("login"))

            login_user(user)
            return redirect(url_for("home"))

        flash("Invalid credentials")

    return render_template("login.html")

@app.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for("home"))

    pending_users = User.query.filter_by(is_approved=False).all()
    items = Item.query.all()

    return render_template("admin_dashboard.html",
                           pending_users=pending_users,
                           items=items)

@app.route("/approve/<int:user_id>")
@login_required
def approve_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for("home"))

    user = User.query.get(user_id)
    user.is_approved = True
    db.session.commit()

    return redirect(url_for("admin_dashboard"))

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")

@app.route("/switch_role")
@login_required
def switch_role():
    if current_user.role == "buyer":
        current_user.role = "seller"
    else:
        current_user.role = "buyer"

    db.session.commit()
    return redirect(url_for("profile"))

@app.route("/")
def home():
    items = Item.query.order_by(Item.created_at.desc()).all()
    return render_template("home.html", items=items)

@app.route("/delete_item/<int:item_id>")
@login_required
def delete_item(item_id):
    item = Item.query.get(item_id)

    if item.seller_id == current_user.id or current_user.is_admin:
        db.session.delete(item)
        db.session.commit()

    return redirect(url_for("sell"))

@app.route("/categories")
def categories():
    items = Item.query.all()
    return render_template("categories.html", items=items)