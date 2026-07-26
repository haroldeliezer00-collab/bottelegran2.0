import os
# Forzar la zona horaria de Venezuela para que el bot use la hora local exacta
os.environ['TZ'] = 'America/Caracas'
try:
    import time
    time.tzset()
except AttributeError:
    pass

import requests
from bs4 import BeautifulSoup
import time
import schedule
from threading import Thread
from flask import Flask
import re
import urllib3
from datetime import datetime
import random

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Credenciales actualizadas
TOKEN = '8698848083:AAGa5S9cBp_E8UYSMskNDiC76P3qLY12HJA'
CANAL = '@pruebajsj'

URL_LOTERIA = 'https://lotery.winbigvzla.com/resultados'
URL_BCV = 'https://www.bcv.org.ve/'

app = Flask('')

# Estructura para almacenar los resultados del día organizados por Bloques Horarios
registros_bloques = {}

@app.route('/')
def home():
    return (
        "¡El bot de AGENCIA HAROLD JOSE está activo en el canal @pruebajsj!<br><br>"
        "<b>Pruebas de Bloques de Resultados:</b><br>"
        "👉 <a href='/test/bloque_10'>Probar Envío de Tabla Bloque (Ej. 09:10)</a><br>"
        "👉 <a href='/test/resultados'>Forzar Revisión y Actualización</a>"
    )

@app.route('/test/bloque_10')
def test_bloque_10():
    enviar_tabla_bloque("09:10 AM")
    return "¡Prueba ejecutada! Se envió el bloque de resultados al canal."

@app.route('/test/resultados')
def test_resultados():
    verificar_resultados()
    return "¡Prueba ejecutada! Se forzó la revisión de resultados."

resultados_enviados = set()
primera_ejecucion = True

def limpiar_texto(texto):
    return " ".join(texto.split())

def enviar_telegram(mensaje, disable_web_preview=True):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CANAL, 
        "text": mensaje, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": disable_web_preview
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Error al enviar al canal: {response.text}")
    except Exception as e:
        print(f"⚠️ Excepción de conexión con Telegram: {e}")

def limpiar_memoria_diaria():
    global resultados_enviados, primera_ejecucion, registros_bloques
    resultados_enviados.clear()
    registros_bloques.clear()
    primera_ejecucion = True
    print("🧹 Memoria y registros de bloques limpiados para el nuevo día.")

def enviar_tabla_bloque(hora_corte="09:10 AM"):
    global registros_bloques
    
    mensaje = (
        "╔═══════ ⋆★⋆ ═══════╗\n"
        "   ★𝙰𝙶𝙴𝙽𝙲𝙸𝙰 𝙷𝙰𝚁𝙾𝙻𝙳 𝙹𝙾𝚂𝙴★\n"
        "  ╚═══════ ⋆★⋆ ═══════╝\n"
        "╭⊰ 𝚂𝙴𝙶𝚄𝚁𝙸𝙳𝙰𝙳 𝚈 𝙲𝙾𝙽𝙵𝙸𝙰𝙽𝚉𝙰 ⊱╮\n"
        "    Mas de 6 años brindando\n"
        "        confianza y seguridad\n"
        "    en cada rincón de Venezuela\n"
        "        ʀᴇꜱᴜʟᴛᴀᴅᴏꜱ ᴏꜰᛁᴄɪᴀʟᴇꜱ\n"
        "\"𝙻𝚊 𝚜𝚞𝚎𝚛𝚝𝚎 𝚎𝚜 𝚞𝚗𝚊 𝚏𝚕𝚎𝚌𝚑𝚊🏹𝚕𝚊𝚗𝚣𝚊𝚍𝚊 𝚚𝚞𝚎 𝚑𝚊𝚌𝚎 𝚋𝚕𝚊𝚗𝚌𝚘🎯𝚎𝚗 𝚎𝚕 𝚚𝚞𝚎 𝚖𝚎𝚗𝚘𝚜 𝚕𝚊 𝚎𝚜𝚙𝚎𝚛𝚊🤑\"\n"
        "📲JUEGA AQUI👇👇\n"
        "WHATSAPP: 04124489363\n"
        "📰 RESULTADOS ANIMALITOS 📰\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
    )

    # Bloque 1: GRAJ, L.ACT, SELV
    mensaje += " HORA🎰GRAJ🪙L.ACT🪙SELV\n"
    for h in sorted(registros_bloques.keys()):
        g = registros_bloques[h].get('GRAJ', '....🚫')
        la = registros_bloques[h].get('L.ACT', '....🚫')
        s = registros_bloques[h].get('SELV', '....🚫')
        mensaje += f"⏰{h}  {g:<6} {la:<6} {s}\n"

    mensaje += "\n HORA🎰G.ARO🪙CHAIM🪙MONJE\n"
    for h in sorted(registros_bloques.keys()):
        ga = registros_bloques[h].get('G.ARO', '....🚫')
        ch = registros_bloques[h].get('CHAIM', '....🚫')
        mo = registros_bloques[h].get('MONJE', '....🚫')
        mensaje += f"⏰{h}  {ga:<6} {ch:<6} {mo}\n"

    mensaje += "\n HORA🎰L.ANIM🪙L.PANT🪙L.REAL\n"
    for h in sorted(registros_bloques.keys()):
        lan = registros_bloques[h].get('L.ANIM', '....🚫')
        lpa = registros_bloques[h].get('L.PANT', '....🚫')
        lre = registros_bloques[h].get('L.REAL', '....🚫')
        mensaje += f"⏰{h}  {lan:<6} {lpa:<6} {lre}\n"

    mensaje += (
        "\nMUCHA SUERTE EN SUS JUGADAS 🍀💰"
    )
    
    enviar_telegram(mensaje, disable_web_preview=True)
    print(f"📊 Tabla de bloque ({hora_corte}) enviada correctamente.")

def verificar_resultados():
    global resultados_enviados, primera_ejecucion, registros_bloques
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
        respuesta = requests.get(URL_LOTERIA, headers=headers, timeout=15)
        if respuesta.status_code != 200:
            return

        soup = BeautifulSoup(respuesta.text, 'html.parser')
        tarjetas = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'card|box|item|lotto|result', re.IGNORECASE))

        for tarjeta in tarjetas:
            nombre_loteria = ""
            posibles_titulos = tarjeta.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'span', 'div', 'strong', 'b'], class_=re.compile(r'title|header|name|lotto|text', re.IGNORECASE))
            for pt in posibles_titulos:
                t_text = pt.get_text(" ", strip=True).upper()
                if t_text and len(t_text) > 2 and not re.search(r'\d{1,2}:\d{2}', t_text) and "PENDIENTE" not in t_text:
                    if t_text not in ["WINBIG", "RESULTADOS"]:
                        nombre_loteria = t_text
                        break

            if not nombre_loteria:
                lineas = [l.strip().upper() for l in tarjeta.get_text("\n", strip=True).split("\n") if l.strip()]
                for linea in lineas:
                    if len(linea) > 2 and not re.search(r'\d{1,2}:\d{2}', linea) and "PENDIENTE" not in linea and "-" not in linea:
                        nombre_loteria = linea
                        break

            if not nombre_loteria or len(nombre_loteria) > 40:
                continue

            nombre_loteria = limpiar_texto(nombre_loteria)

            slots_sorteo = tarjeta.find_all(['div', 'li', 'span', 'tr'], class_=re.compile(r'item|slot|draw|row|col', re.IGNORECASE))
            if not slots_sorteo:
                slots_sorteo = [tarjeta]

            for slot in slots_sorteo:
                texto_slot = slot.get_text(" ", strip=True).upper()
                if "PENDIENTE" in texto_slot:
                    continue

                match_h = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM))', texto_slot)
                if not match_h:
                    continue
                hora_completa = match_h.group(1).upper()
                hora_corta = hora_completa[:5]

                match_res = re.search(r'(\d{1,2}\s-\s[A-ZÁÉÍÓÚÑa-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚÑa-zñáéíóú]+)?)', texto_slot)
                if not match_res:
                    continue

                resultado_bruto = limpiar_texto(match_res.group(1)).upper()
                
                abr_lot = "L.ACT"
                if "GRAJ" in nombre_loteria or "GRANJITA" in nombre_loteria:
                    abr_lot = "GRAJ"
                elif "SELVA" in nombre_loteria:
                    abr_lot = "SELV"
                elif "GUACHARO" in nombre_loteria:
                    abr_lot = "G.ARO"
                elif "CHAIMA" in nombre_loteria:
                    abr_lot = "CHAIM"
                elif "MONJE" in nombre_loteria:
                    abr_lot = "MONJE"

                if hora_corta not in registros_bloques:
                    registros_bloques[hora_corta] = {}
                registros_bloques[hora_corta][abr_lot] = resultado_bruto

                clave = (nombre_loteria, hora_completa, resultado_bruto)
                if primera_ejecucion:
                    resultados_enviados.add(clave)
                else:
                    if clave not in resultados_enviados:
                        resultados_enviados.add(clave)

        if primera_ejecucion:
            primera_ejecucion = False
            print(f"🚀 Sincronización inicial de bloques lista. Total registros: {len(resultados_enviados)}")
            return

    except Exception as e:
        print(f"⚠️ Error general en revisión de bloques: {e}")

def loop_bot():
    verificar_resultados()

    schedule.every().day.at("00:00").do(limpiar_memoria_diaria)
    
    schedule.every().day.at("08:10").do(lambda: enviar_tabla_bloque("08:10 AM"))
    schedule.every().day.at("09:10").do(lambda: enviar_tabla_bloque("09:10 AM"))
    schedule.every().day.at("10:10").do(lambda: enviar_tabla_bloque("10:10 AM"))
    schedule.every().day.at("11:10").do(lambda: enviar_tabla_bloque("11:10 AM"))
    schedule.every().day.at("12:10").do(lambda: enviar_tabla_bloque("12:10 PM"))
    schedule.every().day.at("13:10").do(lambda: enviar_tabla_bloque("01:10 PM"))
    schedule.every().day.at("14:10").do(lambda: enviar_tabla_bloque("02:10 PM"))
    schedule.every().day.at("15:10").do(lambda: enviar_tabla_bloque("03:10 PM"))
    schedule.every().day.at("16:10").do(lambda: enviar_tabla_bloque("04:10 PM"))
    schedule.every().day.at("17:10").do(lambda: enviar_tabla_bloque("05:10 PM"))
    schedule.every().day.at("18:10").do(lambda: enviar_tabla_bloque("06:10 PM"))
    schedule.every().day.at("19:10").do(lambda: enviar_tabla_bloque("07:10 PM"))
    schedule.every().day.at("20:10").do(lambda: enviar_tabla_bloque("08:10 PM"))
    schedule.every().day.at("21:10").do(lambda: enviar_tabla_bloque("09:10 PM"))

    schedule.every(1).minute.do(verificar_resultados)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    t = Thread(target=loop_bot)
    t.daemon = True
    t.start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
