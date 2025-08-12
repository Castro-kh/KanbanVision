from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from werkzeug.security import generate_password_hash
import os

# Configuration de l'application Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kanban.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modèles
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)

class Operation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_operation = db.Column(db.String(100))
    poste = db.Column(db.String(50))
    operateur = db.Column(db.String(50))
    statut = db.Column(db.String(50))
    debut = db.Column(db.DateTime)
    fin = db.Column(db.DateTime)

# Initialisation de la base de données
with app.app_context():
    if os.path.exists("kanban.db"):
        os.remove("kanban.db")  # Supprimer l’ancienne base si elle existe
        print("🗑 Ancienne base supprimée.")

    db.create_all()
    print("✅ Nouvelle base kanban.db créée.")

    # Ajout d’un utilisateur admin
    admin = User(
        role='admin',
        username='admin',
        password_hash=generate_password_hash('admin123')
    )
    db.session.add(admin)
    db.session.commit()
    print("👤 Utilisateur admin ajouté (admin / admin123).")
