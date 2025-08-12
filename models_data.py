from extensions import db
from flask_login import UserMixin
from werkzeug.security import check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

class Operation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_operation = db.Column(db.String(120))
    poste = db.Column(db.String(120))
    operateur = db.Column(db.String(120))
    statut = db.Column(db.String(20))
    debut = db.Column(db.DateTime)
    fin = db.Column(db.DateTime)
