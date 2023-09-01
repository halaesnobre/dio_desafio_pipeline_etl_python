import os
import dotenv
import requests
import sqlite3
from pathlib import Path

dotenv.load_dotenv()

api_correios = os.environ['correios_tokenkey_API']
cartao_postagem = os.environ['correios_cartao_postagem']
db_sqlite = os.environ['db_sqlite']


def get_correios_token():
    URL_API_CORREIOS = "https://api.correios.com.br/token/v1/autentica/cartaopostagem"
    headers = {"Authorization": f"Basic {api_correios}"}
    response = requests.post(URL_API_CORREIOS, json=cartao_postagem, headers=headers)
    data = response.json()
    return data["token"] if response.status_code == 201 else None


def get_sqlite_conection():
    path = Path(__file__).parent
    conn = sqlite3.connect(path / db_sqlite)
    return conn