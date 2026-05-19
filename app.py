from flask import Flask, render_template, redirect, url_for, request, flash
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

# =========================
# APP CONFIGURATION
# =========================

app = Flask(__name__)

app.config['SECRET_KEY'] = 'bidmate_secret_key'

# SQLite Database (works locally + Render)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'database.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# =========================
# DATABASE
# =========================

db = SQLAlchemy(app)

# =========================
# LOGIN MANAGER
# =========================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = 'login'

# =========================
# USER MODEL
# =========================

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
        'Item',
        backref='seller',
        lazy=True
    )

# =========================
# ITEM MODEL
# =========================

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
        db.Float,
        nullable=False
    )

    category = db.Column(
        db.String(100),
        nullable=False
    )

    image = db.Column(
        db.String(300),
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
        db.ForeignKey('user.id'),
        nullable=False
    )

# =========================
# CREATE DATABASE
# =========================

with app.app_context():
    db.create_all()

# =========================
# LOGIN LOADER
# =========================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =========================
# HOME PAGE
# =========================

@app.route('/')
def home():

    items = Item.query.order_by(
        Item.created_at.desc()
    ).all()

    return render_template(
        'home.html',
        items=items
    )

# =========================
# REGISTER
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form.get('username')

        email = request.form.get('email')

        password = request.form.get('password')

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash('Email already exists!', 'danger')

            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)

        db.session.commit()

        flash('Registration successful!', 'success')

        return redirect(url_for('login'))

    return render_template('register.html')

# =========================
# LOGIN
# =========================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email')

        password = request.form.get('password')

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            flash('Login successful!', 'success')

            return redirect(url_for('home'))

        else:

            flash('Invalid email or password!', 'danger')

    return render_template('login.html')

# =========================
# LOGOUT
# =========================

@app.route('/logout')
@login_required
def logout():

    logout_user()

    flash('Logged out successfully!', 'info')

    return redirect(url_for('home'))

# =========================
# SELL ITEM
# =========================

@app.route('/sell', methods=['GET', 'POST'])
@login_required
def sell():

    if request.method == 'POST':

        title = request.form.get('title')

        description = request.form.get('description')

        price = request.form.get('price')

        category = request.form.get('category')

        image = request.form.get('image')

        barter = request.form.get('is_barter')

        new_item = Item(
            title=title,
            description=description,
            price=float(price),
            category=category,
            image=image,
            is_barter=True if barter else False,
            seller_id=current_user.id
        )

        db.session.add(new_item)

        db.session.commit()

        flash('Item listed successfully!', 'success')

        return redirect(url_for('home'))

    return render_template('sell.html')

# =========================
# ITEM DETAILS
# =========================

@app.route('/item/<int:item_id>')
def item_detail(item_id):

    item = Item.query.get_or_404(item_id)

    return render_template(
        'item_detail.html',
        item=item
    )

# =========================
# CATEGORIES PAGE
# =========================

@app.route('/categories')
def categories():

    categories = [
        'Books',
        'Electronics',
        'Notes',
        'Fashion',
        'Hostel Items',
        'Accessories',
        'Gaming',
        'Others'
    ]

    return render_template(
        'categories.html',
        categories=categories
    )

# =========================
# CATEGORY ITEMS
# =========================

@app.route('/category/<string:category_name>')
def category_items(category_name):

    items = Item.query.filter_by(
        category=category_name
    ).all()

    return render_template(
        'category_items.html',
        items=items,
        category_name=category_name
    )

# =========================
# PROFILE PAGE
# =========================

@app.route('/profile')
@login_required
def profile():

    user_items = Item.query.filter_by(
        seller_id=current_user.id
    ).all()

    return render_template(
        'profile.html',
        user_items=user_items
    )

# =========================
# DELETE ITEM
# =========================

@app.route('/delete-item/<int:item_id>')
@login_required
def delete_item(item_id):

    item = Item.query.get_or_404(item_id)

    if item.seller_id != current_user.id:

        flash('Unauthorized action!', 'danger')

        return redirect(url_for('home'))

    db.session.delete(item)

    db.session.commit()

    flash('Item deleted successfully!', 'success')

    return redirect(url_for('profile'))

# =========================
# SEARCH
# =========================

@app.route('/search')
def search():

    query = request.args.get('q')

    if query:

        items = Item.query.filter(
            Item.title.contains(query)
        ).all()

    else:

        items = []

    return render_template(
        'search_results.html',
        items=items,
        query=query
    )

# =========================
# RUN APP
# =========================

if __name__ == '__main__':

    app.run(debug=True)