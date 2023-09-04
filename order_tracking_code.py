import requests
import concurrent.futures
from conections import (get_sqlite_conection, get_sql_conection,
                        BRASPRESS_API_BASE_URL, BRASPRESS_HEADERS_API,
                        BAGY_ORDERS_API_BASE_URL, BAGY_HEADERS_API, cnpj)


def get_tracking_code(order):
    con = get_sqlite_conection()
    cursor_pos = con.cursor()

    nfe = order['fulfillment']['nfe_number']
    envio = None

    if order['shipping']['carrier_id'] == 12341:
        envio = {
            "shipping_carrier_id": 12341,
            "shipping_code": "Produto aguardando retirada.",
            "shipping_carrier": "Retira na Loja"
        }
        response = requests.put(f"{BAGY_ORDERS_API_BASE_URL}/{order['id']}/fulfillment/shipped",
            json=envio, headers=BAGY_HEADERS_API)
        if response.status_code == 200:
            return f"Rastreamento do pedido {order['code']} atualizada com sucesso na Bagy!"
        else:
            return f"Falha ao atualizar pedido {order['code']} na Bagy: {response.status_code}"

    cursor_pos.execute(
        f"SELECT COD_POSTAL, ID_TRANSP FROM POSTAGENS WHERE DESTINATARIO = {nfe}?")
    row = cursor_pos.fetchone()
    cursor_pos.close()
    con.close()
    if row is not None:
        envio = {
            "shipping_carrier_id": row[1],
            "shipping_code": row[0],
            "shipping_carrier": "Correios"
        }
    else:
        try:
            response = requests.get(BRASPRESS_API_BASE_URL.format(cnpj, nfe), headers=BRASPRESS_HEADERS_API)
            tracking = response.json()['conhecimentos']
        except Exception as e:
            return f"Falha ao buscar tracking do pedido {order['code']} na Braspress: {e}"
        
        if tracking != []:
            awb = tracking[0]['numero']
            envio = {
                "shipping_carrier_id": 8884,
                "shipping_code": str(awb),
                "shipping_carrier": "Braspress"
            }
    
    if envio:
        resp = requests.put(BAGY_ORDERS_API_BASE_URL + f"/{order['id']}/fulfillment/shipped",
                            json=envio, headers=BAGY_HEADERS_API)
        if resp.status_code == 200:
            return f"Rastreamento do pedido {order['code']} atualizada com sucesso na Bagy!"
        else:
            return f"Falha ao atualizar pedido {order['code']} na Bagy: {resp.status_code}"
    
# Verifica se a nota fiscal informada anteriormente foi cancelada
# e atualiza a nota fiscal no pedido caso esteja  
    qr = (
        "SELECT A.nffs_nfs, A.nffs_ser, c.CNFL_NFL, e.ENCV_STR_NUMRAS "
        "FROM TCOM_NFFSAI A "
        "INNER JOIN TCOM_PEDSAI B ON A.PEDS_COD = b.PEDS_COD "
        "INNER JOIN TOPE_CTRNFL C ON A.nffs_cod = c.NFFS_COD "
        "INNER JOIN TCOM_ENCNFS D ON A.nffs_cod = D.NFFS_COD "
        "INNER JOIN TCOM_ENCVOL E ON d.ENCV_COD = e.ENCV_COD "
        f"WHERE a.UNID_COD = 1 AND b.PEDS_EXT_COD = 'D{order['code']}'"
    )
    con_erp = get_sql_conection()
    cursor_erp = con_erp.cursor()
    cursor_erp.execute(qr)
    row = cursor_erp.fetchone()
    cursor_erp.close()
    con_erp.close()
    if row is not None and str(row[0]) != order['fulfillment']['nfe_number']:
        nfe_data = {
            "nfe_number": str(row[0]),
            "nfe_token": str(row[2]),
            "nfe_series": str(row[1]).strip()
        }
        resp = requests.put(f'{BAGY_ORDERS_API_BASE_URL}/{order["id"]}/fulfillment/invoiced',
                            json=nfe_data, headers=BAGY_HEADERS_API)
        if resp.status_code == 200:
            return f"Nota fiscal do pedido {order['code']} atualizada com sucesso na Bagy!"
        else:
            return f"Falha ao atualizar nota fiscal do pedido {order['code']} na Bagy: {resp.status_code}"
    
    con.close()
    return (
        f"Pedido {order['code']} faturado em "
        f"{order['fulfillment']['nfe_created_at']} não enviado até o momento"
    )

def process_ped(order):
    try:
        result = get_tracking_code(order)
        print(f'Situação: {result}')
    except Exception as exc:
        print(f"{order['code']} generated an exception:{exc}")


def get_tracking_code_process():
    url_get_orders = (f"{BAGY_ORDERS_API_BASE_URL}?payment_status=approved"
                        "&fulfillment_status=invoiced&sort=code&limit=100")
    response = requests.get(url_get_orders, headers=BAGY_HEADERS_API)
    orders = response.json()["data"]
    links = response.json()["links"]
    while True:
        if links['next'] is not None:
            response = requests.get(orders['links']['next'], headers=BAGY_HEADERS_API)
            orders.append(response.json()["data"])
            links = response.json()["links"]
        else:
            break
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(process_ped, orders)


if __name__ == '__main__':
    get_tracking_code_process()
