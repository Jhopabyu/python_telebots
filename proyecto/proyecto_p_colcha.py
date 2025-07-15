from telegram.ext import ApplicationBuilder, ConversationHandler, MessageHandler, CommandHandler, filters, ContextTypes
from telegram import Update, ReplyKeyboardMarkup
from mailjet_rest import Client
from dotenv import load_dotenv
from datetime import datetime
import os, sqlite3, re, webbrowser
from fpdf.enums import XPos, YPos
from PIL import Image, ImageDraw, ImageFont

# --- Configuración inicial ---
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MAILJET_API_KEY = os.getenv("MAILJET_API_KEY")
MAILJET_API_SECRET = os.getenv("MAILJET_SECRET_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")
MAILJET_FROM_NAME = os.getenv("MAILJET_FROM_NAME")

# --- Constantes para el flujo del bot ---
MENU, MODELO, REPUESTO, DATOS, AUTORIZACION, CONFIRMAR = range(6)

# --- Diccionarios y listas para el bot ---
SERVICIOS = {
    "1. Mazda": ["CX-5", "Mazda 3", "BT-50"],
    "2. Chevrolet": ["Aveo", "Spark", "Tracker"],
    "3. Hyundai": ["Tucson", "Elantra", "Accent"],
    "4. Renault": ["Logan", "Duster", "Sandero"]
}

# --- Diccionarios y listas para el bot ---
PRECIOS = {
    "1. Mazda": {
        "Pastillas de freno": 60,
        "Filtro de aire": 40,
        "Aceite": 30,
        "Amortiguador": 90,
        "Otro": 50
    },
    "2. Chevrolet": {
        "Pastillas de freno": 25,
        "Filtro de aire": 20,
        "Aceite": 15,
        "Amortiguador": 60,
        "Otro": 30
    },
    "3. Hyundai": {
        "Pastillas de freno": 80,
        "Filtro de aire": 50,
        "Aceite": 45,
        "Amortiguador": 100,
        "Otro": 60
    },
    "4. Renault": {
        "Pastillas de freno": 50,
        "Filtro de aire": 35,
        "Aceite": 25,
        "Amortiguador": 70,
        "Otro": 40
    }
}

# --- Conexión a la base de datos ---
conn = sqlite3.connect("telebot.db", check_same_thread=False)
cursor = conn.cursor()
# Crear la tabla si no existe
cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        servicio TEXT,
        modelo TEXT,
        message_id INTEGER,
        timestamp TEXT
    )
""")
conn.commit()

# Metodo para guardar cada interaccion
def guardar_interaccion(update: Update, modelo=""):
    user = update.effective_user
    username = user.username or "Sin username"
    servicio = update.message.text
    message_id = update.message.message_id
    timestamp = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO chat_data (user_id, username, servicio, modelo, message_id, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user.id, username, servicio, modelo, message_id, timestamp))
    conn.commit()
    
# Metodo para extraer el email
def extraer_email(texto):
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', texto)
    return match.group(0) if match else None

"""def limpiar_texto(texto):
    return texto.encode('latin-1', errors='ignore').decode('latin-1')"""


from datetime import datetime
from fpdf.enums import XPos, YPos

# Función para generar el PDF
def generar_pdf(servicio, nombre, correo, repuesto, modelo, precio):
    from fpdf import FPDF
    import os

    pdf = FPDF()
    pdf.add_page()

    font_regular = os.path.join("fonts", "DejaVuSans.ttf")

    if not os.path.isfile(font_regular):
        raise FileNotFoundError(f"No se encontró la fuente TTF en: {font_regular}")

    pdf.add_font("DejaVu", "", font_regular)

    # Título (sin negrita)
    pdf.set_font("DejaVu", "", 14)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, " Confirmación de Pedido", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(10)

    # Datos personales
    pdf.set_font("DejaVu", "", 12)
    pdf.cell(0, 10, f" Nombre: {nombre}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, f" Correo: {correo}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.multi_cell(0, 10, f" Repuesto: {repuesto}")
    pdf.ln(10)

    # Tabla encabezados (usando fuente normal también)
    pdf.set_font("DejaVu", "", 12)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(60, 10, "Marca", 1, align="C", fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(60, 10, "Modelo", 1, align="C", fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(60, 10, "Precio ($)", 1, align="C", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    

    # Tabla datos
    pdf.cell(60, 10, servicio, border=1, align="C", new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(60, 10, modelo, border=1, align="C", new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(60, 10, f"{precio}", border=1, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(10)
    

    # Pie de página
    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(170, 10, "Gracias por confiar en nosotros - Repuestos de Carros", border=0, align="C", new_x=XPos.RIGHT, new_y=YPos.TOP)

    filename = f"pedido_{nombre.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join("archivos", filename)
    os.makedirs("archivos", exist_ok=True)
    pdf.output(filepath)

    return filepath


"""def generar_imagen(servicio, datos, precio):
    os.makedirs("imagenes", exist_ok=True)
    img = Image.new("RGB", (600, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font = ImageFont.truetype(font_path, 16) if os.path.exists(font_path) else ImageFont.load_default()
    draw.text((20, 20), "Confirmación de Pedido", fill=(0, 0, 0), font=font)
    draw.text((20, 60), f"Servicio: {servicio}", fill=(0, 0, 0), font=font)
    draw.text((20, 100), f"Datos: {datos}", fill=(0, 0, 0), font=font)
    draw.text((20, 140), f"Precio: ${precio}", fill=(0, 0, 0), font=font)

    filename = f"imagen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join("imagenes", filename)
    img.save(filepath)
    return filepath"""

def enviar_mailjet(context, destinatario, asunto, contenido):
    mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3.1')
    data = {
        "Messages": [
            {
                "From": {
                    "Email": EMAIL_FROM,
                    "Name": "Repuestos de Carros"
                },
                "To": [
                    {
                        "Email": destinatario,
                        "Name": "Cliente"
                    }
                ],
                "Subject": asunto,
                "HTMLPart": f"""
                    <div style="font-family:Arial, sans-serif; color:#2c3e50;">
                        <h2>🎉 ¡Gracias por tu pedido!</h2>
                        <p>📝 <strong>Datos:</strong> {context.user_data['datos']}</p>
                        <p>✅ <strong>Marca:</strong> {context.user_data['servicio']}</p>
                        <p> 🚗 <strong>Modelo:</strong> {context.user_data['modelo']}</p>
                        <p>🔧 <strong>Repuesto:</strong> {context.user_data['repuesto']}</p>
                        <p>💵 <strong>Precio del Repuesto:</strong> ${PRECIOS[context.user_data['servicio']].get(context.user_data['repuesto'], "N/A")}</p>



                        <img src="https://via.placeholder.com/500x200.png?text=Gracias+por+tu+confianza" 
                            alt="Gracias por tu pedido" 
                            style="width:100%; max-width:500px; margin:20px 0;">

                        <p>Haz clic en el botón para visitar nuestra página:</p>
                        <a href="https://www.semicaloja.com/"
                        style="display:inline-block; padding:12px 24px; background-color:#1abc9c; color:white; text-decoration:none; border-radius:6px; font-weight:bold;">
                        Ir a la página 🚀
                        </a>

                    </div>
                """
            }
        ]
    }
    result = mailjet.send.create(data=data)
    return result.status_code == 200

# Funciones de inicio de conversaciones
async def start(update: Update, context):
    keyboard = [[opcion] for opcion in SERVICIOS.keys()]
    await update.message.reply_text(
        "🚀 Bienvenido al *Bot de Repuestos de Carros*.\nSelecciona una marca:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True),
        parse_mode="Markdown"
    )
    guardar_interaccion(update)
    return MENU
# Funciones para seleccionar un a marca de carro
async def seleccionar_servicio(update: Update, context):
    servicio = update.message.text.strip()
    if servicio in SERVICIOS:
        context.user_data["servicio"] = servicio
        modelos = SERVICIOS[servicio]
        keyboard = [[modelo] for modelo in modelos]
        await update.message.reply_text(
            "Selecciona el modelo:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        guardar_interaccion(update)
        print("DEBUG modelo seleccionado:", servicio) 
        return MODELO
    else:
        await update.message.reply_text("Servicio no válido. Usa el menú.")
        guardar_interaccion(update)
        return MENU
# Funciones para seleccionar un modelo de carro
async def seleccionar_modelo(update: Update, context):
    modelo = update.message.text.strip()
    servicio = context.user_data.get("servicio")

    if not servicio:
        await update.message.reply_text("❌ Marca no encontrada. Por favor, comienza de nuevo con /start.")
        return ConversationHandler.END

    modelos_validos = SERVICIOS.get(servicio, [])
    if modelo not in modelos_validos:
        await update.message.reply_text("❌ Modelo no válido. Selecciona uno del menú.")
        keyboard = [[m] for m in modelos_validos]
        await update.message.reply_text("Selecciona nuevamente el modelo:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))
        return MODELO

    context.user_data["modelo"] = modelo
    guardar_interaccion(update, modelo=modelo)
     # MOSTRAR OPCIONES DE REPUESTO
    repuestos = PRECIOS.get(servicio, {}).keys()
    keyboard = [[r] for r in repuestos]
    await update.message.reply_text(
        "🛠️ Selecciona el repuesto que deseas:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    print("DEBUG modelo seleccionado:", modelo)  
   
    return REPUESTO
# Funciones para seleccionar un repuesto 
async def seleccionar_repuesto(update: Update, context):
    repuesto = update.message.text.strip()
    servicio = context.user_data.get("servicio")
    repuestos_disponibles = PRECIOS.get(servicio, {}).keys()

    if repuesto not in repuestos_disponibles:
        keyboard = [[r] for r in repuestos_disponibles]
        await update.message.reply_text(
            "❗ Repuesto no válido. Selecciona uno del menú:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return REPUESTO

    context.user_data["repuesto"] = repuesto
    await update.message.reply_text(
        "✍️ Ahora escribe *nombre, correo* separados por coma.\n\n📌 Ejemplo:\nJuan Pérez, juan@gmail.com",
        parse_mode="Markdown"
    )
    return DATOS


async def recibir_repuesto(update: Update, context):
    repuesto = update.message.text.strip()
    servicio = context.user_data.get("servicio")

    if repuesto not in PRECIOS.get(servicio, {}):
        await update.message.reply_text("❌ Repuesto no válido. Usa el menú anterior.")
        return REPUESTO

    context.user_data["repuesto"] = repuesto
    await update.message.reply_text(
        "📥 Ahora escribe *nombre y correo* separados por coma.\n\nEjemplo:\nJuan Pérez, juan@gmail.com",
        parse_mode="Markdown"
    )
    return DATOS


# Recolección de datos

async def recibir_datos(update: Update, context):
    texto = update.message.text.strip()
    partes=[p.strip() for p in texto.split(",")]
    email = extraer_email(texto)
    if len(partes) < 2:
        await update.message.reply_text(
            "❗ Por favor escribe *nombre, correo y repuesto* separados por comas.\n\n"
            "📌 Ejemplo:\nJuan Pérez, juan@gmail.com,",
            parse_mode="Markdown"
        )
        return DATOS
    nombre,email = partes[0],partes[1]
    if not email:
        await update.message.reply_text("No se detectó un correo válido. Intenta de nuevo.")
        guardar_interaccion(update)
        return DATOS
    
    context.user_data["nombre"] = nombre
    context.user_data["correo"] = email
    #context.user_data["repuesto"] = repuesto
    context.user_data["datos"] = f"{nombre} | {email}"
    keyboard = [["✅ Sí", "❌ No"]]
    await update.message.reply_text("🔐 ¿Autorizas el uso de tus datos para procesar tu pedido?", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    guardar_interaccion(update)
    return AUTORIZACION
# Funciones de autorización
async def autorizacion(update: Update, context):
    respuesta = update.message.text.lower()
    if "si" in respuesta or "✅" in respuesta:
        servicio = context.user_data["servicio"]
        repuesto = context.user_data["repuesto"]
        precio = PRECIOS.get(servicio, {}).get(repuesto, 0)
        keyboard = [["✅ Confirmar", "❌ Cancelar"]]
        await update.message.reply_text(f"💵 Precio del servicio: ${precio}.\n¿Confirmas el pedido?", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        guardar_interaccion(update)
        return CONFIRMAR
    else:
        await update.message.reply_text("🚫 Pedido cancelado. Usa /start para comenzar de nuevo.")
        return ConversationHandler.END
# Funciones de confirmación
async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guardar_interaccion(update)
    if "confirmar" in update.message.text.lower():
        servicio = context.user_data["servicio"]
        modelo = context.user_data.get("modelo", "Modelo no especificado")
        repuesto = context.user_data["repuesto"]
        datos = context.user_data["datos"]
        correo = extraer_email(datos)
        precio = PRECIOS.get(servicio, {}).get(repuesto, 0)
        mensaje = (
            f"🎉 *Gracias por tu pedido!*\n\n"
            f"🏷️ *Marca Auto:* {servicio}\n"
            f"✅ *Modelo:* {modelo}\n"
            f"🛠️ *Repuesto:* {repuesto}\n"
            f"👤 *Descripción:* {datos}\n"
            f"💲 *Precio:* ${precio}\n\n"
            "Nos pondremos en contacto contigo pronto. 📧"
        )
        print("email", datos, modelo, precio, correo)
        print("mensaje", mensaje)
        nombre = context.user_data.get("nombre", "No especificado")
        correo = context.user_data.get("correo", "No especificado")
        repuesto = context.user_data.get("repuesto", "No especificado")

        pdf_path = generar_pdf(servicio, nombre, correo, repuesto, modelo, precio)

        #img_path = generar_imagen(f"{servicio} - {modelo}", datos, precio)

        enviado = enviar_mailjet(context, correo, "Confirmación de Pedido", mensaje)
        if enviado:
            await update.message.reply_text("📧 Correo enviado correctamente. Gracias por tu pedido.")
            await update.message.reply_document(document=open(pdf_path, "rb"), filename=os.path.basename(pdf_path))
            #await update.message.reply_photo(photo=open(img_path, "rb"), filename=os.path.basename(img_path))
        else:
            await update.message.reply_text("⚠️ Error al enviar el correo.")
        await update.message.reply_text("¿Necesitas algo más? Escribe /start para hacer otro pedido.")   
        return ConversationHandler.END 
    else:
        await update.message.reply_text("Pedido cancelado. Usa /start para empezar de nuevo.")
    return ConversationHandler.END

# --- Lanzar la app ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],

        states={
            # iterar sobre las claves del diccionario
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, seleccionar_servicio)],
            MODELO: [MessageHandler(filters.TEXT & ~filters.COMMAND, seleccionar_modelo)],
            REPUESTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, seleccionar_repuesto)],
            DATOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_datos)],
            AUTORIZACION: [MessageHandler(filters.TEXT & ~filters.COMMAND, autorizacion)],
            CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar)]
        },
        fallbacks=[]
    )
# Agregar el manejador de conversaciones
    app.add_handler(conv_handler)
    print("Bot de Repuestos de Carros activo...")
    app.run_polling()