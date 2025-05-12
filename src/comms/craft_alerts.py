import os


def craft(required_alerts, log, monitor):
    # erase all alert text files from previous times
    for existing in os.listdir(os.path.join(os.curdir, "templates")):
        if "wapp" in existing:
            os.remove(os.path.join(os.curdir, "templates", existing))

    # loop all members in alert list, compose message
    for k, alert_data in enumerate(required_alerts):
        content = compose_text(alert_data)
        # write in outbound folder
        with open(
            os.path.join(os.curdir, "outbound", f"wapp{k:03d}.txt"),
            "w",
            encoding="utf-8",
        ) as file:
            file.write(content)

    monitor.add_item(f"Total New Alerts: {len(required_alerts)}", type=1)


def compose_text(alert_data):
    # same header for all alerts
    _base_msg = "El Sistema de Alertas Perú te informa:\n"

    # add all corresponding alerts to message text
    match alert_data[5]:
        case "BREVETE":
            msg = f"{_base_msg}{alert_data[1]}, tu Licencia de Conducir vence el {date_friendly(alert_data[4])}.\n"
        case "SOAT":
            msg = f"{_base_msg}{alert_data[1]}, tu Certificado SOAT de placa *{alert_data[3]}* vence el *{date_friendly(alert_data[4])}*.\n"
        case "SATIMP":
            msg = f"{_base_msg}{alert_data[1]}, tu Impuesto Vehicular SAT vence el {date_friendly(alert_data[4])}.\n"
        case "REVTEC":
            msg = f"{_base_msg}{alert_data[1]}, tu Revision Técnica de placa *{alert_data[3]}* vence el *{date_friendly(alert_data[4])}*.\n"

    return msg


def date_friendly(fecha):
    # change date format to a more legible one
    _months = (
        "Ene",
        "Feb",
        "Mar",
        "Abr",
        "May",
        "Jun",
        "Jul",
        "Ago",
        "Set",
        "Oct",
        "Nov",
        "Dic",
    )
    _day = fecha[8:]
    _month = _months[int(fecha[5:7]) - 1]
    _year = fecha[:4]

    return f"{_day}-{_month}-{_year}"
