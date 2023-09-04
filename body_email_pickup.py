import locale


def order_itens(itens):
    ite_pedido = ""
    for item in itens:
        ite_qtd = item["quantity"]
        ite_url = item["url"]
        ite_name = item["name"]
        ite_vr = locale.currency(float(item["price"]), grouping=True, symbol=True)
        ite_pedido = (
            ite_pedido
            + f"""
        <tr>
        <td>
        <table class="row">
        <tr class="list__row">
        <td valign="top" class="list__cell list__cell--quantity" width="1">
        <b>{ite_qtd}x</b>
        </td>
        <td valign="top" class="list__cell">
        <a href="{ite_url}" style="color: #697476;">
            {ite_name}
        </a>"""
        )
        if item["components"] != []:
            ite_pedido += """<p class="list__components">"""
            for component in item["components"]:
                compo_qtd = component["quantity"]
                compo_name = component["name"]
                ite_pedido = (
                    ite_pedido
                    + f"""
                <span class="list__component">
                <strong>{compo_qtd}x</strong>
                {compo_name}
                </span>"""
                )
            ite_pedido += """</p>"""
        ite_pedido = (
            ite_pedido
            + f"""
        </td>
        <td align="top" width="1" class="list__cell list__cell--price">
        {ite_vr}
        </td>
        </tr>
        </table>
        </td>
        </tr>"""
        )
    return ite_pedido


def body_email(
    pedido,
    data_pedido,
    nome,
    evento_descricao,
    evento_detalhe,
    end_retira,
    itens,
    valor_subtotal,
    valor_discount,
    valor_shipping_price,
    valor_tax,
    valor_ped,
    instore,
    endereco,
    add_msg,
    prazo_entrega,
    nome_transp,
    ped_token,
):
    email_html_head = """
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
    <html lang="pt-br">
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <meta name="viewport" content="width=device-width, user-scalable=no">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta content="telephone=no" name="format-detection">
    <style>body, h4 {font-size: 14px}body{background: #f6f7f9;color: #697476;padding: 10px;line-height: 1.3}body, input, select, td, textarea {font-family: -apple-system, BlinkMacSystemFont, San Francisco, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif}table{border-spacing: 0;border-collapse: collapse}strong {font-weight: 600}center {max-width: 600px;margin: 0 auto}center.white {background: #fff;padding-bottom: 30px}hr {border: 0;height: 2px;background: #f5f7f7;margin: 30px 0}hr.spacer {background: 0 0;margin: 10px 0}h4 {margin-top: 0;margin-bottom: 8px}body, p {margin: 0}.header {border-top: solid 5px #697476;border-bottom: solid 2px #f5f7f7;margin-bottom: 25px;width: 100%}.header__block {padding-top: 20px;padding-bottom: 20px}.header__order {font-size: 16px;font-weight: 700;margin-bottom: 5px}.header__cell--logo {text-align: center}.header__cell--info {text-align: right;padding-left: 10px}.footer {padding: 20px 0}.footer__link {font-weight: 600;text-decoration: none;color: inherit}.footer__text {font-size: 10px;margin-top: 10px;padding: 0 2%}.container {width: 90%;margin: 0 auto}.row {width: 100%}.section {border-top: solid 2px #f5f7f7}.d-block {display: block}.shop-name__image img {max-height: 70px;max-width: 220px}.shop-name__text {Text-decoration: none;color: inherit}.text--center {text-align: center}.text--primary, .text--success {color: #34d2a1}.text--warning {color: #ffb400}.text--danger {color: #ff8162}.text--nowrap {white-space: nowrap}.subtotal td, .text--sm {font-size: 13px}.text--lg {font-size: 16px}.title {font-weight: 700;font-size: 18px;margin: 15px 0 5px}.subtitle {font-weight: 600;font-size: 16px;margin: 5px 0 20px}.buttons {margin-top: 25px;display: block}.btn {font-size: 14px;font-weight: 500;color: #fff;text-align: center;padding: 15px 35px;border-radius: 4px;display: inline-block;text-decoration: none !important;background: #34d2a1;border: 0}.btn--outline {font-weight: 400;line-height: 1;letter-spacing: -.3px;background: 0 0;border: solid 2px #697476;color: #697476;padding: 14px 20px;margin: 0 7px}.btn--default {background: #697476}.btn--warning {background: #ffb400}.btn--sm {padding: 12px 20px}.subtotal {width: 100%;max-width: 320px;margin-top: 20px;margin-bottom: 20px}.subtotal td {padding: 5px 0}.subtotal tbody tr:last-child td {padding-bottom: 10px}.subtotal tfoot td {padding-top: 10px;border-top: solid 2px #f5f7f7}.subtotal__text--total {font-size: 16px}.subtotal__value {text-align: right}.subtotal__value--total {font-size: 16px}.list__cell {vertical-align: top;border-bottom: solid 1px #f5f7f7;padding: 8px 0}.list__cell__middle {vertical-align: middle;border-bottom: solid 1px #f5f7f7}.list__cell--price {white-space: nowrap;padding-left: 10px;font-weight: 600}.list__cell--quantity {padding-right: 5px}.list__description {margin-top: 5px;font-size: 12px}.list__components {margin-top: 5px;margin-bottom: 6px}.list__component {display: block;font-size: 12px;margin-bottom: 2px}.order-tracking {background: #f5f7f7;width: 100%;text-align: center;padding: 30px;border-radius: 6px}.order-tracking__title {font-size: 16px;font-weight: 700}.order-tracking__code {font-weight: 400;font-size: 22px;margin: 8px}.order-address {font-size: 0}.order-address__block {display: inline-block;max-width: 47%;min-width: 47%;vertical-align: top;font-size: 14px;margin-bottom: 15px;padding-right: 3%}.coupon__info {width: 100%;background-color: #697476;border-radius: 4px;padding: 30px 10px;text-align: center}.coupon__text {color: #fff}.coupon__code {margin: 15px 0 0;color: #fff;font-size: 38px;border-bottom: dashed 1px #969ea0;display: inline-block}.coupon__terms {padding: 10px;display: inline-block}.howto__item {display: inline-block;width: 100%;max-width: 32%;min-width: 170px;vertical-align: top;margin-top: 30px;margin-bottom: 20px}.howto__item img {display: block;margin-bottom: 10px;max-width: 90px}</style>
    </head>"""

    emailHTMLBody = (f"""{email_html_head}
    <body>
    <center class="white">
    <table class="header">
    <tr>
    <td class="header__block">
    <table class="container">
    <tr>
    <td width="50%" class="header__cell header__cell--logo">
    <a href="https://www.classicline.com.br/" class="shop-name__image">
    <img src="https://cdn.dooca.store/320/files/logo-1.png?v=1595597687" alt="Logo Classicline" title="Classicline">
    </a>
    </td>
    <td class="header__cell header__cell--info">
    <p class="header__order">Pedido # {pedido}</p>
    <small>Realizado em {data_pedido}</small>
    </td>
    </tr>
    </table>
    </td>
    </tr>
    </table>
    <table class="container">
    <tr>
    <td>
    <h2 class="title">
    Oi {nome}!
    </h2>
    <p class="subtitle text--warning">
    Seu pedido está aguardando retirada!
    </p>
    <p>
    Seu pedido está aguardando <strong>retirada!</strong>
    <br>Segue abaixo informações para que você possa retirar seu pedido.
    </p><br>
    <div class="text">
    {evento_descricao}
    <br>
    {evento_detalhe}
    </div>
    <hr>
    <div class="mt-3" style="margin: 4px">
    <strong>
    {end_retira}
    </span></strong>
    </div>
    <hr class="spacer">
    <strong>Atenção:</strong> Caso você já tenha retirado seu pedido, por favor desconsidere este e-mail.
    </div>
    </td>
    </tr>
    </table>
    <hr>
    <table class="container">
    <tr>
    <td>
    <h3>
    Resumo do seu pedido
    </h3>
    </td>
    </tr>
    </table>
    <table class="container">
    {order_itens(itens)}
    </table>
    <table class="container">
    <tr>
    <td align="center" valign="top">
    <table class="row subtotal" align="right">
    <tbody>
    <tr>
    <td class="subtotal__text">Subtotal</td>
    <td class="subtotal__value">{valor_subtotal}</td>
    </tr>
    <tr>
    <td class="subtotal__text">Descontos</td>
    <td class="subtotal__value">{valor_discount}</td>
    </tr>
    <tr>
    <td class="subtotal__text">Frete</td>
    <td class="subtotal__value">{valor_shipping_price}</td>
    </tr>
    <tr>
    <td class="subtotal__text">Taxas Adicionais</td>
    <td class="subtotal__value">{valor_tax}</td>
    </tr>
    </tbody>
    <tfoot>
    <tr>
    <td class="subtotal__text subtotal__text--total">
    <strong>TOTAL</strong>
    </td>
    <td class="subtotal__value subtotal__value--total">
    <strong>{valor_ped}</strong><br>
    </td>
    </tr>
    </tfoot>
    </table>
    </td>
    </tr>
    </table>
    <hr>
    <table class="container order-address">
    <tr>
    <td align="left">
    <div class="order-address__block">
    <table>
    <tr>
    <td>"""
    )
    if "instore" == instore:
        emailHTMLBody += """
    <h4>
    Endereço de retirada
    </h4>
    <p>
    Av. Santos Dumont, 266
    <br>Centro
    <br>Fortaleza - CE
    <br>CEP 60.150160
    </p>"""
    else:
        emailHTMLBody += f"""
    <h4>
    Endereço de entrega
    </h4>
    <p>
    { endereco['street'] }, { endereco['number'] }
    { (' - '+endereco['detail'] if endereco['detail'] != None else '') }
    <br>{ endereco['district'] }
    <br>{ endereco['city'] } - { endereco['state'] }
    <br>CEP { endereco['zipcode'] }
    </p>"""
        if add_msg is not None:
            emailHTMLBody += f"""
            <small>*{ add_msg }</small>"""
    emailHTMLBody += """
    </td>
    </tr>
    </table>
    </div>
    <div class="order-address__block">
    <table>
    <tr>
    <td>
    <h4>"""

    if "instore" == instore:
        emailHTMLBody += " Disponível "
    else:
        emailHTMLBody += " Entrega "
    emailHTMLBody += f"""
    em até { prazo_entrega } dias úteis
    </h4>
    <p>{ nome_transp }</p>
    <small>
    *será considerado somente após a confirmação do pagamento.
    </small>
    </td>
    </tr>
    </table>
    </div>
    </td>
    </tr>
    </table>
    <hr>
    <table class="container">
    <tr>
    <td align="center">
    <a href="https://www.classicline.com.br/conta/pedido/{ ped_token }" class="btn btn--outline"
    style="min-width: 200px; margin-bottom:5px">acompanhar pedido online</a>
    </td>
    </tr>
    </table>
    </center>
    <center class="footer">
    <a href="https://www.classicline.com.br/" class="footer__link">
    www.classicline.com.br
    </a>
    <p class="footer__text">

    </p>
    </center>
    </body>
    </html>"""

    return emailHTMLBody
