from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# ---------------------------------------------------
# APP CONFIG
# ---------------------------------------------------

app = Flask(__name__)

app.config["SECRET_KEY"] = "bidmate_secret_key"

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///database.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------------------------------------------
# LOGIN MANAGER
# ---------------------------------------------------

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"

# ---------------------------------------------------
# MODELS
# ---------------------------------------------------

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )

    items = db.relationship(
        "Item",
        backref="seller",
        lazy=True
    )


class Item(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    price = db.Column(
        db.Integer,
        nullable=False
    )

    category = db.Column(
        db.String(100),
        nullable=False
    )

    image = db.Column(
        db.String(500),
        nullable=True
    )

    is_barter = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    seller_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

# ---------------------------------------------------
# CREATE DATABASE
# ---------------------------------------------------

with app.app_context():
    db.create_all()

# ---------------------------------------------------
# LOGIN LOADER
# ---------------------------------------------------

@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))

# ---------------------------------------------------
# HOME
# ---------------------------------------------------

@app.route("/")
def home():

    items = Item.query.order_by(
        Item.created_at.desc()
    ).all()

    return render_template(
        "home.html",
        items=items
    )

# ---------------------------------------------------
# REGISTER
# ---------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]

        email = request.form["email"]

        password = generate_password_hash(
            request.form["password"]
        )

        existing_user = User.query.filter(
            (User.username == username) |
            (User.email == email)
        ).first()

        if existing_user:

            flash("User already exists")
            return redirect(url_for("register"))

        new_user = User(
            username=username,
            email=email,
            password=password
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful")

        return redirect(url_for("login"))

    return render_template("register.html")

# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            flash("Login successful")

            return redirect(url_for("home"))

        else:

            flash("Invalid credentials")

    return render_template("login.html")

# ---------------------------------------------------
# LOGOUT
# ---------------------------------------------------

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully")

    return redirect(url_for("home"))

# ---------------------------------------------------
# SELL ITEM
# ---------------------------------------------------

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():

    if request.method == "POST":

        title = request.form["title"]

        description = request.form["description"]

        price = request.form["price"]

        category = request.form["category"]

        image = request.form["image"]

        is_barter = True if request.form.get(
            "is_barter"
        ) else False

        item = Item(
            title=title,
            description=description,
            price=price,
            category=category,
            image=image,
            is_barter=is_barter,
            seller_id=current_user.id
        )

        db.session.add(item)

        db.session.commit()

        flash("Item listed successfully")

        return redirect(url_for("home"))

    return render_template("sell.html")

# ---------------------------------------------------
# ITEM DETAIL
# ---------------------------------------------------

@app.route("/item/<int:item_id>")
def item_detail(item_id):

    item = Item.query.get_or_404(item_id)

    return render_template(
        "item_detail.html",
        item=item
    )

# ---------------------------------------------------
# PROFILE
# ---------------------------------------------------

@app.route("/profile")
@login_required
def profile():

    items = Item.query.filter_by(
        seller_id=current_user.id
    ).all()

    return render_template(
        "profile.html",
        items=items
    )

# ---------------------------------------------------
# SEARCH
# ---------------------------------------------------

@app.route("/search")
def search():

    query = request.args.get("q")

    if query:

        items = Item.query.filter(
            Item.title.ilike(f"%{query}%")
        ).all()

    else:

        items = []

    return render_template(
        "search.html",
        items=items,
        query=query
    )

# ---------------------------------------------------
# CATEGORY PAGE
# ---------------------------------------------------

@app.route("/category/<category_name>")
def category_items(category_name):

    items = Item.query.filter_by(
        category=category_name
    ).all()

    return render_template(
        "category_items.html",
        items=items,
        category_name=category_name
    )

# ---------------------------------------------------
# EDIT ITEM
# ---------------------------------------------------

@app.route(
    "/edit/<int:item_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_item(item_id):

    item = Item.query.get_or_404(item_id)

    if item.seller_id != current_user.id:

        flash("Unauthorized access")

        return redirect(url_for("home"))

    if request.method == "POST":

        item.title = request.form["title"]

        item.description = request.form["description"]

        item.price = request.form["price"]

        item.category = request.form["category"]

        item.image = request.form["image"]

        item.is_barter = True if request.form.get(
            "is_barter"
        ) else False

        db.session.commit()

        flash("Item updated successfully")

        return redirect(url_for("profile"))

    return render_template(
        "edit_item.html",
        item=item
    )

# ---------------------------------------------------
# DELETE ITEM
# ---------------------------------------------------

@app.route("/delete/<int:item_id>")
@login_required
def delete_item(item_id):

    item = Item.query.get_or_404(item_id)

    if item.seller_id != current_user.id:

        flash("Unauthorized access")

        return redirect(url_for("home"))

    db.session.delete(item)

    db.session.commit()

    flash("Item deleted successfully")

    return redirect(url_for("profile"))

# ---------------------------------------------------
# CONTACT
# ---------------------------------------------------

@app.route("/contact")
def contact():

    return render_template("contact.html")

# ---------------------------------------------------
# ABOUT
# ---------------------------------------------------

@app.route("/about")
def about():

    return render_template("about.html")

# ---------------------------------------------------
# RUN APP
# ---------------------------------------------------

if __name__ == "__main__":

    app.run(debug=True)