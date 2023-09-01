import os
from bs4 import BeautifulSoup as bs
from conections import get_sqlite_conection


# Função para determinar o ID de transporte
def get_transport_id(row_data):
    if row_data[0] in ["ENCOMENDA NORMAL NOVO VAREJO", "ENCOMENDA NORMAL BRONZE"]:
        return 1315
    elif row_data[0] in ["ENCOMENDA NORMAL PAC MINI"]:
        return 20207
    elif row_data[0] in ["SEDEX NOVO VAREJO", "SEDEX SEDEX 2.0"]:
        return 1316
    elif row_data[0] in [
        "CARTA REGISTRADA FATURADO ECT",
        "CARTA REGISTRADA CARTA REGISTRADA",
    ]:
        return 8059
    return None

# Função para processar e inserir postagens no banco de dados
def process_postagens(data, conn):
    cursor_pos = conn.cursor()
    for row in data:
        row_data = row.text.replace("\n", "|").split("|")
        if len(row_data) == 2:
            id_tran = get_transport_id(row_data)
            if id_tran is None:
                continue
        if len(row_data) == 12:
            cd_postal = row_data[8]
            dest = row_data[1]
            dt_postagem = row_data[0] + "/2023"
            cep_dest = row_data[2].replace("-", "")
            uf_dest = row_data[3]
            peso = row_data[5].replace(".", "")
            vr_decl = row_data[10].replace(",", ".")
            vr_postagem = row_data[11].replace(",", ".")
            try:
                cursor_pos.execute(
                    """
                insert into POSTAGENS (COD_POSTAL, DESTINATARIO,
                DT_POSTAGEM, CEP, UF, PESO, VR_DECL, VR_POSTAGEM, ID_TRANSP)
                values(?,?,?,?,?,?,?,?,?)""",
                    (
                        cd_postal,
                        dest,
                        dt_postagem,
                        cep_dest,
                        uf_dest,
                        peso,
                        vr_decl,
                        vr_postagem,
                        id_tran,
                    ),
                )
                conn.commit()
                print(
                    f"Código {cd_postal} referente destinatário {dest} incluso."
                )
            except Exception as e:
                print(e)
                continue


# Função principal
def main():
    path = os.environ["path_htm_files"]
    conn = get_sqlite_conection()
    
    dir = os.listdir(path)
    for file in dir:
        if file.endswith(".HTM"):
            html = open(os.path.join(path, file), "r")
            soup = bs(html, "html.parser")
            data = soup.findAll("tr", {"bgcolor": ["#FFFF66", "#FFFFCC", "#FFCC99"]})
            
            process_postagens(data, conn)
            
            html.close()
            os.remove(os.path.join(path, file))
    
    conn.close()

if __name__ == "__main__":
    main()
