from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
import os
app = Flask(__name__)
app.secret_key = 'chave_secreta_reciclagem_2024'

DB_PATH = 'reciclagem.db'

app.secret_key = "sua_chave_secreta"
DB_PATH = 'reciclagem.db'
# ─── Banco de Dados ────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materiais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            descricao TEXT,
            instrucoes TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Inserir materiais de exemplo se a tabela estiver vazia
    cursor.execute('SELECT COUNT(*) FROM materiais')
    if cursor.fetchone()[0] == 0:
        exemplos = [
            ('Papel', 'Papel', 'Jornais, revistas, papelão', 'Manter seco e limpo, separar do papelão molhado'),
            ('Plástico PET', 'Plástico', 'Garrafas de refrigerante e água', 'Lavar e amassar antes de descartar'),
            ('Vidro', 'Vidro', 'Garrafas, potes e frascos', 'Não misturar com espelhos ou vidro temperado'),
            ('Alumínio', 'Metal', 'Latas de bebidas e alimentos', 'Lavar e amassar para economizar espaço'),
            ('Cobre', 'Metal', 'Fios e tubulações', 'Separar por tipo de metal'),
            ('Papelão', 'Papel', 'Caixas e embalagens', 'Desmontar e amarrar em fardos'),
        ]
        cursor.executemany(
            'INSERT INTO materiais (nome, categoria, descricao, instrucoes) VALUES (?,?,?,?)',
            exemplos
        )

    conn.commit()
    conn.close()

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# ─── Rotas ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        senha = hash_senha(request.form['senha'])

        conn = get_db()
        usuario = conn.execute(
            'SELECT * FROM usuarios WHERE email=? AND senha=?', (email, senha)
        ).fetchone()
        conn.close()

        if usuario:
            session['usuario_id'] = usuario['id']
            session['usuario_nome'] = usuario['nome']
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou senha incorretos.', 'danger')

    return render_template('login.html')

# CADASTRO
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        email = request.form['email'].strip()
        senha = request.form['senha']
        confirmar = request.form['confirmar']

        if senha != confirmar:
            flash('As senhas não coincidem.', 'danger')
            return render_template('cadastro.html')

        if len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
            return render_template('cadastro.html')

        try:
            conn = get_db()
            conn.execute(
                'INSERT INTO usuarios (nome, email, senha) VALUES (?,?,?)',
                (nome, email, hash_senha(senha))
            )
            conn.commit()
            conn.close()
            flash('Cadastro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Este email já está cadastrado.', 'danger')

    return render_template('cadastro.html')

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))

# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    total_materiais = conn.execute('SELECT COUNT(*) FROM materiais WHERE ativo=1').fetchone()[0]
    total_usuarios = conn.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0]
    categorias = conn.execute(
        'SELECT categoria, COUNT(*) as qtd FROM materiais WHERE ativo=1 GROUP BY categoria'
    ).fetchall()
    recentes = conn.execute(
        'SELECT * FROM materiais WHERE ativo=1 ORDER BY criado_em DESC LIMIT 5'
    ).fetchall()
    conn.close()

    return render_template('dashboard.html',
                           total_materiais=total_materiais,
                           total_usuarios=total_usuarios,
                           categorias=categorias,
                           recentes=recentes)

# LISTAR MATERIAIS
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

    query += ' ORDER BY nome'
    lista = conn.execute(query, params).fetchall()
    categorias = conn.execute(
        'SELECT DISTINCT categoria FROM materiais WHERE ativo=1 ORDER BY categoria'
    ).fetchall()
    conn.close()

    return render_template('materiais.html', lista=lista, categorias=categorias,
                           busca=busca, categoria_filtro=categoria_filtro)

# ADICIONAR MATERIAL
@app.route('/materiais/novo', methods=['GET', 'POST'])
def novo_material():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nome = request.form['nome'].strip()
        categoria = request.form['categoria'].strip()
        descricao = request.form['descricao'].strip()
        instrucoes = request.form['instrucoes'].strip()

        if not nome or not categoria:
            flash('Nome e categoria são obrigatórios.', 'danger')
            return render_template('material_form.html', material=None)

        conn = get_db()
        conn.execute(
            'INSERT INTO materiais (nome, categoria, descricao, instrucoes) VALUES (?,?,?,?)',
            (nome, categoria, descricao, instrucoes)
        )
        conn.commit()
        conn.close()
        flash(f'Material "{nome}" adicionado com sucesso!', 'success')
        return redirect(url_for('materiais'))

    return render_template('material_form.html', material=None)

# EDITAR MATERIAL
@app.route('/materiais/editar/<int:id>', methods=['GET', 'POST'])
def editar_material(id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    material = conn.execute('SELECT * FROM materiais WHERE id=?', (id,)).fetchone()

    if not material:
        conn.close()
        flash('Material não encontrado.', 'danger')
        return redirect(url_for('materiais'))

    if request.method == 'POST':
        nome = request.form['nome'].strip()
        categoria = request.form['categoria'].strip()
        descricao = request.form['descricao'].strip()
        instrucoes = request.form['instrucoes'].strip()

        conn.execute(
            'UPDATE materiais SET nome=?, categoria=?, descricao=?, instrucoes=? WHERE id=?',
            (nome, categoria, descricao, instrucoes, id)
        )
        conn.commit()
        conn.close()
        flash('Material atualizado com sucesso!', 'success')
        return redirect(url_for('materiais'))

    conn.close()
    return render_template('material_form.html', material=material)

# EXCLUIR MATERIAL (soft delete)
@app.route('/materiais/excluir/<int:id>', methods=['POST'])
def excluir_material(id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    conn.execute('UPDATE materiais SET ativo=0 WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('Material removido com sucesso.', 'info')
    return redirect(url_for('materiais'))

# USUÁRIOS (admin simples)
@app.route('/usuarios')
def usuarios():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    lista = conn.execute('SELECT id, nome, email, criado_em FROM usuarios ORDER BY criado_em DESC').fetchall()
    conn.close()
    return render_template('usuarios.html', lista=lista)

# ─── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    print("✅ Banco de dados inicializado!")
    print("🌐 Acesse: http://127.0.0.1:5000")
    app.run(debug=True)
