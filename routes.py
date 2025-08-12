from flask import render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from flask import send_file
from datetime import datetime
import io
from io import BytesIO
import pandas as pd
from app import app, db, Operation, User
from werkzeug.security import generate_password_hash

# ============================
# ADMIN PAGE (FILTRAGE)
# ============================
@app.route('/admin', methods=['GET'])
@login_required
def admin_page():
    if current_user.role != 'admin':
        flash("Accès refusé", "danger")
        return redirect(url_for('logout'))

    statut = request.args.get('statut')
    operateur = request.args.get('operateur')
    poste = request.args.get('poste')
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')

    query = Operation.query

    if statut and statut != "Tous":
        query = query.filter(Operation.statut == statut)
    if operateur:
        query = query.filter(Operation.operateur.ilike(f"%{operateur}%"))
    if poste:
        query = query.filter(Operation.poste.ilike(f"%{poste}%"))
    if date_debut:
        query = query.filter(Operation.debut >= datetime.strptime(date_debut, "%Y-%m-%d"))
    if date_fin:
        query = query.filter(Operation.fin <= datetime.strptime(date_fin, "%Y-%m-%d"))

    operations = query.order_by(Operation.id.desc()).all()
    return render_template('admin.html', operations=operations)

# ============================
# CREATION UTILISATEUR
# ============================
@app.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    if current_user.role != 'admin':
        flash("Accès refusé", "danger")
        return redirect(url_for('logout'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        new_user = User(username=username, password_hash=generate_password_hash(password), role=role)
        db.session.add(new_user)
        db.session.commit()
        flash("Utilisateur créé avec succès", "success")
        return redirect(url_for('admin_page'))

    return render_template('create_user.html')

# ============================
# DASHBOARD
# ============================
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash("Accès refusé", "danger")
        return redirect(url_for('logout'))

    operations = Operation.query.all()
    stats = {
        'total': len(operations),
        'a_faire': len([op for op in operations if op.statut == 'À faire']),
        'en_cours': len([op for op in operations if op.statut == 'En cours']),
        'controle': len([op for op in operations if op.statut == 'Contrôle']),
        'termine': len([op for op in operations if op.statut == 'Terminé'])
    }
    return render_template('dashboard.html', **stats)

# Modifier (GET pour afficher le formulaire, POST pour enregistrer)
@app.route('/edit_operation/<int:op_id>', methods=['GET', 'POST'])
@login_required
def edit_operation(op_id):
    if current_user.role != 'admin':
        flash("Accès refusé", "danger")
        return redirect(url_for('logout'))

    op = Operation.query.get_or_404(op_id)
    if request.method == 'POST':
        op.nom_operation = request.form['nom_operation']
        op.poste = request.form['poste']
        op.operateur = request.form['operateur']
        op.statut = request.form['statut']
        db.session.commit()
        flash("Opération modifiée", "success")
        return redirect(url_for('admin_page'))
    return render_template('edit_operation.html', op=op)

# Supprimer (POST)
@app.route('/delete_operation/<int:op_id>', methods=['POST'])
@login_required
def delete_operation(op_id):
    if current_user.role != 'admin':
        flash("Accès refusé", "danger")
        return redirect(url_for('logout'))

    op = Operation.query.get_or_404(op_id)
    db.session.delete(op)
    db.session.commit()
    flash("Opération supprimée", "info")
    return redirect(url_for('admin_page'))

@app.route('/export_excel')
@login_required
def export_excel():
    if current_user.role != 'admin':
        flash("Accès refusé", "danger")
        return redirect(url_for('index'))

    # 1) Récupération des données
    operations = Operation.query.all()
    rows = []
    for op in operations:
        rows.append({
            "ID": op.id,
            "Nom opération": op.nom_operation or "",
            "Poste": op.poste or "",
            "Opérateur": op.operateur or "",
            "Statut": op.statut or "",
            "Début": op.debut.strftime("%Y-%m-%d %H:%M") if op.debut else "",
            "Fin": op.fin.strftime("%Y-%m-%d %H:%M") if op.fin else "",
        })

    df = pd.DataFrame(rows, columns=["ID","Nom opération","Poste","Opérateur","Statut","Début","Fin"])

    # 2) Création du fichier Excel en mémoire
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sheet_name = 'Opérations'
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        wb  = writer.book
        ws  = writer.sheets[sheet_name]

        # Formats
        header_fmt = wb.add_format({
            'bold': True, 'font_color': 'white', 'bg_color': '#1f2937',
            'align': 'center', 'valign': 'vcenter', 'border': 1
        })
        cell_fmt = wb.add_format({'border': 1, 'valign': 'vcenter'})
        date_fmt = wb.add_format({'num_format': 'yyyy-mm-dd hh:mm', 'border': 1, 'valign': 'vcenter'})
        id_fmt   = wb.add_format({'border': 1, 'valign': 'vcenter', 'align': 'center'})

        # Appliquer le style d’en-tête
        for col_idx, col_name in enumerate(df.columns):
            ws.write(0, col_idx, col_name, header_fmt)

        # Appliquer formats cellule ligne par ligne (dates, id…)
        for row_idx in range(len(df)):
            # ID
            ws.write(row_idx+1, 0, df.iloc[row_idx]["ID"], id_fmt)
            # Nom, Poste, Opérateur, Statut
            ws.write(row_idx+1, 1, df.iloc[row_idx]["Nom opération"], cell_fmt)
            ws.write(row_idx+1, 2, df.iloc[row_idx]["Poste"], cell_fmt)
            ws.write(row_idx+1, 3, df.iloc[row_idx]["Opérateur"], cell_fmt)
            ws.write(row_idx+1, 4, df.iloc[row_idx]["Statut"], cell_fmt)
            # Dates (si non vide)
            debut_val = df.iloc[row_idx]["Début"]
            fin_val   = df.iloc[row_idx]["Fin"]
            if debut_val:
                # On réécrit au format datetime XlsxWriter si besoin
                try:
                    dt = pd.to_datetime(debut_val)
                    ws.write_datetime(row_idx+1, 5, dt.to_pydatetime(), date_fmt)
                except Exception:
                    ws.write(row_idx+1, 5, debut_val, cell_fmt)
            else:
                ws.write(row_idx+1, 5, "", cell_fmt)

            if fin_val:
                try:
                    dt = pd.to_datetime(fin_val)
                    ws.write_datetime(row_idx+1, 6, dt.to_pydatetime(), date_fmt)
                except Exception:
                    ws.write(row_idx+1, 6, fin_val, cell_fmt)
            else:
                ws.write(row_idx+1, 6, "", cell_fmt)

        # 3) Largeur auto des colonnes (simple & efficace)
        for col_idx, col_name in enumerate(df.columns):
            series = df[col_name].astype(str).fillna("")
            max_len = max([len(col_name)] + [len(x) for x in series.tolist()])
            # Un peu de marge
            ws.set_column(col_idx, col_idx, min(max_len + 2, 40))

        # 4) Filtre automatique + freeze panes
        ws.autofilter(0, 0, len(df), len(df.columns)-1)
        ws.freeze_panes(1, 0)

        # 5) Mise en couleur par statut (conditional formatting)
        status_col = 4  # index de colonne "Statut"
        last_row   = len(df)
        status_range = xl_range = f"{chr(65+status_col)}2:{chr(65+status_col)}{last_row+1}"  # ex: E2:E100

        ws.conditional_format(status_range, {
            'type':     'text',
            'criteria': 'containing',
            'value':    'À faire',
            'format':   wb.add_format({'bg_color': '#e5e7eb', 'border':1})
        })
        ws.conditional_format(status_range, {
            'type':     'text',
            'criteria': 'containing',
            'value':    'En cours',
            'format':   wb.add_format({'bg_color': '#fde68a', 'border':1})
        })
        ws.conditional_format(status_range, {
            'type':     'text',
            'criteria': 'containing',
            'value':    'Contrôle',
            'format':   wb.add_format({'bg_color': '#bae6fd', 'border':1})
        })
        ws.conditional_format(status_range, {
            'type':     'text',
            'criteria': 'containing',
            'value':    'Terminé',
            'format':   wb.add_format({'bg_color': '#bbf7d0', 'border':1})
        })

    output.seek(0)
    return send_file(
        output,
        download_name="operations.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )