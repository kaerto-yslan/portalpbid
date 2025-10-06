from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from main import app, get_db_connection, get_tipos, get_dashboards, find_user_by_username
import sqlite3

# ======================================================
# 🔒 REDIRECIONA USUÁRIO PARA TROCA DE SENHA NO PRIMEIRO LOGIN
# ======================================================
@app.before_request
def force_first_login():
    if current_user.is_authenticated:
        endpoint = request.endpoint or ""
        if current_user.first_login == 1 and endpoint not in (
            "logout", "login", "change_password_first_time", "static"
        ):
            return redirect(url_for("change_password_first_time"))

# ======================================================
# 🔗 ROTA PRINCIPAL (REDIRECIONA PARA LOGIN OU HOMEPAGE)
# ======================================================
@app.route("/")
def index():
    return redirect(url_for("homepage") if current_user.is_authenticated else url_for("login"))

# ======================================================
# 🔐 LOGIN
# ======================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = find_user_by_username(username)
        if user and check_password_hash(user.password_hash, password):
            login_user(user)

            if user.first_login == 1:
                return redirect(url_for("change_password_first_time"))

            return redirect(url_for("homepage"))

        flash("Usuário ou senha inválidos.", "danger")

    return render_template("login.html")


# ======================================================
# 🔑 TROCA DE SENHA NO PRIMEIRO LOGIN
# ======================================================
@app.route("/primeira_troca_senha", methods=["GET", "POST"])
@login_required
def change_password_first_time():
    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not new_password or not confirm_password:
            flash("Preencha todos os campos.", "warning")
            return redirect(url_for("change_password_first_time"))

        if new_password != confirm_password:
            flash("As senhas não coincidem.", "danger")
            return redirect(url_for("change_password_first_time"))

        hashed_password = generate_password_hash(new_password)
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ?, first_login = 0 WHERE id = ?",
                (hashed_password, current_user.id)
            )
            conn.commit()

        flash("Senha alterada com sucesso!", "success")
        return redirect(url_for("homepage.html"))

    return render_template("primeira_troca_senha.html", username=current_user.username)


# ======================================================
# 🧍‍♂️ REGISTRO DE USUÁRIO
# ======================================================
@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    tipos = get_tipos()
    SENHA_PADRAO = "Tahto@2025"  # Defina aqui a senha padrão

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        tipo = request.form.get("tipo")

        if not username:
            flash("Preencha todos os campos.", "warning")
            return render_template("register.html", tipos=tipos)

        if not tipo or not tipo.isdigit() or int(tipo) not in [t[0] for t in tipos]:
            flash("Tipo de usuário inválido.", "danger")
            return render_template("register.html", tipos=tipos)

        tipo = int(tipo)
        hashed_password = generate_password_hash(SENHA_PADRAO)  # Sempre usa a mesma senha

        try:
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO users (username, password_hash, tipo, first_login) VALUES (?, ?, ?, 1)",
                    (username, hashed_password, tipo)
                )
                conn.commit()

            flash(f"Usuário cadastrado com sucesso! Senha padrão: {SENHA_PADRAO}", "success")
            return redirect(url_for("homepage"))

        except sqlite3.IntegrityError:
            flash("Usuário já existe.", "danger")

    return render_template("register.html", tipos=tipos)



# ======================================================
# 📊 DASHBOARD
# ======================================================
@app.route("/dashboard")
@login_required
def dashboard():
    with get_db_connection() as conn:
        clientes = [row["cliente"] for row in conn.execute(
            "SELECT DISTINCT cliente FROM dashboard ORDER BY cliente"
        ).fetchall()]
        dashboards = [dict(row) for row in conn.execute(
            "SELECT cliente, nome AS nome_dashboard, link FROM dashboard ORDER BY cliente, nome"
        ).fetchall()]

    return render_template(
        "dashboard.html",
        username=current_user.username,
        clientes=clientes,
        dashboards=dashboards
    )


# ======================================================
# 🏠 HOMEPAGE PERSONALIZADA POR TIPO
# ======================================================
@app.route("/homepage")
@login_required
def homepage():
    tipo = int(current_user.tipo)

    empresas = {
        1: "Admin",
        2: "Tahto",
        3: "Icatu",
        4: "Ifood",
        5: "Nio",
        6: "Sam's Club",
        7: "Quinto Andar",
        8: "Vero",
        9: "Zara",
    }

    empresa = empresas.get(tipo)

    # Admin e Tahto veem todos os dashboards
    dashboards = get_dashboards() if tipo in (1, 2) else get_dashboards(empresa)

    # Template baseado no tipo de usuário
    template_map = {
        1: "homepage_1.html",
        2: "homepage_2.html",
        3: "homepage_3.html",
        4: "homepage_4.html",
        5: "homepage_5.html",
        6: "homepage_6.html",
        7: "homepage_7.html",
        8: "homepage_8.html",
        9: "homepage_9.html",
    }
    template = template_map.get(tipo, "homepage.html")

    return render_template(template, username=current_user.username, dashboards=dashboards)


# ======================================================
# 📋 REGISTRO DE DASHBOARD
# ======================================================
@app.route("/register_dashboard", methods=["GET", "POST"])
@login_required
def register_dashboard():
    tipos = get_tipos()

    if request.method == "POST":
        cliente = request.form.get("cliente", "").strip()
        nome = request.form.get("nome", "").strip()
        link = request.form.get("link", "").strip()

        if not cliente or not nome or not link:
            flash("Todos os campos são obrigatórios.", "warning")
            return render_template("register_dashboard.html", tipos=tipos)

        try:
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO dashboard (cliente, nome, link) VALUES (?, ?, ?)",
                    (cliente, nome, link)
                )
                conn.commit()

            flash("Dashboard cadastrado com sucesso!", "success")
            return redirect(url_for("register_dashboard"))

        except sqlite3.IntegrityError:
            flash("Já existe um dashboard com esse nome.", "danger")

    return render_template("register_dashboard.html", tipos=tipos)


# ======================================================
# 🚪 LOGOUT
# ======================================================
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("login"))

@app.route('/gestao_dashboards')
def gestao_dashboards():
    conn = get_db_connection()
    dashboards = conn.execute('SELECT * FROM dashboard').fetchall()
    conn.close()
    return render_template('gestao_dashboards.html', dashboards=dashboards)

# --- Excluir Dashboard ---
@app.route('/excluir_dashboard/<int:id>', methods=['POST'])
def excluir_dashboard(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM dashboard WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Dashboard excluído com sucesso!', 'success')
    return redirect(url_for('gestao_dashboards'))

# --- Editar Dashboard ---
@app.route('/editar_dashboard/<int:id>', methods=['GET', 'POST'])
def editar_dashboard(id):
    conn = get_db_connection()
    dashboard = conn.execute('SELECT * FROM dashboard WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        cliente = request.form['cliente']
        nome = request.form['nome']
        link = request.form['link']
        
        conn.execute('UPDATE dashboard SET cliente = ?, nome = ?, link = ? WHERE id = ?',
                     (cliente, nome, link, id))
        conn.commit()
        conn.close()
        flash('Dashboard atualizado com sucesso!', 'success')
        return redirect(url_for('gestao_dashboards'))

    conn.close()
    return render_template('editar_dashboard.html', dashboard=dashboard)

@app.route("/gestao_usuarios")
def gestao_usuarios():
    conn = get_db_connection()
    # Pega usuários e o nome do tipo do usuário
    usuarios = conn.execute("""
        SELECT a.id, a.username, a.tipo, b.classe AS tipo_nome,
               CASE WHEN a.first_login = 1 THEN 'Não' ELSE 'Sim' END AS ja_fez_login
        FROM users a
        LEFT JOIN tipo_usuario b ON a.tipo = b.tipo
        where a.username <> 'admin'
    """).fetchall()
    conn.close()

    # Pega lista de tipos para o select
    conn = get_db_connection()
    tipos = conn.execute("SELECT tipo, classe FROM tipo_usuario").fetchall()
    conn.close()

    # Converte resultados para listas de dicionários (opcional, mas facilita o Jinja)
    usuarios = [dict(u) for u in usuarios]
    tipos = [(t['tipo'], t['classe']) for t in tipos]

    return render_template("gestao_usuarios.html", usuarios=usuarios, tipos=tipos)

# --- Alterar tipo ---
@app.route('/alterar_tipo/<int:user_id>', methods=['POST'])
def alterar_tipo(user_id):
    novo_tipo = request.form.get('novo_tipo')
    conn = get_db_connection()
    conn.execute("UPDATE users SET tipo = ? WHERE id = ?", (novo_tipo, user_id))
    conn.commit()
    conn.close()
    flash('Tipo do usuário atualizado com sucesso!', 'success')
    return redirect(url_for('gestao_usuarios'))

# --- Excluir usuário ---
@app.route('/excluir_usuario/<int:user_id>', methods=['POST'])
def excluir_usuario(user_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('gestao_usuarios'))

# --- Resetar senha ---
@app.route('/resetar_senha/<int:user_id>', methods=['POST'])
def resetar_senha(user_id):
    nova_senha = generate_password_hash("Tahto@2025")
    conn = get_db_connection()
    conn.execute("UPDATE users SET password_hash = ?, first_login = 1 WHERE id = ?", (nova_senha, user_id))
    conn.commit()
    conn.close()
    flash('Senha resetada com sucesso!', 'success')
    return redirect(url_for('gestao_usuarios'))