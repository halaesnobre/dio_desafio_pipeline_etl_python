import os
import dotenv
import requests
import sqlite3
import pyodbc
from pathlib import Path

dotenv.load_dotenv()

#Variables
cnpj = os.environ['cnpj']
api_correios = os.environ['correios_tokenkey_API']
cartao_postagem = os.environ['correios_cartao_postagem']
db_sqlite = os.environ['db_sqlite']
db_server = os.environ['erp_banco_server']
db_database = os.environ['erp_database']
db_user = os.environ['erp_db_username']
db_password = os.environ['erp_db_password']
bagy_token = os.environ['bagy_token']
braspress_token = os.environ['braspress_token']
email_smtp_server = os.environ['email_smtp_server']
email_smtp_port = os.environ['email_smtp_port']
email_smtp_user = os.environ['email_smtp_user']
email_smtp_password = os.environ['email_smtp_password']
email_sender = os.environ['email_sender']

#URLs API Bagy
BAGY_HEADERS_API = {'Authorization': f'Bearer {bagy_token}'}
BAGY_ORDERS_API_BASE_URL = 'https://api.dooca.store/orders'

#URLs API Braspress
BRASPRESS_HEADERS_API = {'Authorization': f'Basic {braspress_token}',
                         'Content-Type': 'application/json;charset=UTF-8',
                         'User-Agent': 'Rastro/1.0'}
BRASPRESS_API_BASE_URL = "https://api.braspress.com/v1/tracking/{}/{}/json"


def get_correios_token():
    headers = {"Authorization": f"Basic {api_correios}"}
    response = requests.post(CORREIOS_API_AUTENTICATION_BASE_URL, json=cartao_postagem, headers=headers)
    data = response.json()
    return data["token"] if response.status_code == 201 else None

#URLs API Correios
CORREIOS_API_TRACKING_BASE_URL = "https://api.correios.com.br/srorastro/v1/objetos/{}?resultado=T"
CORREIOS_API_AUTENTICATION_BASE_URL = "https://api.correios.com.br/token/v1/autentica/cartaopostagem"
CORREIOS_API_TOKEN = get_correios_token()


def get_sqlite_conection():
    path = Path(__file__).parent
    conn = sqlite3.connect(path / db_sqlite)
    return conn


def get_sql_conection():
    server = db_server
    database = db_database
    username = db_user
    password = db_password
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        + f"SERVER={server};DATABASE={database};UID={username};PWD={password}"
    )
    return conn