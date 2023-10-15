from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from telegram import Bot
import asyncio
from flask_socketio import SocketIO, emit, join_room, leave_room
import time
import logging
from config import SQLALCHEMY_DATABASE_URI, BOT_TOKEN, CHAT_ID
from models import (
    db, 
    User,
    Channel,
    ReboundTelegram,
    generate_unique_channel_link)




logging.basicConfig(filename='bot_logs.txt', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

secret_key = '90f60ba324ecd8278ab17e0d8d4fac90230aac79b3539c1a'
app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
socketio = SocketIO(app)

db.init_app(app)


bot = Bot(token=BOT_TOKEN)


async def send_telegram_message(message_text):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message_text)
        time.sleep(10)  # Ожидание 1 секунды
    finally:
        await bot.close()


@app.route('/register', methods=['GET', 'POST'])
async def register():
    email = None
    channel_name = None
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        session['email'] = email
        session['link'] = channel_name
        channel_generate_link_name = generate_unique_channel_link()
        channel_url = url_for('channel_page', channel_link=channel_generate_link_name, _external=True)
        print(f'[URL], {channel_url}')

        new_user = User(name=name, email=email, phone=phone)
        db.session.add(new_user)

        new_channel = Channel(link=channel_generate_link_name, user=new_user)
        db.session.add(new_channel)

        new_rebound = ReboundTelegram(
            name_user=new_user.name,
            email_user=new_user.email,
            phone_user=new_user.phone,
            link_chat=channel_url
        )
        db.session.add(new_rebound)

        db.session.commit()

        email = new_user.email  # Получаем email нового пользователя
        channel_name = new_channel.link  # Получаем название канала

        message_text = f"Имя: {new_rebound.name_user}\nEmail: {new_rebound.email_user}\nНомер телефона: {new_rebound.phone_user}\nСсылка на чат: {new_rebound.link_chat}"
        
        # Используем asyncio.gather для отправки сообщения в Telegram и выполнения редиректа
        await asyncio.gather(
            send_telegram_message(message_text),
        )

        return redirect(channel_url)

    return render_template('registration.html', email=email, channel_name=channel_name)


@app.route('/check_user/<phone>')
def check_user(phone):
    user_exists = User.query.filter_by(phone=phone).first() is not None
    return jsonify({'exists': user_exists})

@app.route('/check_email/<email>')
def check_email(email):
    user_exists = User.query.filter_by(email=email).first() is not None
    return jsonify({'exists': user_exists})


# ---------------------------------------------------------------
# Функционал чата
@app.route('/chat/<channel_link>')
def channel_page(channel_link):
    channel = Channel.query.filter_by(link=channel_link).first()
    print(f'[INFO, 89 line, Channel] {channel}')
    if channel:
        user = db.session.get(User, channel.user_id)
        print(f'[INFO 92 line] {user.email}')
        if user:
            email = user.email
            return render_template('chat.html', channel_link=channel_link, email=email)
        else:
            return render_template('error.html', message='[404] User is not found')
    else:
        return render_template('error.html', message='[404] Channel not found')


@socketio.on('connect')
def handle_connect():
    print(request.args)
    email = request.args.get('email') 
    channel_link = request.args.get('channel_link')  
    join_room(channel_link)
    emit('user_connected', {'username': email})
    print(f'\033[94mПользователь {email} подключился к чату {channel_link}\033[0m')


# -----------------------------------------------------------------------------------------




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, port=4043, debug=True)