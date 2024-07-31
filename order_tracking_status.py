import concurrent.futures
from datetime import datetime
import requests

from conections import (
    CORREIOS_API_TRACKING_BASE_URL,
    CORREIOS_API_TOKEN,
    BRASPRESS_API_BASE_URL,
    BRASPRESS_HEADERS_API,
    BAGY_ORDERS_API_BASE_URL,
    BAGY_HEADERS_API,
    cnpj,
    get_mongodb_conection,
)
from body_email_pickup import body_email
from send_email import send_email

from locale import currency, setlocale, LC_ALL

setlocale(LC_ALL, "pt_BR.UTF-8")


def get_correios_tracking_data(ob):
    try:
        response = requests.get(
            CORREIOS_API_TRACKING_BASE_URL.format(ob),
            headers={"Authorization": f"Bearer {CORREIOS_API_TOKEN}"},
        )
        response.raise_for_status()
        return response.json()["objetos"][0]
    except requests.exceptions.RequestException as e:
        print(f"Falha na consulta do rastreamento do objeto {ob}: {e}")
        return None


def save_correios_tracking_data(tracking_data):
    mongoclient, collection = get_mongodb_conection()
    try:
        with mongoclient:
            db = mongoclient.RastreadorDB
            col = db.get_collection(collection)

            # Certifique-se de que há um índice no campo "codObjeto"
            col.create_index("codObjeto", unique=True)

            cod_objeto = tracking_data["codObjeto"]
            eventos_novos = tracking_data.get("eventos", [])

            obj = col.find_one({"codObjeto": cod_objeto}, {"_id": 0})

            if obj is None:
                col.insert_one(tracking_data)
            else:
                eventos_atuais = obj.get("eventos", [])
                if eventos_atuais != eventos_novos:
                    col.update_one(
                        {"codObjeto": cod_objeto},
                        {"$set": {"eventos": eventos_novos}},
                        upsert=True,
                    )
    except mongoclient.errors.PyMongoError as e:
        print(f"Erro ao acessar o MongoDB: {e}")


def get_braspress_tracking_data(nfe):
    try:
        response = requests.get(
            BRASPRESS_API_BASE_URL.format(cnpj, nfe),
            headers=BRASPRESS_HEADERS_API,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Falha na consulta do rastreamento da Braspress para NFe {nfe}: {e}")
        return None


def check_correios_tracking(order):
    shipping_code = order["fulfillment"]["shipping_code"].strip()
    tracking_data = get_correios_tracking_data(shipping_code)
    if tracking_data is None:
        return f"{shipping_code} - Falha na conexão com o rastreador dos Correios. Execução Cancelada!"
    # save_correios_tracking_data(tracking_data)
    order_id = str(order["fulfillment"]["order_id"])
    order_code = str(order["code"])
    order_transp = order["fulfillment"]["shipping_carrier"]
    email = order["customer"]["email"]
    name = order["customer"]["name"]
    order_total = currency(float(order["total"]), grouping=True, symbol=True)
    order_subtotal = currency(float(order["subtotal"]), grouping=True, symbol=True)
    order_discount = currency(float(order["discount"]), grouping=True, symbol=True)
    order_shipping_price = currency(
        float(order["shipping"]["price"]), grouping=True, symbol=True
    )
    order_tax = currency(float(order["tax"]), grouping=True, symbol=True)
    order_token = order["token"]
    order_shipping_delivery_time = order["shipping"]["delivery_time"]
    order_shipping_alias = order["shipping"]["alias"]
    order_instore = order["shipping"]["api"]
    order_add_msg = order["shipping"]["additional_message"]
    order_date = datetime.fromisoformat(order["created_at"]).strftime(
        "%d/%m/%Y %H:%M:%S"
    )
    details = ""
    address_pickup = ""
    event_status = ""
    msg = ""
    shipping_code = order["fulfillment"]["shipping_code"].strip()

    if "mensagem" not in tracking_data:
        evento_data = datetime.fromisoformat(
            tracking_data["eventos"][0]["dtHrCriado"]
        ).date()
        event_status = tracking_data["eventos"][0]["descricao"]
        event_details = (
            tracking_data["eventos"][0]["detalhe"]
            if "detalhe" in tracking_data["eventos"][0]
            else ""
        )
        event_type = tracking_data["eventos"][0]["tipo"]
        event_code = tracking_data["eventos"][0]["codigo"]
        unidade_uf = tracking_data["eventos"][0]["unidade"]["endereco"]["uf"]
        unidade_cidade = (
            tracking_data["eventos"][0]["unidade"]["endereco"]["cidade"]
            if "cidade" in tracking_data["eventos"][0]["unidade"]["endereco"]
            else "BR"
        )
        unidade_tipo = tracking_data["eventos"][0]["unidade"]["tipo"]
        if event_code in ["LDI"] and event_type in ["01", "03", "04"]:
            unidade_logradouro = tracking_data["eventos"][0]["unidade"]["endereco"][
                "logradouro"
            ]
            unidade_numero = tracking_data["eventos"][0]["unidade"]["endereco"][
                "numero"
            ]
            unidade_complemento = (
                tracking_data["eventos"][0]["unidade"]["endereco"]["complemento"]
                if "complemento" in tracking_data["eventos"][0]["unidade"]["endereco"]
                else ""
            )
            unidade_bairro = tracking_data["eventos"][0]["unidade"]["endereco"][
                "bairro"
            ]
            address_pickup = f""" Endereço para retirada: {unidade_tipo} - {unidade_logradouro},{unidade_numero}
                - {unidade_complemento} - {unidade_bairro} - {unidade_cidade} - {unidade_uf}"""
    else:
        event_status = tracking_data["mensagem"]

    if event_status == "SRO-020: Objeto não encontrado na base de dados dos Correios.":
        today = datetime.now()
        shipping_date = datetime.strptime(
            order["fulfillment"]["shipping_created_at"][0:10].replace("-", "/"),
            "%Y/%m/%d",
        )
        dias = (today - shipping_date).days
        print(dias)
        if dias > 90:
            requests.put(
                f"{BAGY_ORDERS_API_BASE_URL}/{order['id']}/fulfillment/delivered",
                headers=BAGY_HEADERS_API,
            )
        return f"""{order_code} - {order_transp} - {shipping_code} : 
            Objeto não encontrado na base de dados dos Correios."""

    elif event_status in [
        "Objeto entregue ao destinatário",
        "Objeto entregue na Caixa de Correios Inteligente",
    ]:
        response = requests.put(
            f"{BAGY_ORDERS_API_BASE_URL}/{order['id']}/fulfillment/delivered",
            headers=BAGY_HEADERS_API,
        )
        if response.status_code == 200:
            return f"Pedido {order_code} entregue. Status atualizado para Entregue na Bagy!"
        else:
            return f"Falha ao atualizar dados do pedido {order_code} - {response.status_code}!"

    elif event_status == ("Solicitação de suspensão de entrega recebida"):
        # Caso os Correios tenha solicitado a suspensão da entrega
        # devido um possível extravio ou roubo, verifica o status da entrega
        # do evento anterior
        if tracking_data["eventos"][1]["descricao"] in [
            "Objeto não localizado no fluxo postal",
            "Objeto roubado dos Correios",
        ]:
            return f"ATENÇÃO!! Objeto {shipping_code} referente ao pedido {order_code} foi extraviado pelo Correios"

    elif event_status == ("Objeto não localizado no fluxo postal"):
        return f"ATENÇÃO!! Objeto {shipping_code} referente ao pedido {order_code} foi extraviado pelo Correios"

    elif event_status in [
        # Envia email para o cliente caso o pedido esteja
        # aguardando retirada e inclui a tag Enviado e-mail Retirada
        # e inclui o endereço para retirada no histórico do pedido
        "Objeto aguardando retirada no endereço indicado",
        "Objeto disponível para retirada em Caixa Postal",
    ]:
        if order["tags"] is None:
            order["tags"] = []
        if "Enviado e-mail Retirada" not in order["tags"]:
            msg = event_status + ". " + details + " " + address_pickup
            history_data = {"status": "shipped", "note": msg}
            requests.post(
                f"{BAGY_ORDERS_API_BASE_URL}/{order['id']}/history",
                json=history_data,
                headers=BAGY_HEADERS_API,
            )
            body = body_email(
                order_code,
                order_date,
                name,
                event_status,
                event_details,
                address_pickup,
                order["items"],
                order_subtotal,
                order_discount,
                order_shipping_price,
                order_tax,
                order_total,
                order_instore,
                order["address"],
                order_add_msg,
                order_shipping_delivery_time,
                order_shipping_alias,
                order_token,
            )
            if order["marketplace"] is None:
                send_email(
                    email,
                    "Seu pedido está aguardando retirada",
                    body,
                    order_id,
                    {"tags": "Enviado e-mail Retirada"},
                )
            else:
                send_email(
                    "",
                    "Pedido {} aguardando retirada".format(
                        order["marketplace"]["marketplace_name"].upper()
                    ),
                    body,
                    order_id,
                    {"tags": "Enviado e-mail Retirada"},
                )
        return (
            f"Pedido {order_code} aguardando retirada. Informações atualizadas na Bagy!"
        )

    elif event_status == ("Objeto entregue ao remetente"):
        msg = event_status
        history_data = {"status": "shipped", "note": msg}
        requests.post(
            f"{BAGY_ORDERS_API_BASE_URL}/{order['id']}/history",
            json=history_data,
            headers=BAGY_HEADERS_API,
        )
        response = requests.put(
            f"{BAGY_ORDERS_API_BASE_URL}/{order['id']}/fulfillment/delivered",
            headers=BAGY_HEADERS_API,
        )
        if response.status_code == 200:
            return f"Pedido {order_code} RETORNOU AO REMETENTE. Status atualizado para Entregue na Bagy!"
        else:
            return f"Falha ao atualizar dados do pedido {order_code} - {response.status_code}!"

    else:
        return f"Pedido {order_code} está no status {event_status}."


def check_braspress_tracking(order):
    order_code = order["code"]
    nfe = order["fulfillment"]["nfe_number"]
    tracking_data = get_braspress_tracking_data(nfe)
    if tracking_data is None:
        return f"Falha na conexão com o rastreador da Braspress para NFe {nfe}. Execução Cancelada!"
    if tracking_data["conhecimentos"] != []:
        if tracking_data["conhecimentos"][0]["dataEntrega"] is not None:
            response = requests.put(
                f"{BAGY_ORDERS_API_BASE_URL}/{order['id']}/fulfillment/delivered",
                headers=BAGY_HEADERS_API,
            )
            if response.status_code == 200:
                return f"Pedido {order_code} entregue. Status atualizado para Entregue na Bagy!"
            else:
                return f"Falha ao atualizar dados do pedido {order_code} - {response.status_code}!"
        elif (
            tracking_data["conhecimentos"][0]["ultimaOcorrencia"]
            == "FINALIZADO PENDENTE"
            or tracking_data["conhecimentos"][0]["status"] == "PENDENTE"
            or tracking_data["conhecimentos"][0]["status"] == "FINALIZADO PENDENTE"
        ):
            return f"ATENÇÃO!! Pedido {order_code} está com o status {tracking_data['conhecimentos'][0]['status']} na Braspress."
        else:
            return f"Pedido {order_code} está com o status {tracking_data['conhecimentos'][0]['status']} na Braspress."
    else:
        return str(order["code"]) + " - " + order["fulfillment"]["shipping_carrier"]


def check_pickup_tracking(order):
    data_envio = datetime.strptime(
        order["fulfillment"]["shipping_created_at"][0:10], "%Y-%m-%d"
    )
    dias = (datetime.now() - data_envio).days
    if dias > 15:
        response = requests.put(
            f"{BAGY_ORDERS_API_BASE_URL}/{order['id']}/fulfillment/delivered",
            headers=BAGY_HEADERS_API,
        )
        if response.status_code == 200:
            return f"Pedido {order['code']} entregue. Status atualizado para Entregue na Bagy!"
        else:
            return f"Falha ao atualizar dados do pedido {order['code']} - {response.status_code}!"
    elif dias > 10:
        return f"ATENÇÃO! Verificar se o pedido {order['code']} ainda está aguardando retirada"

    return f"Pedido {order['code']} aguardando retirada na Loja!"


def process_tracking(order):
    carrier_id = order["fulfillment"]["shipping_carrier_id"]
    if carrier_id not in [8884, 12341, 20206]:
        return check_correios_tracking(order)
    elif carrier_id in [8884, 20206]:
        return check_braspress_tracking(order)
    elif carrier_id in [12341]:
        return check_pickup_tracking(order)


def process_order_tracking(order):
    try:
        result = process_tracking(order)
        print(result)
    except Exception as e:
        print(f"Erro no processamento do pedido {order['code']}: {e}")


def get_tracking_status_process():
    url_get_orders = (
        f"{BAGY_ORDERS_API_BASE_URL}?payment_status=approved"
        "&fulfillment_status=shipped&sort=code&limit=100$marketplace=0"
    )
    response = requests.get(url_get_orders, headers=BAGY_HEADERS_API)
    orders = response.json()["data"]
    links = response.json()["links"]
    while True:
        if links["next"] is not None:
            response = requests.get(links["next"], headers=BAGY_HEADERS_API)
            orders.extend(response.json()["data"])
            links = response.json()["links"]
        else:
            break
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(process_order_tracking, orders)


if __name__ == "__main__":
    get_tracking_status_process()
