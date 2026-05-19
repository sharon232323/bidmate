from extensions import db
from flask_login import UserMixin
from datetime import datetime


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
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    items = db.relationship(
        'Item',
        backref='seller',
        lazy=True,
        cascade="all, delete"
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
        db.ForeignKey('user.id'),
        nullable=False
    )