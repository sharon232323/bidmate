import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    flash,
    url_for
)

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

from models import db, User, Item

from datetime import datetime



# ====================================
# APP CONFIG
# ====================================

app = Flask(__name__)

app.config['SECRET_KEY'] = 'bidmate_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bidmate.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['UPLOAD_FOLDER'] = 'static/uploads'


# ====================================
# INIT
# ====================================

db.init_app(app)

login_manager = LoginManager()

login_manager.login_view = 'login'

login_manager.init_app(app)


# ====================================
# CREATE UPLOAD FOLDER
# ====================================

os.makedirs(
    app.config['UPLOAD_FOLDER'],
    exist_ok=True
)


# ====================================
# LOAD USER
# ====================================

@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))


# ====================================
# CREATE DATABASE
# ====================================

with app.app_context():

    db.create_all()


# ====================================
# HOME PAGE
# ====================================

@app.route('/')
def home():

    items = Item.query.order_by(
        Item.created_at.desc()
    ).all()

    return render_template(
        'index.html',
        items=items
    )


# ====================================
# REGISTER
# ====================================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']

        email = request.form['email']

        password = request.form['password']

        college = request.form['college']

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash('Email already exists')

            return redirect('/register')

        hashed_password = generate_password_hash(
            password
        )

        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            college=college
        )

        db.session.add(new_user)

        db.session.commit()

        flash('Registration successful')

        return redirect('/login')

    return render_template('register.html')


# ====================================
# LOGIN
# ====================================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']

        password = request.form['password']

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            flash('Login successful')

            return redirect('/')

        else:

            flash('Invalid email or password')

    return render_template('login.html')


# ====================================
# LOGOUT
# ====================================

@app.route('/logout')
@login_required
def logout():

    logout_user()

    flash('Logged out successfully')

    return redirect('/')


# ====================================
# SELL ITEM
# ====================================

@app.route('/sell', methods=['GET', 'POST'])
@login_required
def sell():

    if request.method == 'POST':

        title = request.form['title']

        description = request.form['description']

        category = request.form['category']

        price = request.form['price']

        auction = True if request.form.get('auction') else False

        barter = True if request.form.get('barter') else False

        image_file = request.files['image']

        image_name = secure_filename(
            image_file.filename
        )

        image_path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            image_name
        )

        image_file.save(image_path)

        item = Item(
            title=title,
            description=description,
            category=category,
            price=price,
            image=image_name,
            auction=auction,
            barter=barter,
            highest_bid=int(price),
            user_id=current_user.id
        )

        db.session.add(item)

        db.session.commit()

        flash('Item uploaded successfully')

        return redirect('/')

    return render_template('sell.html')


# ====================================
# ITEM DETAILS
# ====================================

@app.route('/item/<int:item_id>')
def item_details(item_id):

    item = Item.query.get_or_404(item_id)

    return render_template(
    'item_detail.html',
    item=item
)


# ====================================
# PLACE BID
# ====================================

@app.route('/bid/<int:item_id>', methods=['POST'])
@login_required
def place_bid(item_id):

    item = Item.query.get_or_404(item_id)

    bid_amount = int(
        request.form['bid_amount']
    )

    if bid_amount > item.highest_bid:

        item.highest_bid = bid_amount

        db.session.commit()

        flash('Bid placed successfully')

    else:

        flash(
            'Bid must be higher than current bid'
        )

    return redirect(f'/item/{item.id}')


# ====================================
# BARTER PAGE
# ====================================

@app.route('/barter')
def barter():

    items = Item.query.filter_by(
        barter=True
    ).all()

    return render_template(
        'barter.html',
        items=items
    )


# ====================================
# CATEGORIES PAGE
# ====================================

@app.route('/categories')
def categories():

    items = Item.query.all()

    return render_template(
        'categories.html',
        items=items
    )


# ====================================
# SEARCH
# ====================================

@app.route('/search')
def search():

    query = request.args.get('query')

    items = Item.query.filter(
        Item.title.contains(query)
    ).all()

    return render_template(
        'search.html',
        items=items,
        query=query
    )


# ====================================
# DASHBOARD
# ====================================

@app.route('/dashboard')
@login_required
def dashboard():

    user_items = Item.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
    'my_listings.html',
    items=user_items
)

# ====================================
# DELETE ITEM
# ====================================

@app.route('/delete-item/<int:item_id>')
@login_required
def delete_item(item_id):

    item = Item.query.get_or_404(item_id)

    if item.user_id != current_user.id:

        flash('Unauthorized')

        return redirect('/')

    db.session.delete(item)

    db.session.commit()

    flash('Item deleted')

    return redirect('/dashboard')


# ====================================
# RUN APP
# ====================================

if __name__ == '__main__':

    app.run(debug=True)