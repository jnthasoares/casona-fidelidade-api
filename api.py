# api.py (Versão final com CÓDIGO DE 5 DÍGITOS)

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2 import IntegrityError
import os
import threading
import email_manager

app = Flask(__name__)

origins_permitidas = [
    "https://monumental-chaja-fb2a91.netlify.app",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]
CORS(app, resources={r"/cadastro": {"origins": origins_permitidas}})

DATABASE_URL = "postgresql://casona_user:jk9XTM0eT9sak0iv2pqggV7C4qTDm6Sb@dpg-d1aqmj15pdvs73d6n6r0-a.oregon-postgres.render.com/casona_fidelidade"

mail_sender = email_manager.EmailManager()


def cadastrar_cliente_na_api(data):
    conn = None
    try:
        loja_de_origem = data.get('lojaOrigem', 'Cadastro Online')
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cursor:
            cursor.execute("SELECT nextval('codigo_cliente_seq')")
            novo_codigo_num = cursor.fetchone()[0]

            # --- MUDANÇA PRINCIPAL AQUI ---
            novo_codigo_str = f"{novo_codigo_num:05d}"  # Alterado de 04d para 05d

            query = """
                INSERT INTO clientes 
                (codigo, nome, telefone, email, data_nascimento, sexo, total_compras, total_gasto, contagem_brinde, loja_origem)
                VALUES (%s, %s, %s, %s, %s, %s, 0, 0.0, 0, %s)
            """
            params = (
                novo_codigo_str, data['nome'], data['telefone'], data['email'],
                data['dataNascimento'], data['sexo'], loja_de_origem
            )
            cursor.execute(query, params)
            conn.commit()

            threading.Thread(
                target=mail_sender.send_welcome_email,
                args=(data['email'], data['nome'], novo_codigo_str),
                daemon=True
            ).start()

            return novo_codigo_str, None
    except IntegrityError:
        if conn: conn.rollback()
        return None, "Este e-mail ou telefone já pode estar cadastrado."
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERRO GERAL NA API: {e}")
        return None, "Ocorreu um erro interno no servidor. Tente novamente mais tarde."
    finally:
        if conn: conn.close()


@app.route('/cadastro', methods=['POST'])
def handle_cadastro():
    data = request.json
    required_fields = ['nome', 'telefone', 'email', 'dataNascimento', 'sexo', 'lojaOrigem']
    if not all(k in data for k in required_fields):
        return jsonify({"sucesso": False, "mensagem": "Dados incompletos enviados ao servidor."}), 400
    novo_codigo, erro = cadastrar_cliente_na_api(data)
    if novo_codigo:
        return jsonify({"sucesso": True, "mensagem": "Cadastro realizado com sucesso!", "codigo": novo_codigo})
    else:
        return jsonify({"sucesso": False, "mensagem": erro}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)