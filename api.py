# api.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2 import IntegrityError
import os

# Inicializa a aplicação Flask
app = Flask(__name__)

# Configura o CORS para permitir requisições do seu site no Netlify
# ATENÇÃO: Substitua pela URL real do seu site Netlify!
CORS(app, resources={r"/cadastro": {"origins": "https://monumental-chaja-fb2a91.netlify.app"}})

# URL do banco de dados (a mesma dos seus outros apps)
DATABASE_URL = "postgresql://casona_user:jk9XTM0eT9sak0iv2pqggV7C4qTDm6Sb@dpg-d1aqmj15pdvs73d6n6r0-a.oregon-postgres.render.com/casona_fidelidade"


def cadastrar_cliente_na_api(data):
    """
    Função que recebe os dados do formulário e insere no banco.
    Retorna (novo_codigo, None) em caso de sucesso, ou (None, mensagem_de_erro) em caso de falha.
    """
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cursor:
            # Pega o próximo código da sequência
            cursor.execute("SELECT nextval('codigo_cliente_seq')")
            novo_codigo_num = cursor.fetchone()[0]
            novo_codigo_str = f"{novo_codigo_num:04d}"

            # Insere o novo cliente
            query = """
                INSERT INTO clientes 
                (codigo, nome, telefone, email, data_nascimento, sexo, total_compras, total_gasto, contagem_brinde, loja_origem)
                VALUES (%s, %s, %s, %s, %s, %s, 0, 0.0, 0, 'Cadastro Online')
            """
            params = (
                novo_codigo_str,
                data['nome'],
                data['telefone'],
                data['email'],
                data['dataNascimento'],
                data['sexo']
            )
            cursor.execute(query, params)
            conn.commit()

            # Aqui você poderia adicionar o envio de e-mail de boas-vindas em uma thread

            return novo_codigo_str, None

    except IntegrityError as e:
        if conn: conn.rollback()
        # Pode ser um e-mail ou telefone já cadastrado, se você adicionar constraints UNIQUE
        return None, "Dados já existentes ou em conflito. Verifique as informações."
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERRO GERAL NA API: {e}")  # Log para você ver o erro
        return None, "Ocorreu um erro interno no servidor. Tente novamente mais tarde."
    finally:
        if conn: conn.close()


@app.route('/cadastro', methods=['POST'])
def handle_cadastro():
    # Pega os dados JSON enviados pelo frontend
    data = request.json

    # Validação básica no servidor (nunca confie 100% no frontend)
    if not all(k in data for k in ['nome', 'telefone', 'email', 'dataNascimento', 'sexo']):
        return jsonify({"sucesso": False, "mensagem": "Dados incompletos."}), 400

    novo_codigo, erro = cadastrar_cliente_na_api(data)

    if novo_codigo:
        return jsonify({
            "sucesso": True,
            "mensagem": "Cadastro realizado com sucesso!",
            "codigo": novo_codigo
        })
    else:
        # Retorna a mensagem de erro específica
        return jsonify({"sucesso": False, "mensagem": erro}), 500


# Esta parte só é usada para testes locais
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))