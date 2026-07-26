import os
import time
from datetime import datetime
from flask import Flask, render_template_string
import telebot
import schedule
import threading

# Configuración de Tokens y Canales (reemplaza con tus datos reales si es necesario)
TOKEN = os.environ.get("TELEGRAM_TOKEN", "TU_TOKEN_DE_BOT")
CANAL_PUBLICO = "@pruebajsj"  # Tu canal público donde llega la gente

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Variables de estado diario
taquilla_activa_hoy = False
imagen_activa_id = None
ultimo_dia_activo = None

TEXTO_TAQUILLA = (
    "✅ AG HAROLD JOSÉ ACTIVA ✅\n"
    "Ya estamos operativos brindando la mejor atención. Calidad, respaldo y rapidez en cada una de todas tus solicitudes.\n\n"
    "📲 Envía tus jugadas:\n"
    "(Comprobante de pago / Lotería / monto / Hora)\n\n"
    "📖 Consulta nuestro reglamento aquí:\n"
    "https://wa.me/p/33319103291071105/584124489363\n"
    "🚀 Agiliza tu proceso aquí: https://wa.me/p/24724650613899486/584124489363\n\n"
    "RESULTADOS AUTOMÁTICOS\n"
    "https://t.me/resultadosagharoldjose\n\n"
    "¡Mucho éxito en la jornada de hoy! 🍀✨"
)

# 1. Detector de mensajes en el canal privado
@bot.channel_post_handler(content_types=['photo'])
def detectar_taquilla_privada(message):
    global taquilla_activa_hoy, imagen_activa_id, ultimo_dia_activo
    
    hoy = datetime.now().date()
    
    # Validar si es domingo (weekday 6)
    if hoy.weekday() == 6:
        print("Domingo detectado: Ignorando activación automática de taquilla.")
        return

    # Verificar si el mensaje tiene texto o caption con la frase clave
    caption = message.caption if message.caption else ""
    if "taquilla activa" in caption.lower():
        # Guardar la imagen y activar el estado de hoy
        imagen_activa_id = message.photo[-1].file_id
        taquilla_activa_hoy = True
        ultimo_dia_activo = hoy
        
        print(f"¡Taquilla activada manualmente en el canal privado a las {datetime.now().strftime('%H:%M:%S')}!")
        
        # Enviar inmediatamente al canal público
        try:
            bot.send_photo(
                chat_id=CANAL_PUBLICO,
                photo=imagen_activa_id,
                caption=TEXTO_TAQUILLA
            )
            print("Mensaje de taquilla activa enviado al canal público con éxito.")
        except Exception as e:
            print(f"Error al enviar la taquilla al canal público: {e}")

# 2. Función para el envío automático de las 3:30 p.m.
def tarea_refuerzo_tarde():
    global taquilla_activa_hoy, imagen_activa_id
    hoy = datetime.now().date()
    
    # Los domingos no aplica
    if hoy.weekday() == 6:
        return

    # Si la taquilla fue activada hoy por la mañana, reforzar a las 3:30 p.m.
    if taquilla_activa_hoy and imagen_activa_id:
        print(f"Ejecutando refuerzo de taquilla de las 3:30 p.m.")
        try:
            bot.send_photo(
                chat_id=CANAL_PUBLICO,
                photo=imagen_activa_id,
                caption=TEXTO_TAQUILLA + "\n\n🔄 *¡Seguimos activos con la jornada de la tarde!*",
                parse_mode="Markdown"
            )
            print("Refuerzo de las 3:30 p.m. enviado correctamente.")
        except Exception as e:
            print(f"Error al enviar refuerzo de tarde: {e}")
    else:
        print("A las 3:30 p.m. la taquilla no había sido abierta hoy, se omite el refuerzo.")

# Configurar horario del refuerzo diario a las 15:30 (3:30 p.m.)
schedule.every().day.at("15:30").do(tarea_refuerzo_tarde)

def ejecutar_programador():
    while True:
        schedule.run_pending()
        time.sleep(30)

# 3. Ruta Web para estado y pruebas manuales
@app.route("/")
def home():
    estado_texto = "ACTIVA" if taquilla_activa_hoy else "INACTIVA"
    return render_template_string(f"""
    <html>
        <head><title>Panel Agente Harold José</title></head>
        <body style="font-family: Arial; text-align: center; margin-top: 50px;">
            <h2>Centro de Control - Bot Telegram</h2>
            <p>Estado de la Taquilla Hoy: <b style="color: {'green' if taquilla_activa_hoy else 'red'};">{estado_texto}</b></p>
            <p>El bot está escuchando tu canal privado y programado para las 3:30 p.m.</p>
        </body>
    </html>
    """)

@app.route("/test-refuerzo")
def test_refuerzo():
    tarea_refuerzo_tarde()
    return "Prueba de refuerzo ejecutada manualmente."

if __name__ == "__main__":
    # Iniciar el planificador en segundo plano
    hilo_scheduler = threading.Thread(target=ejecutar_programador, daemon=True)
    hilo_scheduler.start()
    
    # Iniciar bot en modo polling para escuchar el canal privado
    hilo_bot = threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True)
    hilo_bot.start()
    
    # Iniciar servidor web Flask
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
