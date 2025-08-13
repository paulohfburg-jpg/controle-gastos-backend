# coding=utf-8
import sqlite3
from flask import Flask, jsonify, request, g, send_from_directory
from flask_cors import CORS

from datetime import datetime

# Define o nome do banco de dados SQLite
DATABASE = 'controle_gastos.db'
app = Flask(__name__, static_folder='static')
CORS(app)

# Função para conectar ao banco de dados
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Isso permite acessar colunas por nome
    return db

# Função para fechar a conexão do banco de dados ao final de cada requisição
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Função para criar as tabelas no banco de dados se elas não existirem
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS origens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                cor TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS caixas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                origem_id INTEGER,
                FOREIGN KEY (origem_id) REFERENCES origens(id)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saldos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                caixa_id INTEGER,
                mes INTEGER NOT NULL,
                ano INTEGER NOT NULL,
                valor REAL NOT NULL,
                FOREIGN KEY (caixa_id) REFERENCES caixas(id)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dividas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                caixa_id INTEGER,
                mes INTEGER NOT NULL,
                ano INTEGER NOT NULL,
                valor REAL NOT NULL,
                FOREIGN KEY (caixa_id) REFERENCES caixas(id)
            );
        """)
        db.commit()

# Inicializa o banco de dados na primeira execução
init_db()


# Endpoints da API para Origens
@app.route('https://controle-gastos-backend-9rox.onrender.com/api/origens', methods=['GET', 'POST'])
def handle_origens():
    db = get_db()
    if request.method == 'POST':
        data = request.json
        cursor = db.cursor()
        cursor.execute("INSERT INTO origens (descricao, cor) VALUES (?, ?)", (data['descricao'], data['cor']))
        db.commit()
        return jsonify({"message": "Origem cadastrada com sucesso!"}), 201
    else:  # GET
        cursor = db.cursor()
        cursor.execute("SELECT * FROM origens")
        origens = cursor.fetchall()
        return jsonify([dict(origem) for origem in origens])

@app.route('https://controle-gastos-backend-9rox.onrender.com/api/origens/<int:id>', methods=['PUT', 'DELETE'])
def handle_origem_by_id(id):
    db = get_db()
    cursor = db.cursor()
    if request.method == 'PUT':
        data = request.json
        cursor.execute("UPDATE origens SET descricao = ?, cor = ? WHERE id = ?", (data['descricao'], data['cor'], id))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Origem não encontrada"}), 404
        return jsonify({"message": "Origem atualizada com sucesso!"})
    else:  # DELETE
        cursor.execute("DELETE FROM origens WHERE id = ?", (id,))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Origem não encontrada"}), 404
        return jsonify({"message": "Origem excluída com sucesso!"})

# Endpoints da API para Caixas
@app.route('https://controle-gastos-backend-9rox.onrender.com/api/caixas', methods=['GET', 'POST'])
def handle_caixas():
    db = get_db()
    if request.method == 'POST':
        data = request.json
        cursor = db.cursor()
        cursor.execute("INSERT INTO caixas (descricao, origem_id) VALUES (?, ?)", (data['descricao'], data['origem_id']))
        db.commit()
        return jsonify({"message": "Caixa cadastrado com sucesso!"}), 201
    else:  # GET
        cursor = db.cursor()
        cursor.execute("SELECT caixas.id, caixas.descricao, caixas.origem_id, origens.descricao AS origem_descricao, origens.cor AS origem_cor FROM caixas JOIN origens ON caixas.origem_id = origens.id")
        caixas = cursor.fetchall()
        return jsonify([dict(caixa) for caixa in caixas])

@app.route('https://controle-gastos-backend-9rox.onrender.com/api/caixas/<int:id>', methods=['PUT', 'DELETE'])
def handle_caixa_by_id(id):
    db = get_db()
    cursor = db.cursor()
    if request.method == 'PUT':
        data = request.json
        cursor.execute("UPDATE caixas SET descricao = ?, origem_id = ? WHERE id = ?", (data['descricao'], data['origem_id'], id))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Caixa não encontrado"}), 404
        return jsonify({"message": "Caixa atualizado com sucesso!"})
    else:  # DELETE
        cursor.execute("DELETE FROM caixas WHERE id = ?", (id,))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Caixa não encontrado"}), 404
        return jsonify({"message": "Caixa excluído com sucesso!"})

# Endpoints da API para Saldos
@app.route('https://controle-gastos-backend-9rox.onrender.com/api/saldos', methods=['GET', 'POST'])
def handle_saldos():
    db = get_db()
    if request.method == 'POST':
        data = request.json
        cursor = db.cursor()
        cursor.execute("INSERT INTO saldos (descricao, caixa_id, mes, ano, valor) VALUES (?, ?, ?, ?, ?)", (data['descricao'], data['caixa_id'], data['mes'], data['ano'], data['valor']))
        db.commit()
        return jsonify({"message": "Saldo cadastrado com sucesso!"}), 201
    else:  # GET
        cursor = db.cursor()
        # Join com 'caixas' e 'origens' para obter todos os dados necessários para a página principal
        cursor.execute("""
            SELECT s.*, c.descricao AS caixa_descricao, o.descricao AS origem_descricao, o.cor AS origem_cor
            FROM saldos s
            JOIN caixas c ON s.caixa_id = c.id
            JOIN origens o ON c.origem_id = o.id
        """)
        saldos = cursor.fetchall()
        return jsonify([dict(saldo) for saldo in saldos])

@app.route('/api/saldos/<int:id>', methods=['PUT', 'DELETE'])
def handle_saldo_by_id(id):
    db = get_db()
    cursor = db.cursor()
    if request.method == 'PUT':
        data = request.json
        cursor.execute("UPDATE saldos SET descricao = ?, caixa_id = ?, mes = ?, ano = ?, valor = ? WHERE id = ?", (data['descricao'], data['caixa_id'], data['mes'], data['ano'], data['valor'], id))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Saldo não encontrado"}), 404
        return jsonify({"message": "Saldo atualizado com sucesso!"})
    else:  # DELETE
        cursor.execute("DELETE FROM saldos WHERE id = ?", (id,))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Saldo não encontrado"}), 404
        return jsonify({"message": "Saldo excluído com sucesso!"})

# Endpoints da API para Dívidas
@app.route('https://controle-gastos-backend-9rox.onrender.com/api/dividas', methods=['GET', 'POST'])
def handle_dividas():
    db = get_db()
    if request.method == 'POST':
        data = request.json
        cursor = db.cursor()
        cursor.execute("INSERT INTO dividas (descricao, caixa_id, mes, ano, valor) VALUES (?, ?, ?, ?, ?)", (data['descricao'], data['caixa_id'], data['mes'], data['ano'], data['valor']))
        db.commit()
        return jsonify({"message": "Dívida cadastrada com sucesso!"}), 201
    else:  # GET
        cursor = db.cursor()
        # Join com 'caixas' e 'origens' para obter todos os dados necessários para a página principal
        cursor.execute("""
            SELECT d.*, c.descricao AS caixa_descricao, o.descricao AS origem_descricao, o.cor AS origem_cor
            FROM dividas d
            JOIN caixas c ON d.caixa_id = c.id
            JOIN origens o ON c.origem_id = o.id
        """)
        dividas = cursor.fetchall()
        return jsonify([dict(divida) for divida in dividas])

@app.route('https://controle-gastos-backend-9rox.onrender.com/api/dividas/<int:id>', methods=['PUT', 'DELETE'])
def handle_divida_by_id(id):
    db = get_db()
    cursor = db.cursor()
    if request.method == 'PUT':
        data = request.json
        cursor.execute("UPDATE dividas SET descricao = ?, caixa_id = ?, mes = ?, ano = ?, valor = ? WHERE id = ?", (data['descricao'], data['caixa_id'], data['mes'], data['ano'], data['valor'], id))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Dívida não encontrada"}), 404
        return jsonify({"message": "Dívida atualizada com sucesso!"})
    else:  # DELETE
        cursor.execute("DELETE FROM dividas WHERE id = ?", (id,))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Dívida não encontrada"}), 404
        return jsonify({"message": "Dívida excluída com sucesso!"})

# Endpoints para a Página Principal (filtragem e totais)
@app.route('https://controle-gastos-backend-9rox.onrender.com/api/dashboard', methods=['GET'])
def get_dashboard_data():
    db = get_db()
    cursor = db.cursor()

    mes = request.args.get('mes')
    ano = request.args.get('ano')
    origem_id = request.args.get('origem_id')

    # Query para Saldos com filtros
    saldos_query = """
        SELECT s.*, c.descricao AS caixa_descricao, o.descricao AS origem_descricao, o.cor AS origem_cor
        FROM saldos s
        JOIN caixas c ON s.caixa_id = c.id
        JOIN origens o ON c.origem_id = o.id
        WHERE 1=1
    """
    params = []
    if mes:
        saldos_query += " AND s.mes = ?"
        params.append(mes)
    if ano:
        saldos_query += " AND s.ano = ?"
        params.append(ano)
    if origem_id:
        saldos_query += " AND o.id = ?"
        params.append(origem_id)
    
    cursor.execute(saldos_query, tuple(params))
    saldos = cursor.fetchall()

    # Query para Dívidas com filtros
    dividas_query = """
        SELECT d.*, c.descricao AS caixa_descricao, o.descricao AS origem_descricao, o.cor AS origem_cor
        FROM dividas d
        JOIN caixas c ON d.caixa_id = c.id
        JOIN origens o ON c.origem_id = o.id
        WHERE 1=1
    """
    params = []
    if mes:
        dividas_query += " AND d.mes = ?"
        params.append(mes)
    if ano:
        dividas_query += " AND d.ano = ?"
        params.append(ano)
    if origem_id:
        dividas_query += " AND o.id = ?"
        params.append(origem_id)
    
    cursor.execute(dividas_query, tuple(params))
    dividas = cursor.fetchall()

    # Query para totais
    totais_origem_query = """
        SELECT o.id, o.descricao, o.cor,
               SUM(CASE WHEN s.id IS NOT NULL THEN s.valor ELSE 0 END) AS saldo_total,
               SUM(CASE WHEN d.id IS NOT NULL THEN d.valor ELSE 0 END) AS divida_total
        FROM origens o
        LEFT JOIN caixas c ON o.id = c.origem_id
        LEFT JOIN saldos s ON c.id = s.caixa_id AND (s.mes = ? OR ? IS NULL) AND (s.ano = ? OR ? IS NULL)
        LEFT JOIN dividas d ON c.id = d.caixa_id AND (d.mes = ? OR ? IS NULL) AND (d.ano = ? OR ? IS NULL)
        GROUP BY o.id, o.descricao, o.cor
    """
    params_totais = [mes, mes, ano, ano, mes, mes, ano, ano]
    cursor.execute(totais_origem_query, tuple(params_totais))
    totais_por_origem = cursor.fetchall()
    
    # Cálculo do Saldo Final
    saldo_final_por_origem = []
    for item in totais_por_origem:
        saldo_final_por_origem.append({
            "id": item['id'],
            "descricao": item['descricao'],
            "cor": item['cor'],
            "saldo_total": item['saldo_total'],
            "divida_total": item['divida_total'],
            "saldo_final": item['saldo_total'] - item['divida_total']
        })

    return jsonify({
        "saldos": [dict(s) for s in saldos],
        "dividas": [dict(d) for d in dividas],
        "totais_por_origem": [dict(t) for t in totais_por_origem],
        "saldo_final_por_origem": saldo_final_por_origem
    })

# Rota para servir o frontend
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))  # Render define PORT, localmente usa 5000
    app.run(host="0.0.0.0", port=port, debug=True)

