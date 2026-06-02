# ♻️ EcoRecicla — Sistema de Reciclagem

Sistema web simples para testar banco de dados SQLite com Flask.

## 🚀 Como rodar no PyCharm

### 1. Instalar dependência
```
pip install flask
```
Ou no terminal do PyCharm:
```
pip install -r requirements.txt
```

### 2. Executar
```
python app.py
```

### 3. Acessar no navegador
```
http://127.0.0.1:5000
```

---

## 📁 Estrutura do Projeto
```
reciclagem/
├── app.py               ← Aplicação principal (Flask)
├── requirements.txt     ← Dependências
├── reciclagem.db        ← Banco SQLite (criado automaticamente)
└── templates/
    ├── base.html        ← Layout base
    ├── login.html       ← Tela de login
    ← Tela de cadastro
    ├── dashboard.html   ← Dashboard
    ├── materiais.html   ← Lista de materiais
    ├── material_form.html ← Formulário add/editar
    └── usuarios.html    ← Lista de usuários
```

## 🗄️ Banco de Dados (SQLite)

### Tabela `usuarios`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER | Chave primária |
| nome | TEXT | Nome do usuário |
| email | TEXT | Email único |
| senha | TEXT | Senha (SHA-256) |
| criado_em | TIMESTAMP | Data de cadastro |

### Tabela `materiais`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER | Chave primária |
| nome | TEXT | Nome do material |
| categoria | TEXT | Categoria (Papel, Plástico, etc) |
| descricao | TEXT | Descrição |
| instrucoes | TEXT | Instruções de descarte |
| ativo | INTEGER | 1=ativo, 0=removido |
| criado_em | TIMESTAMP | Data de cadastro |

## ✅ Funcionalidades
- [x] Cadastro de usuário
- [x] Login / Logout com sessão
- [x] Dashboard com estatísticas
- [x] CRUD completo de materiais
- [x] Filtro e busca de materiais
- [x] Lista de usuários
- [x] Dados de exemplo pré-cadastrados
