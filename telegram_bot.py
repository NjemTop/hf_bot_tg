import encodings
import telebot
import telegram
from telebot import types
import requests
import pandas as pd
import json
from bs4 import BeautifulSoup
import subprocess, sys
import pathlib
from pathlib import Path
import random
import smtplib
import xml.etree.ElementTree as ET
import logging
import os
import platform
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.header import Header
from writexml import create_xml

# создаем форматирование
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')
# создаем логгер
error_logger = logging.getLogger('TeleBot')
error_logger.setLevel(logging.ERROR)
# создаем обработчик, который будет записывать ошибки в файл bot-error.log
error_handler = logging.FileHandler('./logs/bot-error.log')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)
# добавляем обработчик в логгер
error_logger.addHandler(error_handler)

# Создание объекта логгера для информационных сообщений
info_logger = logging.getLogger('info_logger')
info_logger.setLevel(logging.INFO)
info_handler = logging.FileHandler('./logs/bot-info.log')
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(formatter)
info_logger.addHandler(info_handler)

# Проверяем систему, где запускается скрипт
if platform.system() == 'Windows':
    # получаем путь к директории AppData\Local для текущего пользователя
    local_appdata_path = os.environ['LOCALAPPDATA']
else:
    local_appdata_path = os.environ['HOME']

# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"

# Читаем данные из файла
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
    DATA = json.load(f)

# Получаем значение ключа BOT_TOKEN в TELEGRAM_SETTINGS
BOT_TOKEN = DATA['TELEGRAM_SETTINGS']['BOT_TOKEN']

# Сохраняем значение в переменную TOKEN
TOKEN = BOT_TOKEN

### Авторизация в HappyFox
# извлекаем значения API_KEY и API_SECRET
API_KEY = DATA['HAPPYFOX_SETTINGS']['API_KEY']
API_SECRET = DATA['HAPPYFOX_SETTINGS']['API_SECRET']
# сохраняем значения в переменную auth
auth = (API_KEY, API_SECRET)
API_ENDPOINT = DATA['HAPPYFOX_SETTINGS']['API_ENDPOINT']
headers = {'Content-Type': 'application/json'}

# Создаем бота
bot=telebot.TeleBot(TOKEN)

# ФУНКЦИЯ ОТПРАВКИ АЛЕРТА В ЧАТ
def send_telegram_message(alert_chat_id, alert_text):
    """Отправляет сообщение в телеграм-бот"""
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    headers_server = {'Content-type': 'application/json'}
    data = {'chat_id': alert_chat_id, 'text': f'{alert_text}'}
    response = requests.post(url, headers=headers_server, data=json.dumps(data), timeout=30)
    print(response)

# УРОВЕНЬ 1 проверка вызова "старт" и доступа к боту
def check_user_in_file(chat_id):
    """Функция для проверки наличия данных в файле data.xml"""
    try:
        # Открываем файл и ищем chat_id
        with open(Path('data.xml'), encoding="utf-8") as user_access:
            root = ET.parse(user_access).getroot()
            for user in root.findall('user'):
                header_footer = user.find('header_footer')
                chat_id_elem = header_footer.find('chat_id')
                if chat_id_elem is not None and chat_id_elem.text == str(chat_id):
                    return True
                info_logger.info("Учётной записи нет в базе с ID: %s", chat_id)
                return False
    except FileNotFoundError as error_message:
        error_logger.error("Файл data.xml не найден: %s", error_message)
        print("Файл data.xml не найден")
    except ET.ParseError as error_message:
        error_logger.error("Произошла ошибка при чтении файла data.xml: %s", error_message)
        print("Ошибка чтения файла data.xml")
    return False

def get_name_by_chat_id(chat_id):
    """Функция для получения значения атрибута name из файла data.xml"""
    try:
        # Открываем файл и ищем chat_id
        with open(Path('data.xml'), encoding="utf-8") as user_access:
            root = ET.parse(user_access).getroot()
            for user in root.findall('user'):
                header_footer = user.find('header_footer')
                chat_id_elem = header_footer.find('chat_id')
                if chat_id_elem is not None and chat_id_elem.text == str(chat_id):
                    name_elem = header_footer.find('name')
                    if name_elem is not None:
                        return name_elem.text
                else:
                    info_logger.info("Учётной записи нет в базе с ID: %s", chat_id)
                    return None
    except FileNotFoundError as error_message:
        error_logger.error("Файл data.xml не найден: %s", error_message)
        print("Файл data.xml не найден")
    except ET.ParseError as error_message:
        error_logger.error("Произошла ошибка при чтении файла data.xml: %s", error_message)
        print("Ошибка чтения файла data.xml")
    return None

def get_header_footer_id(chat_id):
    """Функция для получения значения атрибута role_id из файла data.xml"""
    try:
        # Открываем файл и ищем chat_id
        with open(Path('data.xml'), encoding="utf-8") as user_access:
            root = ET.parse(user_access).getroot()
            for user in root.findall('user'):
                header_footer = user.find('header_footer')
                chat_id_elem = header_footer.find('chat_id')
                if chat_id_elem is not None and chat_id_elem.text == str(chat_id):
                    support_response_id = header_footer.get('id')
                    return support_response_id
                info_logger.info("Учётной записи нет в базе с ID: %s", chat_id)
                return None
    except FileNotFoundError as error_message:
        error_logger.error("Файл data.xml не найден: %s", error_message)
        print("Файл data.xml не найден")
    except ET.ParseError as error_message:
        error_logger.error("Произошла ошибка при чтении файла data.xml: %s", error_message)
        print("Ошибка чтения файла data.xml")
    return None

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_message(message_start):
    """Функция запуска бота кнопкой /start, а также проверка есть ли уже УЗ"""
    if check_user_in_file(message_start.chat.id):
        # Главное меню
        main_menu = types.InlineKeyboardMarkup()
        button_clients = types.InlineKeyboardButton(text='Клиенты', callback_data='button_clients')
        button_SD_Gold_Platinum = types.InlineKeyboardButton('ServiceDesk (Gold & Platinum)', callback_data='button_SD_Gold_Platinum')
        button_SD_Silver_Bronze = types.InlineKeyboardButton('ServiceDesk (Silver & Bronze)', callback_data='button_SD_Silver_Bronze')
        main_menu.add(button_clients, button_SD_Gold_Platinum, button_SD_Silver_Bronze, row_width=1)
        bot.send_message(message_start.chat.id, 'Приветствую! Выберите нужное действие:', reply_markup=main_menu)
    else:
        question_email = bot.send_message(message_start.chat.id,"Привет! Вашей учётной записи нет в базе.\nПожалуйста, введите адрес рабочей почты.")
        user_id = message_start.chat.id
        bot.register_next_step_handler(question_email, send_verification_code, user_id)

def get_user_info_happyfox(database_email_access_info):
    """Функция обработки УЗ в HappyFox"""
    # Ищем полученную почту в системе HappyFox
    try:
        staff = requests.get(API_ENDPOINT + '/staff/', auth=auth, headers=headers, timeout=30).json()
        for i in range(len(staff)):
            res_i = staff[i]
            find_email = res_i.get('email')
            if find_email == database_email_access_info:
                find_id_HF = res_i.get('id')
                email_access_id = find_email
                find_name = res_i.get('name')
                find_role = res_i.get('role') 
                find_role_id = find_role.get('id')
                return find_id_HF, email_access_id, find_name, find_role_id
        info_logger.info("Почты в системе HappyFox - нет: %s", database_email_access_info)
        print("Почты в системе HappyFox - нет")
        return None
    except requests.exceptions.Timeout as error_message:
        error_logger.error("Timeout error: %s", error_message)
        print("Timeout error:", error_message)
    except requests.exceptions.RequestException as error_message:
        error_logger.error("Request error: %s", error_message)
        print("Request error:", error_message)
        return None
    return None

def send_email(dest_email, email_text):
    """Функция отправки сообщения пользователю с паролем"""
    # Открытие файла и чтение его содержимого
    # Получение информации о почте, пароле и SMTP настройках
    EMAIL_FROM = DATA["MAIL_SETTINGS"]["FROM"]
    PASSWORD = DATA["MAIL_SETTINGS"]["PASSWORD"]
    SMTP_SERVER = DATA["MAIL_SETTINGS"]["SMTP"]
    try:
        ## Настройки SMTP сервера
        with smtplib.SMTP(SMTP_SERVER, 587) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_FROM, PASSWORD)

            subject = 'Добро пожаловать в наш бот!'
            msg_pass = None
            # Создаем объект сообщения отправки пароля на почту при регистрации
            msg_pass = MIMEMultipart()
            # Указываем заголовки
            msg_pass['From'] = EMAIL_FROM
            msg_pass['To'] = dest_email
            msg_pass['Subject'] = subject
            # Добавляем текст сообщения в формате HTML
            msg_pass.attach(MIMEText(email_text, 'html', 'utf-8'))
            # Отправляем сообщение
            server.sendmail(EMAIL_FROM, dest_email, msg_pass.as_string())
    except smtplib.SMTPConnectError as error_message:
        error_logger.error("Произошла ошибка отправки пароля на почту: %s", error_message)
        print("Произошла ошибка отправки пароля на почту:", error_message)

## Если пользователя нет в списке, просим его указать почту, куда будет выслан сгенерированный пароль
def send_verification_code(email_access, user_id):
    """Функция проверки почты на соотвествие и отправления случайного пароля на почту"""
    try:
        ## Если почтовый адрес содержит "@boardmaps.ru"
        if ('@boardmaps.ru' in email_access.text and email_access.chat.id == user_id):
            ## Генерируем рандомный пароль для доступа к боту
            access_password = generate_random_password()
            info_logger.info('Сгенерирован временный пароль: %s, для почты: %s', access_password, email_access.text)
            # Формируем текст письма, включая сгенерированный пароль
            email_text = None
            email_text = f'''\
            <html>
                <body style="background-color: lightblue"; padding: 10px">
                    <h2>Здравствуйте!</h2>
                    <p>Вы успешно зарегистрировались в нашем боте. Ниже приведен временный пароль для входа в систему:</p>
                    <ul>
                        <li><a href="">{access_password}</a></li>
                    </ul>
                    <p>Пожалуйста, введите его в окне бота и не сообщайте его никому.</p>
                    <p>С уважением,<br>Администратор бота</p>
                </body>
            </html>
            '''
            # Отправляем сообщение пользователю
            send_email(email_access.text, email_text)
            info_logger.info("Пользователю с 'chat id': %s, отправлен пароль на почту: %s, ", (email_access.chat.id), (email_access.text))

            ## Бот выдает сообщение с просьбой ввести пароль + вносим почту пользователя в БД
            password_message = bot.send_message(email_access.chat.id, "Пожалуйста, введите пароль, отправленный на указанную почту.")
            bot.register_next_step_handler(password_message, check_pass_answer, access_password, email_access.text)
            
        else:
            bot.send_message(email_access.chat.id, 'К сожалению, не могу предоставить доступ.')
            error_logger.error("Несовпадение chat id: %s сообщением от %s", email_access.chat.id, email_access.message.chat.id)
    except ValueError as error_message:
        error_logger.error("Произошла ошибка отправки пароля на почту: %s", error_message)
        print("Произошла ошибка отправки пароля на почту:", error_message)

def generate_random_password(length=6):
    """Функция для генерации случайного пароля указанной длины, состоящего только из цифр"""
    # все возможные символы для пароля
    chars = string.digits
    # генерируем случайную строку из символов заданной длины
    access_password = ''.join(random.choice(chars) for _ in range(length))
    # возвращаем пароль, при вызове функции
    return access_password

## Проверяем введенный пользователем пароль
def check_pass_answer(password_message, access_password, email_access):
    """Функция проверки пароля и записи УЗ в data.xml"""
    try:
        ## Если пароль подходит
        if password_message.text == access_password:
            ## ВРЕМЕННЫЙ АРГУМЕНТ роли
            find_role = 'Admin'
            find_id_HF = None
            email_access_id = None
            find_name = None
            find_role_id = None
            # Запускаем функцию и передаём туда email пользователя
            user_info = get_user_info_happyfox(email_access)
            if user_info is not None:
                find_id_HF, email_access_id, find_name, find_role_id = user_info
            # Создаем XML файл и записываем данные
            create_xml(email_access_id, find_id_HF, find_name, find_role, find_role_id, password_message.chat.id)

            info_logger.info("Сотрудник: %s, прошёл регистрацию в боте", find_name)
            ## Показываем пользователю главное меню
            main_menu = types.InlineKeyboardMarkup()
            button_clients = types.InlineKeyboardButton(text= 'Клиенты', callback_data='button_clients')
            button_SD_Gold_Platinum = types.InlineKeyboardButton('ServiceDesk (Gold & Platinum)', callback_data='button_SD_Gold_Platinum')
            button_SD_Silver_Bronze = types.InlineKeyboardButton('ServiceDesk (Silver & Bronze)', callback_data='button_SD_Silver_Bronze')
            main_menu.add(button_clients, button_SD_Gold_Platinum, button_SD_Silver_Bronze, row_width=1)
            bot.send_message(password_message.chat.id, 'Приветствую! Выберите нужное действие:', reply_markup=main_menu)
        elif password_message.text == '/start':
            start_message(password_message.chat.id)
            return
        else:
            ## Запросить новый пароль
            bot.send_message(password_message.chat.id, 'Неправильный пароль. Введите пароль ещё раз.')
            ## Зарегистрировать следующий шаг обработчика сообщений
            bot.register_next_step_handler(password_message, check_pass_answer, access_password)
            info_logger.info("Введён неправильный пароль сотрудником:%s", password_message.chat.id)
    except Exception as error_message:
        error_logger.error("Произошла ошибка проверки пароля и записи УЗ в data.xml: %s", error_message)
        print("Произошла ошибка проверки пароля и записи УЗ в data.xml:", error_message)

# Обработчик вызова /clients
@bot.message_handler(commands=['clients'])
def clients_message(message_clients):
    """Функция вызова кнопки /clients"""
    if check_user_in_file(message_clients.chat.id):
        button_clients = types.InlineKeyboardMarkup()
        button_list_of_clients = types.InlineKeyboardButton(text='Список клиентов', callback_data='button_list_of_clients')
        button_clients_version = types.InlineKeyboardButton(text='Версии клиентов', callback_data='button_clients_version')
        button_templates = types.InlineKeyboardButton(text='Статистика по тикетам за период (шаблоны)', callback_data='button_templates')
        button_clients.add(button_list_of_clients, button_clients_version, button_templates, row_width=2)
        bot.send_message(message_clients.chat.id, 'Какую информацию хотите получить?', reply_markup=button_clients)
    else:
        bot.send_message(message_clients.chat.id,"К сожалению, у Вас отсутствует доступ.")
# Обработчик вызова /sd_sb
@bot.message_handler(commands=['sd_sb'])
def sd_sb_message(message_sd_sb):
    """Функция вызова кнопки /sd_sb"""
    if check_user_in_file(message_sd_sb.chat.id):
        button_SD_Silver_Bronze = types.InlineKeyboardMarkup()
        button_update_tickets_SB = types.InlineKeyboardButton(text='Обновление версии приложения (S&B)', callback_data='button_update_tickets_SB')
        button_else_SB = types.InlineKeyboardButton(text= 'Остальные тикеты (S&B)', callback_data='button_else_SB')
        button_SD_Silver_Bronze.add(button_update_tickets_SB, button_else_SB, row_width=1)
        bot.send_message(message_sd_sb.chat.id, 'Выберите раздел:', reply_markup=button_SD_Silver_Bronze)
    else:
        bot.send_message(message_sd_sb.chat.id,"К сожалению, у Вас отсутствует доступ.")
# Обработчик вызова /sd_gp
@bot.message_handler(commands=['sd_gp'])
def sd_gp_message(message_sd_gp):
    """Функция вызова кнопки /sd_gp"""
    if check_user_in_file(message_sd_gp.chat.id):
        button_SD_Gold_Platinum = types.InlineKeyboardMarkup()
        button_update_tickets_GP = types.InlineKeyboardButton(text='Обновление версии приложения (G&P)', callback_data='button_update_tickets_GP')
        button_else_GP = types.InlineKeyboardButton(text= 'Остальные тикеты (G&P)', callback_data='button_else_GP')
        button_SD_Gold_Platinum.add(button_update_tickets_GP, button_else_GP, row_width=1)
        bot.send_message(message_sd_gp.chat.id,"Выберите раздел:", reply_markup=button_SD_Gold_Platinum)
    else:
        bot.send_message(message_sd_gp.chat.id,"К сожалению, у Вас отсутствует доступ.")

# Добавляем подуровни к кнопкам выше
@bot.callback_query_handler(func=lambda call: True)
def inline_button(call):
    """Функция возврата в главное меню. Кнопки [Клиенты] / [ServiceDesk (Gold & Platinum)] / [ServiceDesk (Silver & Bronze)]"""
    if call.data == "mainmenu":
        main_menu = types.InlineKeyboardMarkup()
        button_clients = types.InlineKeyboardButton(text= 'Клиенты', callback_data='button_clients')
        button_SD_Gold_Platinum = types.InlineKeyboardButton('ServiceDesk (Gold & Platinum)', callback_data='button_SD_Gold_Platinum')
        button_SD_Silver_Bronze = types.InlineKeyboardButton('ServiceDesk (Silver & Bronze)', callback_data='button_SD_Silver_Bronze')
        main_menu.add(button_clients, button_SD_Gold_Platinum, button_SD_Silver_Bronze, row_width=1)
        bot.edit_message_text('Главное меню:', call.message.chat.id, call.message.message_id, reply_markup=main_menu)
    
# УРОВЕНЬ 2 "КЛИЕНТЫ". Добавляем кнопки [Список клиентов] / [Версии клиентов] / [Шаблоны]
    elif call.data == "button_clients":
        button_clients = types.InlineKeyboardMarkup()
        button_list_of_clients = types.InlineKeyboardButton(text='Список клиентов', callback_data='button_list_of_clients')
        button_clients_version = types.InlineKeyboardButton(text='Версии клиентов', callback_data='button_clients_version')
        button_templates = types.InlineKeyboardButton(text='Статистика по тикетам за период (шаблоны)', callback_data='button_templates')
        button_clients.add(button_list_of_clients, button_clients_version, button_templates, row_width=2)
        back_from_button_clients = types.InlineKeyboardButton(text='Назад', callback_data='mainmenu')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_clients.add(back_from_button_clients, main_menu, row_width=2)
        bot.edit_message_text('Какую информацию хотите получить?', call.message.chat.id, call.message.message_id,reply_markup=button_clients)
    # УРОВЕНЬ 3. Вызов кнопки "СПИСОК КЛИЕНТОВ"
    elif call.data == 'button_list_of_clients':
        button_list_of_clients = types.InlineKeyboardMarkup()
        back_from_button_list_of_clients = types.InlineKeyboardButton(text= 'Назад', callback_data='button_clients')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_list_of_clients.add(back_from_button_list_of_clients, main_menu, row_width=2)
        bot.edit_message_text('Для просмотра списка клиентов, пожалуйста, перейдите по ссылке:\nhttps://apps.boardmaps.ru/app/creg/page1-63bd167887eafa565f728b82.', call.message.chat.id, call.message.message_id,reply_markup=button_list_of_clients)
    # УРОВЕНЬ 3 "ВЕРСИИ КЛИЕНТОВ". Добавляем кнопки [Общий список версий] / [Узнать версию клиента]
    elif call.data == "button_clients_version":
        button_clients_version = types.InlineKeyboardMarkup()
        button_version_main_list = types.InlineKeyboardButton(text='Общий список версий', callback_data='button_version_main_list')
        button_version = types.InlineKeyboardButton(text= 'Узнать версию клиента', callback_data='button_version')
        button_clients_version.add(button_version_main_list, button_version, row_width=2)
        back_from_button_clients_version = types.InlineKeyboardButton(text= 'Назад', callback_data='button_clients')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_clients_version.add(back_from_button_clients_version, main_menu, row_width=2)
        bot.edit_message_text('Выберите раздел:', call.message.chat.id, call.message.message_id,reply_markup=button_clients_version)
    ### УРОВЕНЬ 4 "ОБЩИЙ СПИСОК ВЕРСИЙ". Добавляем ссылку на список
    elif call.data == "button_version_main_list":
        button_version_main_list = types.InlineKeyboardMarkup()
        back_from_button_version_main_list = types.InlineKeyboardButton(text= 'Назад', callback_data='button_clients_version')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_version_main_list.add(back_from_button_version_main_list, main_menu, row_width=2)
        bot.edit_message_text('Для просмотра списка версий клиентов, пожалуйста, перейдите по ссылке:\nhttps://apps.boardmaps.ru/app/creg/page1-63bd167887eafa565f728b82.', call.message.chat.id, call.message.message_id,reply_markup=button_version_main_list)
    ### УРОВЕНЬ 4 "УЗНАТЬ ВЕРСИЮ КЛИЕНТА"
    elif call.data == "button_version":  
        button_version = types.InlineKeyboardMarkup()
        back_from_button_version = types.InlineKeyboardButton(text='Отмена', callback_data='button_clients_version') 
        main_menu = types.InlineKeyboardButton(text='Главное меню', callback_data='mainmenu')
        button_version.add(back_from_button_version, main_menu, row_width=2)
        test=bot.edit_message_text('Просьба отправить в чат сообщение с наименованием клиента, версию которого Вы хотите узнать.', call.message.chat.id, call.message.message_id,reply_markup=button_version)
        bot.register_next_step_handler(test,send_text_version)

    # УРОВЕНЬ 3 "ШАБЛОНЫ". Добавляем кнопки [Теле2] / [ПСБ] / [РЭЦ] / [Почта России]
    elif call.data == "button_templates": 
        button_templates = types.InlineKeyboardMarkup()
        button_tele2 = types.InlineKeyboardButton(text='Теле2', callback_data='button_tele2')
        button_psb = types.InlineKeyboardButton(text='ПСБ', callback_data='button_psb')
        button_rez = types.InlineKeyboardButton(text='РЭЦ', callback_data='button_rez')
        button_pochtaR = types.InlineKeyboardButton(text='Почта России', callback_data='button_pochtaR')
        button_templates.add(button_tele2, button_psb, button_rez, button_pochtaR, row_width=2)
        back_from_button_templates = types.InlineKeyboardButton(text='Назад', callback_data='button_clients')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_templates.add(back_from_button_templates, main_menu, row_width=2)
        bot.edit_message_text('Шаблон какого клиента необходимо выгрузить?', call.message.chat.id, call.message.message_id,reply_markup=button_templates)
    ### УРОВЕНЬ 4 "ТЕЛЕ2" 
    elif call.data == "button_tele2":
        bot.send_message(call.message.chat.id, text='Пожалуйста, ожидайте. По завершении процесса, в чат будет отправлен файл отчета.')
        setup_script = 'Report_tele2.ps1'
        try:
            result_tele2 = subprocess.run(["pwsh", "-File", setup_script],stdout=sys.stdout, check=True)
            # Записываем в лог информацию о пользователе, сформировавшем отчет
            xml_data = None
            with open('data.xml', encoding='utf-8-sig') as file_data:
                xml_data = file_data.read()
                root = ET.fromstring(xml_data)
                chat_id = root.find('chat_id').text
                if str(call.message.chat.id) == chat_id:
                    name = root.find('header_footer/name').text
                    info_logger.info("Пользователь: %s сформировал отчет.", name)
        except subprocess.CalledProcessError as error_message:
            error_logger.error("Ошибка при запуске скрипта %s: %s", setup_script, error_message)
            bot.send_message(call.message.chat.id, text='Произошла ошибка при формировании отчета.')
        else:
            if platform.system() == 'Windows':
                # формируем путь к файлу отчета в директории AppData\Local
                report_path = os.path.join(local_appdata_path, 'Report_tele2.docx').replace('\\', '/')
            elif platform.system() == 'Linux':
                report_path = os.path.join(local_appdata_path, 'Report_tele2.docx')
            with open(report_path, 'rb') as report_file:
                bot.send_document(call.message.chat.id, report_file)
    
    ### УРОВЕНЬ 4 "ПСБ"
    elif call.data == "button_psb":  
        bot.send_message(call.message.chat.id, text='Пожалуйста, ожидайте. По завершении процесса, в чат будет отправлен файл отчета.')
        setup_script = 'Скрипт_формирования_отчёта_клиента_ПСБ.ps1'
        try:
            result_rez = subprocess.run(["pwsh", "-File", setup_script],stdout=sys.stdout, check=True)
            # Записываем в лог информацию о пользователе, сформировавшем отчет
            xml_data = None
            with open('data.xml', encoding='utf-8-sig') as file_data:
                xml_data = file_data.read()
                root = ET.fromstring(xml_data)
                chat_id = root.find('chat_id').text
                if str(call.message.chat.id) == chat_id:
                    name = root.find('header_footer/name').text
                    info_logger.info("Пользователь: %s сформировал отчет.", name)
        except subprocess.CalledProcessError as error_message:
            error_logger.error("Ошибка при запуске скрипта %s: %s", setup_script, error_message)
            bot.send_message(call.message.chat.id, text='Произошла ошибка при формировании отчета.')
        else:
            if platform.system() == 'Windows':
                # формируем путь к файлу отчета в директории AppData\Local
                report_path = os.path.join(local_appdata_path, 'Отчёт_клиента_ПСБ.docx').replace('\\', '/')
            elif platform.system() == 'Linux':
                report_path = os.path.join(local_appdata_path, 'Отчёт_клиента_ПСБ.docx')
            with open(report_path, 'rb') as report_file:
                bot.send_document(call.message.chat.id, report_file)

    ### УРОВЕНЬ 4 "РЭЦ"
    elif call.data == "button_rez":  
        bot.send_message(call.message.chat.id, text='Пожалуйста, ожидайте. По завершении процесса, в чат будет отправлен файл отчета.')
        setup_script = 'Скрипт_формирования_отчёта_клиента_РЭЦ.ps1'
        try:
            result_rez = subprocess.run(["pwsh", "-File", setup_script],stdout=sys.stdout, check=True)
            # Записываем в лог информацию о пользователе, сформировавшем отчет
            xml_data = None
            with open('data.xml', encoding='utf-8-sig') as file_data:
                xml_data = file_data.read()
                root = ET.fromstring(xml_data)
                chat_id = root.find('chat_id').text
                if str(call.message.chat.id) == chat_id:
                    name = root.find('header_footer/name').text
                    info_logger.info("Пользователь: %s сформировал отчет.", name)
        except subprocess.CalledProcessError as error_message:
            error_logger.error("Ошибка при запуске скрипта %s: %s", setup_script, error_message)
            bot.send_message(call.message.chat.id, text='Произошла ошибка при формировании отчета.')
        else:
            if platform.system() == 'Windows':
                # формируем путь к файлу отчета в директории AppData\Local
                report_path = os.path.join(local_appdata_path, 'Отчёт_клиента_РЭЦ.docx').replace('\\', '/')
            elif platform.system() == 'Linux':
                report_path = os.path.join(local_appdata_path, 'Отчёт_клиента_РЭЦ.docx')
            with open(report_path, 'rb') as report_file:
                bot.send_document(call.message.chat.id, report_file)

    ### УРОВЕНЬ 4 "ПОЧТА РОССИИ" ///////////////////////////////////////// в работе
    #elif call.data == "button_pochtaR": 

# УРОВЕНЬ 2 "SD (GOLD & PLATINUM)". Добавляем кнопки [Обновление версии приложения] / [Остальные тикеты]
    elif call.data == "button_SD_Gold_Platinum":
        button_SD_Gold_Platinum = types.InlineKeyboardMarkup()
        button_update_tickets_GP = types.InlineKeyboardButton(text='Обновление версии приложения (G&P)', callback_data='button_update_tickets_GP')
        button_else_GP = types.InlineKeyboardButton(text= 'Остальные тикеты (G&P)', callback_data='button_else_GP')
        button_SD_Gold_Platinum.add(button_update_tickets_GP, button_else_GP, row_width=1)
        back_from_button_SD_Gold_Platinum = types.InlineKeyboardButton(text= 'Назад', callback_data='mainmenu')
        button_SD_Gold_Platinum.add(back_from_button_SD_Gold_Platinum, row_width=1)
        bot.edit_message_text('Выберите раздел:', call.message.chat.id, call.message.message_id,reply_markup=button_SD_Gold_Platinum)
    # УРОВЕНЬ 3 "ОБНОВЛЕНИЕ ВЕРСИИ ПРИЛОЖЕНИЯ" (G&P). Добавляем кнопки [Создать тикеты по списку] / [Повторный запрос сервисного окна]
    elif call.data == "button_update_tickets_GP":
        button_update_tickets_GP = types.InlineKeyboardMarkup()
        button_create_tickets_GP = types.InlineKeyboardButton(text='Создать тикеты по списку (G&P)', callback_data='button_create_tickets_GP')
        button_reply_request_GP = types.InlineKeyboardButton(text= 'Повторный запрос сервисного окна (G&P)', callback_data='button_reply_request_GP')
        button_update_tickets_GP.add(button_create_tickets_GP, button_reply_request_GP, row_width=1)
        back_from_button_update_tickets_GP = types.InlineKeyboardButton(text= 'Назад', callback_data='button_SD_Gold_Platinum')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_update_tickets_GP.add(back_from_button_update_tickets_GP, main_menu, row_width=2)
        bot.edit_message_text('Выберите раздел:', call.message.chat.id, call.message.message_id,reply_markup=button_update_tickets_GP)
    ### УРОВЕНЬ 4 "СОЗДАТЬ ТИКЕТЫ ПО СПИСКУ" (G&P)
    elif call.data == "button_create_tickets_GP":
        button_create_tickets_GP = types.InlineKeyboardMarkup()
        back_from_button_create_tickets_GP = types.InlineKeyboardButton(text= 'Назад', callback_data='button_update_tickets_GP')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_create_tickets_GP.add(back_from_button_create_tickets_GP, main_menu, row_width=2)
        create = bot.edit_message_text('Пожалуйста, напишите в чат номер версии. Пример: 2.60.', call.message.chat.id, call.message.message_id,reply_markup=button_create_tickets_GP)
        bot.register_next_step_handler(create,send_text_for_create_GP)
    ### УРОВЕНЬ 4 "ПОВТОРНЫЙ ЗАПРОС СЕРВИСНОГО ОКНА" (G&P)
    elif call.data == "button_reply_request_GP":
        button_reply_request_GP = types.InlineKeyboardMarkup()
        button_reply_request_GP_yes = types.InlineKeyboardButton(text= 'Да', callback_data='button_reply_request_GP_yes')
        button_reply_request_GP.add(button_reply_request_GP_yes, row_width=1)
        back_from_button_reply_request_GP = types.InlineKeyboardButton(text= 'Назад', callback_data='button_update_tickets_GP')
        main_menu = types.InlineKeyboardButton(text='Главное меню', callback_data='mainmenu')
        button_reply_request_GP.add(back_from_button_reply_request_GP, main_menu, row_width=2)
        bot.edit_message_text('Вы собираетесь запустить повторную отправку запросов на предоставление сервисного окна для Gold и Platinum клиентов. Подтвердите свой выбор.', call.message.chat.id, call.message.message_id,reply_markup=button_reply_request_GP)
    #### УРОВЕНЬ 5: при нажатии кнопки ДА по повторной отправке запроса сервисного окна для G&P     
    elif call.data == "button_reply_request_GP_yes":
        bot.send_message(call.message.chat.id, text='Процесс запущен, ожидайте.')
        setup_script = 'Auto_ping_test.ps1'
        subprocess.run(["pwsh", "-File", setup_script],stdout=sys.stdout)
        bot.send_message(call.message.chat.id, text='Процесс завершен. Повторные запросы направлены клиентам.')
    
    # УРОВЕНЬ 3 "ОСТАЛЬНЫЕ ТИКЕТЫ" (G&P) ///////////////////////////////////////////////// в работе
    elif call.data == "button_else_GP":    
        button_else_GP = types.InlineKeyboardMarkup()
        back_from_button_else_GP = types.InlineKeyboardButton(text='Назад', callback_data='button_SD_Gold_Platinum')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_else_GP.add(back_from_button_else_GP, main_menu, row_width=2)
        bot.edit_message_text('Кнопка на ремонте.', call.message.chat.id, call.message.message_id,reply_markup=button_else_GP)
# УРОВЕНЬ 2 "SD (SILVER & BRONZE)". Добавляем кнопки [Обновление версии приложения] / [Остальные тикеты]
    elif call.data == "button_SD_Silver_Bronze":
        button_SD_Silver_Bronze = types.InlineKeyboardMarkup()
        button_update_tickets_SB = types.InlineKeyboardButton(text='Обновление версии приложения (S&B)', callback_data='button_update_tickets_SB')
        button_else_SB = types.InlineKeyboardButton(text= 'Остальные тикеты (S&B)', callback_data='button_else_SB')
        button_SD_Silver_Bronze.add(button_update_tickets_SB, button_else_SB, row_width=1)
        back_from_button_SD_Silver_Bronze = types.InlineKeyboardButton(text= 'Назад', callback_data='mainmenu')
        button_SD_Silver_Bronze.add(back_from_button_SD_Silver_Bronze, row_width=1)
        bot.edit_message_text('Выберите раздел:', call.message.chat.id, call.message.message_id,reply_markup=button_SD_Silver_Bronze)
    # УРОВЕНЬ 3 "ОБНОВЛЕНИЕ ВЕРСИИ ПРИЛОЖЕНИЯ" (S&B). Добавляем кнопки [Создать тикеты по списку] / [Получить статистику по тикетам] 
    elif call.data == "button_update_tickets_SB":
        button_update_tickets_SB = types.InlineKeyboardMarkup()
        button_create_update_tickets_SB = types.InlineKeyboardButton(text='Создать тикеты по списку (S&B)', callback_data='button_create_update_tickets_SB')
        button_update_statistics_SB = types.InlineKeyboardButton(text= 'Получить статистику по тикетам (S&B)', callback_data='button_update_statistics_SB')
        button_update_tickets_SB.add(button_create_update_tickets_SB, button_update_statistics_SB, row_width=1)
        back_from_button_update_tickets_SB = types.InlineKeyboardButton(text= 'Назад', callback_data='button_SD_Silver_Bronze')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_update_tickets_SB.add(back_from_button_update_tickets_SB, main_menu, row_width=2)
        bot.edit_message_text('Какое действие необходимо выполнить?', call.message.chat.id, call.message.message_id,reply_markup=button_update_tickets_SB)
    ### УРОВЕНЬ 4 "СОЗДАТЬ ТИКЕТЫ ПО СПИСКУ" (S&B) [ОБНОВЛЕНИЕ]
    elif call.data == "button_create_update_tickets_SB":
        button_create_update_tickets_SB = types.InlineKeyboardMarkup()
        back_from_button_create_update_tickets_SB = types.InlineKeyboardButton(text= 'Назад', callback_data='button_update_tickets_SB')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_create_update_tickets_SB.add(back_from_button_create_update_tickets_SB, main_menu, row_width=2)
        choice = bot.edit_message_text('Пожалуйста, напишите в чат номер версии. Пример: 2.60.', call.message.chat.id, call.message.message_id,reply_markup=button_create_update_tickets_SB)
        bot.register_next_step_handler(choice,send_text_for_create_SB)

    ### УРОВЕНЬ 4 "ПОЛУЧИТЬ СТАТИСТИКУ ПО ТИКЕТАМ" (S&B) [ОБНОВЛЕНИЕ] 
    elif call.data == "button_update_statistics_SB":
        button_update_statistics_SB = types.InlineKeyboardMarkup()
        back_from_button_update_statistics_SB = types.InlineKeyboardButton(text='Назад', callback_data='button_update_tickets_SB')
        main_menu = types.InlineKeyboardButton(text='Главное меню', callback_data='mainmenu')
        button_update_statistics_SB.add(back_from_button_update_statistics_SB, main_menu, row_width=2)
        choice_stat_version = bot.edit_message_text('Пожалуйста, напишите в чат номер версии, в разрезе которой необходимо сформировать статистику. Пример: 2.60.', call.message.chat.id, call.message.message_id,reply_markup=button_update_statistics_SB)
        bot.register_next_step_handler(choice_stat_version, send_text_for_stat_update_SB)

    # УРОВЕНЬ 3 "ОСТАЛЬНЫЕ ТИКЕТЫ" (S&B) Добавляем кнопки [Получить статистику по тикетам] ///////////////////////////////////////////////// в работе
    elif call.data == "button_else_SB": 
        button_else_SB = types.InlineKeyboardMarkup()
        button_statistics_else_tickets_SB = types.InlineKeyboardButton(text= 'Получить статистику по тикетам', callback_data='button_statistics_else_tickets_SB')
        button_else_SB.add(button_statistics_else_tickets_SB, row_width=1)
        back_from_button_else_SB = types.InlineKeyboardButton(text= 'Назад', callback_data='button_SD_Silver_Bronze')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_else_SB.add(back_from_button_else_SB, main_menu, row_width=2)
        bot.edit_message_text('Какое действие необходимо выполнить?', call.message.chat.id, call.message.message_id,reply_markup=button_else_SB)
    ### УРОВЕНЬ 4 "ПОЛУЧИТЬ СТАТИСТИКУ ПО ТИКЕТАМ" [ОСТАЛЬНЫЕ]  ///////////////////////////////////////////////// в работе
    elif call.data == "button_statistics_else_tickets_SB":
        button_statistics_else_tickets_SB = types.InlineKeyboardMarkup()
        back_from_button_statistics_else_tickets_SB = types.InlineKeyboardButton(text='Назад', callback_data='button_else_SB')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_statistics_else_tickets_SB.add(back_from_button_statistics_else_tickets_SB, main_menu, row_width=2)
        bot.edit_message_text('Кнопка на ремонте.', call.message.chat.id, call.message.message_id,reply_markup=button_statistics_else_tickets_SB)

#### ДОПОЛНИТЕЛЬНО: при нажатии кнопки ДА по корректности темы в рассылке тикетов по обновлению
    ## ДЛЯ SB
    elif call.data == "button_choise_yes_SB":
        support_response_id = get_header_footer_id(call.message.chat.id)
        if support_response_id is None:
            bot.edit_message_text('У Вас нет прав на отправку рассылки. Пожалуйста, обратитесь к администратору.', call.message.chat.id, call.message.message_id)
            return
        bot.edit_message_text('Отлично! Начат процесс создания тикетов с запросом сервисного окна. Пожалуйста, ожидайте.', call.message.chat.id, call.message.message_id)
        setup_script = Path('Automatic_email_BS.ps1')
        try:
            name_who_run_script = get_name_by_chat_id(call.message.chat.id)
            info_logger.info("Запуск скрипта по отправке рассылки BS, пользователем: %s, номер версии рассылки: %s", name_who_run_script, version_SB)
            result_SB = subprocess.run(["pwsh", "-File", setup_script, str(version_SB), str(support_response_id)], stdout=subprocess.PIPE, check=True).stdout.decode('utf-8')
        except subprocess.CalledProcessError as error_message:
            error_logger.error("Ошибка запуска скрипта по отправке рассылки BS: %s", error_message)
            print("Ошибка запуска скрипта по отправке рассылки BS:", error_message)
        # Записываем вывод из терминала PowerShell, чтобы потом сформировать в файл и отправить в телегу
        with open(f'/app/logs/report_send_SB({version_SB}).log', 'a+', encoding='utf-8-sig') as file_send:
            file_send.write(result_SB)
            file_send.seek(0)  # перематываем указатель в начало файла
            # Отправляем вывод всего результата в телеграмм бота
            bot.send_document(call.message.chat.id, file_send)
        button_choise_yes_SB = types.InlineKeyboardMarkup()
        back_from_button_choise_yes_SB = types.InlineKeyboardButton(text='Назад', callback_data='button_create_update_tickets_SB')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_choise_yes_SB.add(back_from_button_choise_yes_SB, main_menu, row_width=2)
        info_logger.info("Рассылка клиентам BS успешно отправлена.")
        bot.send_message(call.from_user.id, text='Процесс завершен. Тикеты с запросом сервисного окна созданы. Файл с результатами отправлен на почту.', reply_markup=button_choise_yes_SB)   
        try:
            os.remove(f'/app/logs/report_send_SB({version_SB}).log')
        except FileNotFoundError as error_message:
            error_logger.error('Файл не найден: %s', error_message)
            print('Файл не найден: %s', error_message)
        except PermissionError as error_message:
            error_logger.error('Недостаточно прав для удаления файла: %s', error_message)
            print('Недостаточно прав для удаления файла: %s', error_message)
        except OSError as error_message:
            error_logger.error('Ошибка при удалении файла: %s', error_message)
            print('Ошибка при удалении файла: %s', error_message)
        
    ## ДЛЯ GP
    elif call.data == "button_choise_yes_GP":
        support_response_id = get_header_footer_id(call.message.chat.id)
        if support_response_id is None:
            bot.edit_message_text('У Вас нет прав на отправку рассылки. Пожалуйста, обратитесь к администратору.', call.message.chat.id, call.message.message_id)
            return
        bot.edit_message_text('Отлично! Начат процесс создания тикетов и рассылки писем по списку. Пожалуйста, ожидайте.', call.message.chat.id, call.message.message_id)
        setup_script = Path('Automatic_email_GP.ps1')
        try:
            name_who_run_script = get_name_by_chat_id(call.message.chat.id)
            info_logger.info("Запуск скрипта по запросу сервисного окна клиентам GP, пользователем: %s, номер версии рассылки: %s", name_who_run_script, version_GP)
            result_GP = subprocess.run(["pwsh", "-File", setup_script, str(version_GP), str(support_response_id)], stdout=subprocess.PIPE, check=True).stdout.decode('utf-8')
        except subprocess.CalledProcessError as error_message:
            error_logger.error("Ошибка запуска скрипта по отправке рассылки GP: %s", error_message)
            print("Ошибка запуска скрипта по отправке рассылки GP:", error_message)
        # Записываем вывод из терминала PowerShell, чтобы потом сформировать в файл и отправить в телегу
        with open(f'/app/logs/report_send_GP({version_GP}).log', 'a+', encoding='utf-8-sig') as file_send:
            file_send.write(result_GP)
            file_send.seek(0)  # перематываем указатель в начало файла
            # Отправляем вывод всего результата в телеграмм бота
            bot.send_document(call.message.chat.id, file_send)
        button_choise_yes_GP = types.InlineKeyboardMarkup()
        back_from_button_choise_yes_GP = types.InlineKeyboardButton(text='Назад', callback_data='button_create_tickets_GP')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_choise_yes_GP.add(back_from_button_choise_yes_GP, main_menu, row_width=2)
        info_logger.info("Запрос сервисного окна клиентам GP отправлен")
        bot.edit_message_text('Процесс завершен. Тикеты созданы, рассылка отправлена. Файл с результатами отправлен на почту.', call.message.chat.id, call.message.message_id,reply_markup=button_choise_yes_GP)
        try:
            os.remove(f'/app/logs/report_send_GP({version_GP}).log')
        except FileNotFoundError as error_message:
            error_logger.error('Файл не найден: %s', error_message)
            print('Файл не найден: %s', error_message)
        except PermissionError as error_message:
            error_logger.error('Недостаточно прав для удаления файла: %s', error_message)
            print('Недостаточно прав для удаления файла: %s', error_message)
        except OSError as error_message:
            error_logger.error('Ошибка при удалении файла: %s', error_message)
            print('Ошибка при удалении файла: %s', error_message)

#### ДОПОЛНИТЕЛЬНО: при нажатии кнопки ДА по формированию статистики по тикетам SB update
    elif call.data == "button_update_statistics_yes_SB":
        bot.edit_message_text('Отлично! Произвожу расчеты. Пожалуйста, ожидайте.', call.message.chat.id, call.message.message_id)
        setup_script = Path('Ticket_Check_SB_update_statistics.ps1')
        try:
            result = subprocess.run(["pwsh", "-File", setup_script,str(version_stat) ],stdout=sys.stdout, check=True)
            name_who_run_script = get_name_by_chat_id(call.message.chat.id)
            info_logger.info("Запуск скрипта по отправке рассылки GP, пользователем: %s", name_who_run_script)
        except subprocess.CalledProcessError as error_message:
            error_logger.error("Ошибка запуска скрипта по отправке рассылки GP: %s", error_message)
            print("Ошибка запуска скрипта по отправке рассылки GP:", error_message)
        button_update_statistics_yes_SB = types.InlineKeyboardMarkup()
        back_from_button_update_statistics_yes_SB = types.InlineKeyboardButton(text='Назад', callback_data='button_update_statistics_SB')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_update_statistics_yes_SB.add(back_from_button_update_statistics_yes_SB, main_menu, row_width=2)
        bot.edit_message_text(('Статистика по обновлению версии  "' + str(version_stat) + '" :\n' + str(result.stdout)), call.message.chat.id, call.message.message_id,reply_markup=button_update_statistics_yes_SB)

# УРОВЕНЬ 3 "УЗНАТЬ ВЕРСИЮ КЛИЕНТА" - ФОРМИРОВАНИЕ СПИСКА И ВЫЗОВ ФУНКЦИИ:
@bot.chosen_inline_handler(func=lambda result_client_version: True)
# ФУНКЦИИ К КНОПКЕ ВЕРСИИ КЛИЕНТА
def send_text_version(result_client_version):
    """Функция по созданию списка версий и формирования ответа"""
    bot.add_poll_answer_handler
    url = API_ENDPOINT + '/contact_groups/'
    res = requests.get(url,auth=auth, headers=headers).json()
    global list_info_zero
    list_info_zero = []
    for person in res:
        list_name = person.get('name')
        list_version = person.get('description')
        if '---' in str(list_version):
            continue
        else:
            list_info_zero.append(list_name + ': ' + str(list_version))
    if result_client_version.text.lower() in str(list_info_zero).lower():
        counter = 0
        list = []
        for i in range (len(list_info_zero)):
            if result_client_version.text.lower() in str(list_info_zero[i]).lower():
                counter += 1
                list.append(list_info_zero[i])
        if counter == 1:
            button_version = types.InlineKeyboardMarkup()
            button_version_reply = types.InlineKeyboardButton(text= 'Запросить', callback_data='button_version')
            button_version.add(button_version_reply, row_width=1)
            back_from_result_client_version = types.InlineKeyboardButton(text= 'Назад', callback_data='button_clients_version')
            main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
            button_version.add(back_from_result_client_version, main_menu, row_width=2)
            question = (''.join(map(str, list)) + '\nХотите запросить версию другого клиента?')
            bot.send_message(result_client_version.from_user.id, text=question, reply_markup=button_version) 
        elif counter > 1:
            button_version = types.InlineKeyboardMarkup()
            button_version_reply = types.InlineKeyboardButton(text= 'Запросить', callback_data='button_version')
            button_version.add(button_version_reply, row_width=1)
            back_from_result_client_version = types.InlineKeyboardButton(text= 'Назад', callback_data='button_clients_version')
            main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
            button_version.add(back_from_result_client_version, main_menu, row_width=2)
            question = ('В списке клиентов обнаружено несколько совпадений c запросом "' + result_client_version.text + '":\n' + ('\n'.join(map(str, list))) + '\nХотите запросить версию другого клиента?')
            bot.send_message(result_client_version.from_user.id, text=question, reply_markup=button_version)
    else:
        button_version = types.InlineKeyboardMarkup()
        button_version_reply = types.InlineKeyboardButton(text= 'Запросить', callback_data='button_version')
        button_version.add(button_version_reply, row_width=1)
        back_from_result_client_version = types.InlineKeyboardButton(text= 'Назад', callback_data='button_clients_version')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_version.add(back_from_result_client_version, main_menu, row_width=2)
        question = 'Не найдено совпадений.\nХотите направить запрос ещё раз?'
        bot.send_message(result_client_version.from_user.id, text=question, reply_markup=button_version) 

# ФУНКЦИИ К КНОПКЕ СОЗДАНИЯ ТИКЕТОВ [общ.]
@bot.chosen_inline_handler(func=lambda result_GP_update_version: True)
def send_text_for_create_GP(result_GP_update_version):
    """Функция по обработке номера версии от пользака (G&P) и подтверждению темы"""
    global version_GP
    version_GP = result_GP_update_version.text 
    if '.' in version_GP:
        button_create_tickets_GP = types.InlineKeyboardMarkup()
        button_choise_yes_GP = types.InlineKeyboardButton(text= 'Да', callback_data='button_choise_yes_GP')
        button_create_tickets_GP.add(button_choise_yes_GP, row_width=1)
        back_from_result_GP_update_version= types.InlineKeyboardButton(text= 'Назад', callback_data='button_create_tickets_GP')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_create_tickets_GP.add(back_from_result_GP_update_version, main_menu, row_width=2)
        question = 'Просьба проверить, корректна ли тема будущей рассылки: "Обновление BoardMaps ' + str(version_GP)  + '". \n\n Для запуска процесса формирования тикетов,нажмите "Да". Если тема некорректна, нажмите "Главное меню".'
        bot.send_message(result_GP_update_version.from_user.id, text=question, reply_markup=button_create_tickets_GP)   
    else:
        button_create_tickets_GP = types.InlineKeyboardMarkup()
        back_from_result_GP_update_version= types.InlineKeyboardButton(text= 'Назад', callback_data='button_create_tickets_GP')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_create_tickets_GP.add(back_from_result_GP_update_version, main_menu, row_width=2)
        bot.send_message(result_GP_update_version.from_user.id, text='Запрос не соответствует условиям. Пожалуйста, вернитесь назад и повторите попытку.', reply_markup=button_create_tickets_GP) 

@bot.chosen_inline_handler(func=lambda result_SB_update_version: True) 

def send_text_for_create_SB(result_SB_update_version):
    """Функция по обработке номера версии от пользака (S&B) и подтверждению темы"""
    global version_SB
    version_SB = result_SB_update_version.text
    if '.' in version_SB:
        button_create_update_tickets_SB = types.InlineKeyboardMarkup()
        button_choise_yes_SB = types.InlineKeyboardButton(text= 'Да', callback_data='button_choise_yes_SB')
        button_create_update_tickets_SB.add(button_choise_yes_SB, row_width=1)
        back_from_result_SB_update_version = types.InlineKeyboardButton(text= 'Назад', callback_data='button_create_update_tickets_SB')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_create_update_tickets_SB.add(back_from_result_SB_update_version, main_menu, row_width=2)
        question = 'Просьба проверить, корректна ли тема будущей рассылки: "Обновление BoardMaps ' + str(version_SB)  + '". \n\n Для запуска процесса формирования тикетов,нажмите "Да". Если тема некорректна, нажмите "Главное меню".'
        bot.send_message(result_SB_update_version.from_user.id, text=question, reply_markup=button_create_update_tickets_SB) 
    else:
        button_create_update_tickets_SB = types.InlineKeyboardMarkup()
        back_from_result_SB_update_version = types.InlineKeyboardButton(text= 'Назад', callback_data='button_create_update_tickets_SB')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_create_update_tickets_SB.add(back_from_result_SB_update_version, main_menu, row_width=2)
        bot.send_message(result_SB_update_version.from_user.id, text='Запрос не соответствует условиям. Пожалуйста, вернитесь назад и повторите попытку.', reply_markup=button_create_update_tickets_SB) 

# ФУНКЦИИ К КНОПКЕ ФОРМИРОВАНИЯ СТАТИСТИКИ []
@bot.chosen_inline_handler(func=lambda result_SB_update_statistic: True) 

def send_text_for_stat_update_SB(result_SB_update_statistic):
    """Функция по обработке номера версии от пользака (S&B) и подтверждению темы"""
    global version_stat
    version_stat = result_SB_update_statistic.text 
    if '.' in version_stat:
        button_update_statistics_SB = types.InlineKeyboardMarkup()
        button_update_statistics_yes_SB = types.InlineKeyboardButton(text= 'Да', callback_data='button_update_statistics_yes_SB')
        button_update_statistics_SB.add(button_update_statistics_yes_SB, row_width=1)
        back_from_result_SB_update_statistic = types.InlineKeyboardButton(text= 'Назад', callback_data='button_update_statistics_SB')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_update_statistics_SB.add(back_from_result_SB_update_statistic, main_menu, row_width=2)
        question = 'Формируем статистику по версии релиза "' + str(version_stat)  + '"?'
        bot.send_message(result_SB_update_statistic.from_user.id, text=question, reply_markup=button_update_statistics_SB) 
    else:
        button_update_statistics_SB = types.InlineKeyboardMarkup()
        back_from_result_SB_update_statistic = types.InlineKeyboardButton(text= 'Назад', callback_data='button_update_statistics_SB')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_update_statistics_SB.add(back_from_result_SB_update_statistic, main_menu, row_width=2)
        bot.send_message(result_SB_update_statistic.from_user.id, text='Запрос не соответствует условиям. Пожалуйста, вернитесь назад и повторите попытку.', reply_markup=button_update_statistics_SB) 
   
def start_telegram_bot():
    """"Функция запуска телебота"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    try:
        print("Starting Telegram bot...")
        info_logger.info("Starting Telegram bot...")
        # запуск бота
        bot.infinity_polling()
    except requests.exceptions.ConnectionError as error_message:
        print(f"Error in Telegram bot: {error_message}")
        error_logger.error("Error in Telegram bot: %s", error_message)
    except telegram.error.TelegramError as error_message:
        print(f"Error in Telegram bot: {error_message}")
        error_logger.error("Error in Telegram bot: %s", error_message)
    except telebot.apihelper.ApiTelegramException as error_message:
        print(f"Error in Telegram bot: {error_message}")
        error_logger.error("Error in Telegram bot: %s", error_message)
    except Exception as error_message:
        print(f"Error in Telegram bot: {error_message}")
        error_logger.error("Error in Telegram bot: %s", error_message)
