from flask import Flask, render_template, redirect, url_for
from flask import request, flash

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from extensions import db, login_manager
from models import User, Item

import os


# =========================
# APP CONFIG
# =========================

app = Flask(__name__)

app.config['SECRET_KEY'] = 'bidmate_super_secret'

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'database.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# =========================
# INITIALIZE EXTENSIONS
# =========================

db.init_app(app)

login_manager.init_app(app)


# =========================
# LOGIN LOADER
# =========================

@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))


# =========================
# CREATE DATABASE
# =========================

with app.app_context():

    db.create_all()


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

# =========================
# REGISTER PAGE
# =========================

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        username = request.form.get('username')

        email = request.form.get('email')

        password = request.form.get('password')

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                'Email already exists!',
                'danger'
            )

            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(
            password
        )

        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)

        db.session.commit()

        flash(
            'Account created successfully!',
            'success'
        )

        return redirect(url_for('login'))

    return render_template('signup.html')


# =========================
# LOGIN PAGE
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

            flash(
                'Login successful!',
                'success'
            )

            return redirect(url_for('home'))

        else:

            flash(
                'Invalid email or password!',
                'danger'
            )

    return render_template('login.html')


# =========================
# LOGOUT
# =========================

@app.route('/logout')
@login_required
def logout():

    logout_user()

    flash(
        'Logged out successfully!',
        'info'
    )

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

        flash(
            'Item listed successfully!',
            'success'
        )

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
# CATEGORIES
# =========================

@app.route('/categories')
def categories():

    categories = [
        'Books',
        'Electronics',
        'Notes',
        'Fashion',
        'Hostel Items',
        'Gaming',
        'Accessories',
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
        'home.html',
        items=items
    )

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

@app.route("/edit/<int:item_id>", methods=["GET", "POST"])
@login_required
def edit_item(item_id):

    item = Item.query.get_or_404(item_id)

    if item.seller_id != current_user.id:
        flash("Unauthorized access")
        return redirect(url_for("home"))

    if request.method == "POST":

        item.title = request.form["title"]
        item.description = request.form["description"]
        item.price = int(request.form["price"])
        item.category = request.form["category"]
        item.image = request.form["image"]

        item.is_barter = True if request.form.get("is_barter") else False

        db.session.commit()

        flash("Item updated successfully")

        return redirect(url_for("profile"))

    return render_template(
        "edit_item.html",
        item=item
    )

# =========================
# PROFILE
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

        flash(
            'Unauthorized action!',
            'danger'
        )

        return redirect(url_for('home'))

    db.session.delete(item)

    db.session.commit()

    flash(
        'Item deleted!',
        'success'
    )

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
        'home.html',
        items=items
    )

# =========================
# CONTACT PAGE
# =========================

@app.route('/contact')
def contact():

    return render_template('contact.html')

# =========================
# RUN APP
# =========================

if __name__ == '__main__':

    app.run(debug=True)