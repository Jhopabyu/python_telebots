from telebot import TeleBot 

TOKEN_BOT="8062513760:AAGrJwpXi5q9kib6VDg30vtulnGANYTPPf8"
bot = TeleBot(TOKEN_BOT)

@bot.message_handler(commands=['start'])
def start(message):
    print("Entro al start del bot")
    bot.send_message(message.chat.id, "Bienbenido a la tienda de pablo ")
    bot.register_next_step_handler(message,menu)
    
def menu(message):
    bot.send_message(message.chat.id, "Estos son lo paquetes que tenemos:\n 1. Paquete 1\n 2. Paquete 2\n 3. Paquete 3")
    bot.register_next_step_handler(message, opciones)
    
def opciones(message): 
    print(message)
    bot.send_message(message.chat.id, "opcion no valida")
    bot.register_next_step_handler(message)  
if __name__ == '__main__':
    print ("Bot iniciado")
    bot.infinity_polling()