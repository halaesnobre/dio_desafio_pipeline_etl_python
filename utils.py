import requests


def get_correios_token(token_API, cartao_postagem):
    URL_API_CORREIOS = "https://api.correios.com.br/token/v1/autentica/cartaopostagem"
    headers = {"Authorization": f"Basic {token_API}"}
    response = requests.post(URL_API_CORREIOS, json=cartao_postagem, headers=headers)
    data = response.json()
    return data["token"] if response.status_code == 201 else None