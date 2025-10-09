import os
import sqlite3
from flask import Flask
from flask_login import LoginManager, UserMixin
from dotenv import load_dotenv

# ======================================================
# ⚙️ CONFIGURAÇÃO INICIAL
# ======================================================
load_dotenv()

DB_PATH = os.getenv("DB_PATH", "andorinha.db")
POWERBI_PUBLIC_URL = os.getenv("POWERBI_PUBLIC_URL", "")
SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "troque_este_seguro")  # alterar em produção

# ======================================================
# 🚀 INICIALIZAÇÃO DO APP
# ======================================================
app = Flask(__name__)
app.secret_key = SECRET_KEY

# ======================================================
# 🔐 CONFIGURAÇÃO DO LOGIN MANAGER
# ======================================================
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


# ======================================================
# 👤 CLASSE USER
# ======================================================
class User(UserMixin):
    """Classe de usuário compatível com Flask-Login."""
    def __init__(self, id_, username, password_hash, tipo, first_login=1):
        self.id = str(id_)
        self.username = username
        self.password_hash = password_hash
        self.tipo = int(tipo)
        self.first_login = int(first_login)

    def get_id(self):
        return self.id


# ======================================================
# 🗄️ FUNÇÕES DE BANCO
# ======================================================
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def find_user_by_username(username):
    """Busca usuário pelo nome."""
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, tipo, first_login FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        if row:
            return User(row["id"], row["username"], row["password_hash"], row["tipo"], row["first_login"])
        return None


def find_user_by_id(user_id):
    """Busca usuário pelo ID (usado pelo Flask-Login)."""
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, tipo, first_login FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        if row:
            return User(row["id"], row["username"], row["password_hash"], row["tipo"], row["first_login"])
        return None


def get_tipos():
    """Retorna lista de tuplas (tipo, classe), exceto admin."""
    with get_db_connection() as conn:
        return [
            (row["tipo"], row["classe"])
            for row in conn.execute(
                "SELECT tipo, classe FROM tipo_usuario WHERE classe <> 'Admin' ORDER BY classe"
            ).fetchall()
        ]


def get_dashboards(cliente=None):
    """Retorna dashboards, opcional por cliente."""
    query = "SELECT nome AS nome_dashboard, link FROM dashboard"
    params = ()
    if cliente:
        query += " WHERE cliente = ?"
        params = (cliente,)
    query += " ORDER BY nome"
    with get_db_connection() as conn:
        return [dict(row) for row in conn.execute(query, params).fetchall()]


# ======================================================
# 🔄 LOGIN MANAGER CALLBACK
# ======================================================
@login_manager.user_loader
def load_user(user_id):
    """Carrega usuário logado via Flask-Login."""
    return find_user_by_id(user_id)


# ======================================================
# 🧱 INICIALIZAÇÃO DO BANCO
# ======================================================
def init_db():
    """Cria as tabelas se ainda não existirem."""
    with get_db_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            tipo INTEGER NOT NULL DEFAULT 0,
            first_login INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS dashboard (
            cliente TEXT NOT NULL,
            nome TEXT NOT NULL,
            link TEXT NOT NULL,
            id INTEGER PRIMARY KEY AUTOINCREMENT
        );

        CREATE TABLE IF NOT EXISTS tipo_usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo INTEGER UNIQUE NOT NULL,
            classe TEXT NOT NULL
        );
        """)
    app.logger.info("Banco de dados inicializado com sucesso.")


# Inicializa banco ao iniciar o app
init_db()


# ======================================================
# 🌐 IMPORTA ROTAS EXTERNAS
# ======================================================
from views import *  # todas as rotas estão no views.py


# ======================================================
# ▶️ EXECUÇÃO LOCAL
# ======================================================
if __name__ == "__main__":
    app.run(debug=True)
