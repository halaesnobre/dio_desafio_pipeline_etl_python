import requests
import concurrent.futures
from conections import get_sql_conection, BAGY_ORDERS_API_BASE_URL, BAGY_HEADERS_API


def get_nota(order):
    order_id = order["id"]
    order_code = order["code"]
    url_fulfillment = f"{BAGY_ORDERS_API_BASE_URL}/{order_id}/fulfillment"
    con = get_sql_conection()
    concur = con.cursor()
    sql = f"""select A.nffs_nfs, A.nffs_ser, c.CNFL_NFL from TCOM_NFFSAI A
    inner join TCOM_PEDSAI B on a.PEDS_COD = b.PEDS_COD
    inner join TOPE_CTRNFL C on A.nffs_cod = c.NFFS_COD
    where a.UNID_COD = 1 and b.PEDS_EXT_COD = 'D{order_code}';"""
    concur.execute(sql)
    row = concur.fetchone()
    if row is not None:
        data = {
            "nfe_number": str(row[0]),
            "nfe_token": str(row[2]),
            "nfe_series": str(row[1]).strip(),
        }
        resp = requests.put(
            f"{url_fulfillment}/invoiced", json=data, headers=BAGY_HEADERS_API
        )
        concur.close()
        return data
    else:
        qr = f"select PEDS_COD from TCOM_PEDSAI B where B.PEDS_EXT_COD = 'D{order_code}';"
        concur.execute(qr)
        row = concur.fetchone()
        concur.close()
        con.close()
        if row is None:
            resp = requests.delete(url_fulfillment, headers=BAGY_HEADERS_API)
            if resp.status_code == 200:
                return f"Pedido {order_code} cadastrado no Signus. Cancelado atendimento na Bagy!"
            else:
                return f"Falha ao atualizardados do pedido {order_code} - {resp.status_code}!"
        else:
            return f"Pedido {order_code} não faturado até o momento!"


def process_order_nfe(order):
    try:
        result = get_nota(order)
        print(f"Situação: {result}")
    except Exception as e:
        print(f"Erro no processamento do pedido {order['code']}: {e}")


def get_nfe_process():
    url_get_orders = (
        f"{BAGY_ORDERS_API_BASE_URL}/?payment_status=approved"
        "&fulfillment_status=attended,production&sort=-id&limit=100"
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
        executor.map(process_order_nfe, orders)


if __name__ == "__main__":
    get_nfe_process()
