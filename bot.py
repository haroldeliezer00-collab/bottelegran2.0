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

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Credenciales y Canal
TOKEN = '8698848083:AAGa5S9cBp_E8UYSMskNDiC76P3qLY12HJA'
CANAL = '@pruebajsj'

URL_LOTERIA = 'https://lotery.winbigvzla.com/resultados'

app = Flask('')

# Memoria para evitar repetir resultados ya enviados
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
    return "¡El bot de AGENCIA HAROLD JOSE está activo y pasando resultados individuales con normalidad!"

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
    global resultados_enviados, primera_ejecucion
    resultados_enviados.clear()
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

def verificar_resultados():
    global resultados_enviados, primera_ejecucion
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

                match_res = re.search(r'(\d{1,2}\s-\s[A-ZÁÉÍÓÚÑa-zñáéíóú]+(?:\s+[A-ZÁÉÍÓÚÑa-zñáéíóú]+)?)', texto_slot)
                if not match_res:
                    continue

                resultado_bruto = limpiar_texto(match_res.group(1)).upper()
                resultado_limpio = formatear_resultado(resultado_bruto)

                clave_resultado = f"{nombre_loteria}_{hora_completa}_{resultado_limpio}"

                if primera_ejecucion:
                    resultados_enviados.add(clave_resultado)
                    continue

                if clave_resultado not in resultados_enviados:
                    resultados_enviados.add(clave_resultado)
                    
                    mensaje = (
                        "╔═══════ ⋆★⋆ ═══════╗\n"
                        "   ★𝙰𝙶𝙴𝙽𝙲𝙸𝙰 𝙷𝙰𝚁𝙾𝙻𝙳 𝙹𝙾𝚂𝙴★\n"
                        "  ╚═══════ ⋆★⋆ ═══════╝\n"
                        f"📰 *{nombre_loteria}*\n"
                        f"⏰ Hora: {hora_completa}\n"
                        f"🎯 Resultado: {resultado_limpio}\n"
                        "📲 WHATSAPP: 04124489363"
                    )
                    enviar_telegram(mensaje)

        if primera_ejecucion:
            primera_ejecucion = False
            print("🚀 Sincronización inicial completa. Resultados actuales guardados.")

    except Exception as e:
        print(f"⚠️ Error general: {e}")

def loop_bot():
    verificar_resultados()
    schedule.every().day.at("00:00").do(limpiar_memoria_diaria)
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
