from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kanban.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ============================
# MODELS
# ============================
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============================
# ROUTE LOGIN / INDEX
# ============================
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        role = request.form['role']
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, role=role).first()
        if user and user.verify_password(password):
            login_user(user)
            if role == 'admin':
                return redirect(url_for('admin_page'))
            else:
                return redirect(url_for('kanban'))
        else:
            flash('Identifiants incorrects.')
    return render_template('index.html')

@app.route('/kanban', methods=['GET'])
@login_required
def kanban():
    if current_user.role != 'operateur':
        flash("Accès refusé", "danger")
        return redirect(url_for('logout'))

    operations = Operation.query.filter_by(operateur=current_user.username).all()
    return render_template('kanban.html', operations=operations)

@app.route('/new_operation', methods=['POST'])
@login_required
def new_operation():
    if current_user.role != 'operateur':
        return "Accès refusé", 403

    op = Operation(
        nom_operation=request.form['nom_operation'],
        poste=request.form['poste'],
        operateur=current_user.username,
        statut='À faire',
        debut=None,
        fin=None
    )
    db.session.add(op)
    db.session.commit()
    return redirect(url_for('kanban'))

@app.route('/start/<int:op_id>')
@login_required
def start_operation(op_id):
    op = Operation.query.get_or_404(op_id)

    if op.operateur != current_user.username and current_user.role != 'admin':
        flash("Vous n'avez pas le droit de démarrer cette opération.", "danger")
        return redirect(url_for('kanban'))

    op.statut = 'En cours'
    op.debut = datetime.now()
    db.session.commit()
    flash("Opération démarrée", "success")
    return redirect(url_for('kanban'))


@app.route('/finish/<int:op_id>')
@login_required
def finish_operation(op_id):
    op = Operation.query.get_or_404(op_id)
    if op.statut == 'En cours':
        op.statut = 'Contrôle'
    elif op.statut == 'Contrôle':
        op.statut = 'Terminé'
    op.fin = datetime.now()
    db.session.commit()
    return redirect(url_for('kanban'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Importer les routes Admin
import routes

if __name__ == '__main__':
    app.run(debug=True)
