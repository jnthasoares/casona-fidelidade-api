# api.py (Versão final com captura da loja de origem)

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2 import IntegrityError
import os
import threading

# Importe seu gerenciador de e-mail se quiser enviar e-mails de boas-vindas
# import email_manager

app = Flask(__name__)

# Configuração do CORS para permitir requisições do seu site no Netlify e de testes locais
origins_permitidas = [
    "https://monumental-chaja-fb2a91.netlify.app",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]
CORS(app, resources={r"/cadastro": {"origins": origins_permitidas}})

# URL do banco de dados (a mesma dos seus outros apps)
DATABASE_URL = "postgresql://casona_user:jk9XTM0eT9sak0iv2pqggV7C4qTDm6Sb@dpg-d1aqmj15pdvs73d6n6r0-a.oregon-postgres.render.com/casona_fidelidade"


# Inicialize o gerenciador de e-mail se for usar
# mail_sender = email_manager.EmailManager()

def cadastrar_cliente_na_api(data):
    """
    Função que recebe os dados do formulário e insere no banco.
    Retorna (novo_codigo, None) em caso de sucesso, ou (None, mensagem_de_erro) em caso de falha.
    """
    conn = None
    try:
        # --- MUDANÇA: Captura a loja de origem dos dados recebidos ---
        loja_de_origem = data.get('lojaOrigem', 'Cadastro Online')

        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cursor:
            cursor.execute("SELECT nextval('codigo_cliente_seq')")
            novo_codigo_num = cursor.fetchone()[0]
            novo_codigo_str = f"{novo_codigo_num:04d}"

            # --- MUDANÇA: Query de INSERT atualizada para incluir a loja_origem ---
            query = """
                INSERT INTO clientes 
                (codigo, nome, telefone, email, data_nascimento, sexo, total_compras, total_gasto, contagem_brinde, loja_origem)
                VALUES (%s, %s, %s, %s, %s, %s, 0, 0.0, 0, %s)
            """
            params = (
                novo_codigo_str,
                data['nome'],
                data['telefone'],
                data['email'],
                data['dataNascimento'],
                data['sexo'],
                loja_de_origem  # <-- Valor da loja inserido aqui
            )
            cursor.execute(query, params)
            conn.commit()

            # Opcional: Enviar e-mail de boas-vindas em uma thread para não atrasar a resposta
            # threading.Thread(
            #     target=mail_sender.send_welcome_email,
            #     args=(data['email'], data['nome'], novo_codigo_str),
            #     daemon=True
            # ).start()

            return novo_codigo_str, None

    except IntegrityError:
        if conn: conn.rollback()
        # Este erro pode acontecer se você adicionar uma constraint UNIQUE no e-mail ou telefone.
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

    # --- MUDANÇA: Validação agora inclui o campo 'lojaOrigem' ---
    required_fields = ['nome', 'telefone', 'email', 'dataNascimento', 'sexo', 'lojaOrigem']
    if not all(k in data for k in required_fields):
        # A validação no frontend já deve pegar isso, mas é uma segurança extra.
        return jsonify({"sucesso": False, "mensagem": "Dados incompletos enviados ao servidor."}), 400

    novo_codigo, erro = cadastrar_cliente_na_api(data)

    if novo_codigo:
        return jsonify({
            "sucesso": True,
            "mensagem": "Cadastro realizado com sucesso!",
            "codigo": novo_codigo
        })
    else:
        return jsonify({"sucesso": False, "mensagem": erro}), 500


# Esta parte só é usada para testes locais
if __name__ == '__main__':
    # Render usa Gunicorn, mas para testes locais, o servidor do Flask é suficiente.
    # O Render injeta a variável de ambiente PORT.
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)