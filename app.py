
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'reciclagem', 'templates'))
app.secret_key = os.environ.get('SECRET_KEY', 'chave_secreta_2024')

DB_PATH = os.path.join(BASE_DIR, 'reciclagem', 'reciclagem.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS materiais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        categoria TEXT NOT NULL,
        descricao TEXT,
        instrucoes TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    if conn.execute('SELECT COUNT(*) FROM materiais').fetchone()[0] == 0:
        conn.executemany('INSERT INTO materiais (nome, categoria, descricao, instrucoes) VALUES (?,?,?,?)', [
            ('Papel', 'Papel', 'Jornais, revistas, papelão', 'Manter seco e limpo'),
            ('Plástico PET', 'Plástico', 'Garrafas de refrigerante e água', 'Lavar e amassar'),
            ('Vidro', 'Vidro', 'Garrafas, potes e frascos', 'Não misturar com vidro temperado'),
            ('Alumínio', 'Metal', 'Latas de bebidas e alimentos', 'Lavar e amassar'),
            ('Cobre', 'Metal', 'Fios e tubulações', 'Separar por tipo de metal'),
            ('Papelão', 'Papel', 'Caixas e embalagens', 'Desmontar e amarrar em fardos'),
        ])
    conn.commit()
    conn.close()


init_db()


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'usuario_id' in session else url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        senha = hash_senha(request.form['senha'])
        conn = get_db()
        usuario = conn.execute('SELECT * FROM usuarios WHERE email=? AND senha=?', (email, senha)).fetchone()
        conn.close()
        if usuario:
            session['usuario_id'] = usuario['id']
            session['usuario_nome'] = usuario['nome']
            return redirect(url_for('dashboard'))
        flash('Email ou senha incorretos.', 'danger')
    return render_template('login.html')


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        email = request.form['email'].strip()
        senha = request.form['senha']
        if senha != request.form['confirmar']:
            flash('As senhas não coincidem.', 'danger')
        elif len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
        else:
            try:
                conn = get_db()
                conn.execute('INSERT INTO usuarios (nome, email, senha) VALUES (?,?,?)',
                             (nome, email, hash_senha(senha)))
                conn.commit()
                conn.close()
                flash('Cadastro realizado! Faça login.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Este email já está cadastrado.', 'danger')
    return render_template('cadastro.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    total_materiais = conn.execute('SELECT COUNT(*) FROM materiais WHERE ativo=1').fetchone()[0]
    total_usuarios = conn.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0]
    categorias = conn.execute('SELECT categoria, COUNT(*) as qtd FROM materiais WHERE ativo=1 GROUP BY categoria').fetchall()
    recentes = conn.execute('SELECT * FROM materiais WHERE ativo=1 ORDER BY criado_em DESC LIMIT 5').fetchall()
    conn.close()
    return render_template('dashboard.html', total_materiais=total_materiais,
                           total_usuarios=total_usuarios, categorias=categorias, recentes=recentes)


@app.route('/materiais')
def materiais():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    busca = request.args.get('busca', '')
    categoria_filtro = request.args.get('categoria', '')
    conn = get_db()
    query = 'SELECT * FROM materiais WHERE ativo=1'
    params = []
    if busca:
        query += ' AND (nome LIKE ? OR descricao LIKE ?)'
        params += [f'%{busca}%', f'%{busca}%']
    if categoria_filtro:
        query += ' AND categoria=?'
        params.append(categoria_filtro)
    lista = conn.execute(query + ' ORDER BY nome', params).fetchall()
    categorias = conn.execute('SELECT DISTINCT categoria FROM materiais WHERE ativo=1 ORDER BY categoria').fetchall()
    conn.close()
    return render_template('materiais.html', lista=lista, categorias=categorias,
                           busca=busca, categoria_filtro=categoria_filtro)


@app.route('/materiais/novo', methods=['GET', 'POST'])
def novo_material():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        categoria = request.form['categoria'].strip()
        if not nome or not categoria:
            flash('Nome e categoria são obrigatórios.', 'danger')
        else:
            conn = get_db()
            conn.execute('INSERT INTO materiais (nome, categoria, descricao, instrucoes) VALUES (?,?,?,?)',
                         (nome, categoria, request.form['descricao'].strip(), request.form['instrucoes'].strip()))
            conn.commit()
            conn.close()
            flash(f'Material "{nome}" adicionado!', 'success')
            return redirect(url_for('materiais'))
    return render_template('material_form.html', material=None)


@app.route('/materiais/editar/<int:id>', methods=['GET', 'POST'])
def editar_material(id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    material = conn.execute('SELECT * FROM materiais WHERE id=?', (id,)).fetchone()
    if not material:
        conn.close()
        return redirect(url_for('materiais'))
    if request.method == 'POST':
        conn.execute('UPDATE materiais SET nome=?, categoria=?, descricao=?, instrucoes=? WHERE id=?',
                     (request.form['nome'].strip(), request.form['categoria'].strip(),
                      request.form['descricao'].strip(), request.form['instrucoes'].strip(), id))
        conn.commit()
        conn.close()
        flash('Material atualizado!', 'success')
        return redirect(url_for('materiais'))
    conn.close()
    return render_template('material_form.html', material=material)


@app.route('/materiais/excluir/<int:id>', methods=['POST'])
def excluir_material(id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute('UPDATE materiais SET ativo=0 WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('Material removido.', 'info')
    return redirect(url_for('materiais'))


@app.route('/usuarios')
def usuarios():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    lista = conn.execute('SELECT id, nome, email, criado_em FROM usuarios ORDER BY criado_em DESC').fetchall()
    conn.close()
    return render_template('usuarios.html', lista=lista)


if __name__ == '__main__':
    app.run(debug=True)