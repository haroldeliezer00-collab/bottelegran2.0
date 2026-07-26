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

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Credenciales y Canal
TOKEN = '8698848083:AAGa5S9cBp_E8UYSMskNDiC76P3qLY12HJA'
CANAL = '@pruebajsj'

URL_LOTERIA = 'https://lotery.winbigvzla.com/resultados'

app = Flask('')

# Almacén de resultados del día por horas en punto exactas (ej. "08:00", "09:00")
registros_bloques = {}
resultados_enviados = set()
primera_ejecucion = True

# Diccionario de conversión de nombre de animal a emoji oficial
MAPEO_ANIMALES = {
    "BALLENA": "🐋", "DELFIN": "🐋", "CARNERO": "🐏", "TORO": "🐂", 
    "CIEMPIES": "🐛", "GUSANO": "🐛", "ALACRAN": "🦂", "LEON": "🦁", 
    "RANA": "🐸", "PERICO": "🦜", "RATON": "🐁", "AGUILA": "🦅", 
    "TIGRE": "🐯", "GATO": "😺", "CABALLO": "🐎", "MONO": "🐵", 
    "PALOMA": "🕊️", "ZORRO": "🦊", "OSO": "🐻", "PAVO": "🦃", 
    "BURRO": "🫏", "CHIVO": "🐐", "COCHINO": "🐷", "CERDO": "🐷", "PUERCO": "🐷", 
    "GALLO": "🐓", "CAMELLO": "🐫", "CEBRA": "🦓", "IGUANA": "🦎", 
    "GALLINA": "🐔", "VACA": "🐮", "PERRO": "🐶", "ZAMURO": "🦇", "MURCIELAGO": "🦇", 
    "ELEFANTE": "🐘", "CAIMAN": "🐊", "LAGARTO": "🐊", "COCODRILO": "🐊", 
    "JABALI": "🐗", "PUERCOESPIN": "🐗", "ARDILLA": "🐿️", "PESCADO": "🐠", 
    "VENADO": "🦌", "JIRAFA": "🦒", "CULEBRA": "🐍", "SERPIENTE": "🐍",
    "BUFALO": "🐃", "ABEJA": "🐝", "CANGURO": "🦘", "PEREZOSO": "🦥", 
    "CARACOL": "🐌", "PATO": "🦆", "HORMIGA": "🐜", "PANDA": "🐼", 
    "AVESTRUZ": "🦤", "BISONTE": "🦬", "GORILA": "🦍", "HIPOPOTAMO": "🦛", "GRILLO": "🦗"
}

@app.route('/')
def home():
    return (
        "¡El bot de AGENCIA HAROLD JOSE está activo!<br><br>"
        "👉 <a href='/test/bloque'>Probar Envío de Tabla</a><br>"
        "👉 <a href='/test/resultados'>Forzar Revisión de Resultados</a>"
    )

@app.route('/test/bloque')
def test_bloque():
    enviar_tabla_bloque("09:10 AM")
    return "¡Prueba ejecutada!"

@app.route('/test/resultados')
def test_resultados():
    verificar_resultados()
    return "¡Prueba ejecutada!"

def limpiar_texto(texto):
    return " ".join(texto.split())

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CANAL, 
        "text": mensaje, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Error al enviar al canal: {response.text}")
    except Exception as e:
        print(f"⚠️ Excepción de conexión: {e}")

def limpiar_memoria_diaria():
    global resultados_enviados, primera_ejecucion, registros_bloques
    resultados_enviados.clear()
    registros_bloques.clear()
    primera_ejecucion = True
    print("🧹 Memoria limpiada para el nuevo día.")

def formatear_resultado(texto_bruto):
    match = re.search(r'(\d+)\s*-\s*([A-ZÁÉÍÓÚÑa-zñáéíóú\s]+)', texto_bruto)
    if match:
        num = match.group(1).strip()
        nombre = match.group(2).strip().upper()
        emoji = "🎲"
        for key, emj in MAPEO_ANIMALES.items():
            if key in nombre:
                emoji = emj
                break
        return f"{num}{emoji}"
    return texto_bruto

def enviar_tabla_bloque(hora_corte="09:10 AM"):
    global registros_bloques
    
    mensaje = (
        "╔═══════ ⋆★⋆ ═══════╗\n"
        "   ★𝙰𝙶𝙴𝙽𝙲𝙸𝙰 𝙷𝙰𝚁𝙾𝙻𝙳 𝙹𝙾𝚂𝙴★\n"
        "  ╚═══════ ⋆★⋆ ═══════╝\n"
        "╭⊰ 𝚂𝙴𝙶𝚄𝚁𝙸𝙳𝙰𝙳 𝚈 𝙲𝙾𝙽𝙵𝙸𝙰𝙽𝚉𝙰 ⊱╮\n"
        "        Mas de 6 años brindando\n"
        "            confianza y seguridad\n"
        "        en cada rincón de Venezuela\n"
        "            ʀᴇꜱᴜʟᴛᴀᴅᴏꜱ ᴏꜰᛁᴄ𝙸ᴀʟᴇꜱ\n"
        "\"𝙻𝚊 𝚜𝚞𝚎𝚛𝚝𝚎 𝚎𝚜 𝚞𝚗𝚊 𝚏𝚕𝚎𝚌𝚑𝚊🏹𝚕𝚊𝚗𝚣𝚊𝚍𝚊 𝚚𝚞𝚎 𝚑𝚊𝚌𝚎 𝚋𝚕𝚊𝚗𝚌𝚘🎯𝚎𝚗 𝚎𝚕 𝚚𝚞𝚎 𝚖𝚎𝚗𝚘𝚜 𝚕𝚊 𝚎𝚜𝚙𝚎𝚛𝚊🤑\"\n"
        "📲JUEGA AQUI👇👇\n"
        "WHATSAPP: 04124489363\n"
        "📰RESULTADOS ANIMALITOS📰\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
    )

    horas_registradas = sorted(list(registros_bloques.keys()))
    if not horas_registradas:
        horas_registradas = ["08:00"]

    # 1. GRAJ, L.ACT, SELV
    mensaje += " HORA🎰GRAJ🪙L.ACT🪙SELV\n"
    for h in horas_registradas:
        g = registros_bloques[h].get('GRAJ', '....🚫')
        la = registros_bloques[h].get('L.ACT', '....🚫')
        s = registros_bloques[h].get('SELV', '....🚫')
        mensaje += f"⏰{h}  {g:<6} {la:<6} {s}\n"

    # 2. G.ARO, CHAIM, MONJE
    mensaje += "\n HORA🎰G.ARO🪙CHAIM🪙MONJE\n"
    for h in horas_registradas:
        ga = registros_bloques[h].get('G.ARO', '....🚫')
        ch = registros_bloques[h].get('CHAIM', '....🚫')
        mo = registros_bloques[h].get('MONJE', '....🚫')
        mensaje += f"⏰{h}  {ga:<6} {ch:<6} {mo}\n"

    # 3. L.ANIM, L.PANT, L.REAL
    mensaje += "\n HORA🎰L.ANIM🪙L.PANT🪙L.REAL\n"
    for h in horas_registradas:
        lan = registros_bloques[h].get('L.ANIM', '....🚫')
        lpa = registros_bloques[h].get('L.PANT', '....🚫')
        lre = registros_bloques[h].get('L.REAL', '....🚫')
        mensaje += f"⏰{h}  {lan:<6} {lpa:<6} {lre}\n"

    # 4. L.RD, CEN.A, MEGA
    mensaje += "\n HORA🎰L.RD🪙CEN.A🪙MEGA\n"
    for h in horas_registradas:
        lrd = registros_bloques[h].get('L.RD', '....🚫')
        cena = registros_bloques[h].get('CEN.A', '....🚫')
        mega = registros_bloques[h].get('MEGA', '....🚫')
        mensaje += f"⏰{h}  {lrd:<6} {cena:<6} {mega}\n"

    # 5. R.PER, R.COL, R.VEN
    mensaje += "\n HORA🎰R.PER🪙R.COL🪙R.VEN\n"
    for h in horas_registradas:
        rper = registros_bloques[h].get('R.PER', '....🚫')
        rcol = registros_bloques[h].get('R.COL', '....🚫')
        rven = registros_bloques[h].get('R.VEN', '....🚫')
        mensaje += f"⏰{h}  {rper:<6} {rcol:<6} {rven}\n"

    # 6. COND, FRUI, TROP
    mensaje += "\n HORA🎰COND🪙FRUI🪙TROP\n"
    for h in horas_registradas:
        cond = registros_bloques[h].get('COND', '....🚫')
        fru = registros_bloques[h].get('FRUI', '....🚫')
        trop = registros_bloques[h].get('TROP', '....🚫')
        mensaje += f"⏰{h}  {cond:<6} {fru:<6} {trop}\n"

    # 7. G.MIL, ZOOL, L.MAX
    mensaje += "\n HORA🎰G.MIL🪙ZOOL🪙L.MAX\n"
    for h in horas_registradas:
        gmil = registros_bloques[h].get('G.MIL', '....🚫')
        zool = registros_bloques[h].get('ZOOL', '....🚫')
        lmax = registros_bloques[h].get('L.MAX', '....🚫')
        mensaje += f"⏰{h}  {gmil:<6} {zool:<6} {lmax}\n"

    # 8. C.ANI
    mensaje += "\n HORA🎰C.ANI🪙\n"
    for h in horas_registradas:
        cani = registros_bloques[h].get('C.ANI', '....🚫')
        mensaje += f"⏰{h}  {cani}\n"

    mensaje += "\nMUCHA SUERTE EN SUS JUGADAS"
    
    enviar_telegram(mensaje)

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
                
                # FILTRO ESTRICTO: Solo capturar horas en punto exactas (minutos '00')
                if ":00" not in hora_completa:
                    continue

                hora_corta = hora_completa[:5] # Ej: "08:00", "09:00"

                match_res = re.search(r'(\d{1,2}\s-\s[A-ZÁÉÍÓÚÑa-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚÑa-zñáéíóú]+)?)', texto_slot)
                if not match_res:
                    continue

                resultado_bruto = limpiar_texto(match_res.group(1)).upper()
                resultado_limpio = formatear_resultado(resultado_bruto)
                
                # Mapeo de loterías
                abr_lot = ""
                nl = nombre_loteria.upper()
                if "GRANJITA" in nl: abr_lot = "GRAJ"
                elif "ACTIVA" in nl: abr_lot = "L.ACT"
                elif "SELVA" in nl: abr_lot = "SELV"
                elif "GUACHARO" in nl: abr_lot = "G.ARO"
                elif "CHAIMA" in nl: abr_lot = "CHAIM"
                elif "MONJE" in nl: abr_lot = "MONJE"
                elif "ANIMALITOS" in nl and "PANTERA" not in nl and "REAL" not in nl and "CHANCE" not in nl and "MEGA" not in nl: abr_lot = "L.ANIM"
                elif "PANTERITA" in nl or "PANTERA" in nl: abr_lot = "L.PANT"
                elif "REAL" in nl: abr_lot = "L.REAL"
                elif "RED" in nl or " R.D" in nl: abr_lot = "L.RD"
                elif "CENTAURO" in nl or "CENTAVOS" in nl: abr_lot = "CEN.A"
                elif "MEGA" in nl: abr_lot = "MEGA"
                elif "PERUANA" in nl or "PERMUTA" in nl: abr_lot = "R.PER"
                elif "COLOMBIA" in nl or "LOCA" in nl: abr_lot = "R.COL"
                elif "VENEZUELA" in nl: abr_lot = "R.VEN"
                elif "CONDE" in nl: abr_lot = "COND"
                elif "FRUTAL" in nl: abr_lot = "FRUI"
                elif "TROPICAL" in nl: abr_lot = "TROP"
                elif "MILLONARIO" in nl: abr_lot = "G.MIL"
                elif "ZODIACO" in nl or "ZOODIACO" in nl: abr_lot = "ZOOL"
                elif "MAX" in nl: abr_lot = "L.MAX"
                elif "CHANCE" in nl: abr_lot = "C.ANI"

                if abr_lot:
                    if hora_corta not in registros_bloques:
                        registros_bloques[hora_corta] = {}
                    registros_bloques[hora_corta][abr_lot] = resultado_limpio

        if primera_ejecucion:
            primera_ejecucion = False
            print("🚀 Sincronización inicial completa.")
            return

    except Exception as e:
        print(f"⚠️ Error general: {e}")

def loop_bot():
    verificar_resultados()

    schedule.every().day.at("00:00").do(limpiar_memoria_diaria)
    
    # Envíos automáticos a los 10 minutos de cada hora (ej. 08:10, 09:10...)
    for hora in ["08:10", "09:10", "10:10", "11:10", "12:10", "13:10", "14:10", "15:10", "16:10", "17:10", "18:10", "19:10", "20:10", "21:10"]:
        h_str, m_str = hora.split(":")
        h_int = int(h_str)
        suf = "AM" if h_int < 12 else "PM"
        h_12 = h_int if h_int <= 12 else h_int - 12
        if h_12 == 0: h_12 = 12
        hora_label = f"{h_12:02d}:{m_str} {suf}"
        schedule.every().day.at(hora).do(lambda hl=hora_label: enviar_tabla_bloque(hl))

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
