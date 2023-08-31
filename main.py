import os
import dotenv
from utils import get_correios_token

dotenv.load_dotenv()

api_correios = os.environ['correios_tokenkey_API']
cartao_postagem = os.environ['correios_cartao_postagem']

token_correios = get_correios_token(api_correios, cartao_postagem)