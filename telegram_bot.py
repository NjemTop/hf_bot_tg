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
from docxtpl import DocxTemplate
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.header import Header
from writexml import create_xml
from YandexDocsMove import download_and_upload_pdf_files
from DistrMoveFromShare import move_distr_and_manage_share
from DataBase.database_result_update import upload_db_result
from ButtonClasses.button_clients import ButtonClients
from ButtonClasses.button_update import ButtonUpdate
from ButtonClasses.button_else_tickets import ButtonElseTickets
from Report_client.formirovanie_otcheta_tele2 import create_report_tele2

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
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
    DATA = json.load(file)

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

# Получение списка папок Яндекс.Диска
YANDEX_DISK_FOLDERS = DATA["YANDEX_DISK_FOLDERS"]

# Получаем значения из конфига для отправки рассылки
YANDEX_OAUTH_TOKEN = DATA["YANDEX_DISK"]["OAUTH-TOKEN"]
NEXTCLOUD_URL = DATA["NEXT_CLOUD"]["URL"]
NEXTCLOUD_USER = DATA["NEXT_CLOUD"]["USER"]
NEXTCLOUD_PASSWORD = DATA["NEXT_CLOUD"]["PASSWORD"]

# Создаем бота
bot=telebot.TeleBot(TOKEN)
# Переменная состояния для пользователей
user_states = {}

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
        button_SD_update = types.InlineKeyboardButton('Обновление версии', callback_data='button_SD_update')
        button_else_tickets = types.InlineKeyboardButton(text= 'Текущие тикеты', callback_data='button_else_tickets')
        main_menu.add(button_clients, button_SD_update, button_else_tickets,row_width=1)
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
            button_SD_update = types.InlineKeyboardButton('Обновление версии', callback_data='button_SD_update')
            button_else_tickets = types.InlineKeyboardButton(text= 'Текущие тикеты', callback_data='button_else_tickets')
            main_menu.add(button_clients, button_SD_update, button_else_tickets, row_width=1)
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
        button_clients = ButtonClients.button_clients()
        bot.send_message(message_clients.chat.id, 'Какую информацию хотите получить?', reply_markup=button_clients)
    else:
        bot.send_message(message_clients.chat.id,"К сожалению, у Вас отсутствует доступ.")
# Обработчик вызова /update
@bot.message_handler(commands=['update'])
def sd_sb_message(message_update):
    """Функция вызова кнопки /update"""
    if check_user_in_file(message_update.chat.id):
        button_SD_update = ButtonUpdate.button_SD_update()
        bot.send_message(message_update.chat.id, 'Выберите раздел:', reply_markup=button_SD_update)
    else:
        bot.send_message(message_update.chat.id,"К сожалению, у Вас отсутствует доступ.")

@bot.callback_query_handler(func=lambda call: call.data in ["mainmenu", "button_clients", "button_list_of_clients", "button_clients_version", "button_version_main_list", 
        "button_version", "cancel_button_version", "button_templates", "button_tele2", "button_psb", "button_rez", "button_pochtaR"])
# Добавляем подуровни к разделу Клиенты
def inline_button_clients(call):
    """Функция возврата в главное меню. Кнопки [Клиенты] / [Обновление версии]"""
    if call.data == "mainmenu":
        main_menu = types.InlineKeyboardMarkup()
        button_clients = types.InlineKeyboardButton(text= 'Клиенты', callback_data='button_clients')
        button_SD_update = types.InlineKeyboardButton(text= 'Обновление версии', callback_data='button_SD_update')
        button_else_tickets = types.InlineKeyboardButton(text= 'Текущие тикеты', callback_data='button_else_tickets')
        main_menu.add(button_clients, button_SD_update, button_else_tickets, row_width=1)
        bot.edit_message_text('Главное меню:', call.message.chat.id, call.message.message_id, reply_markup=main_menu)
# УРОВЕНЬ 2 "КЛИЕНТЫ". Добавляем кнопки [Список клиентов] / [Версии клиентов] / [Квартальные отчеты за период]
    elif call.data == "button_clients":
        button_clients = ButtonClients.button_clients()
        bot.edit_message_text('Какую информацию хотите получить?', call.message.chat.id, call.message.message_id,reply_markup=button_clients)
    # УРОВЕНЬ 3. Вызов кнопки "СПИСОК КЛИЕНТОВ"
    elif call.data == 'button_list_of_clients':
        button_list_of_clients = ButtonClients.button_list_of_clients()
        bot.edit_message_text('Для просмотра списка клиентов, пожалуйста, перейдите по ссылке:\nhttps://apps.boardmaps.ru/app/creg/page1-63bd167887eafa565f728b82.', call.message.chat.id, call.message.message_id,reply_markup=button_list_of_clients)
    # УРОВЕНЬ 3 "ВЕРСИИ КЛИЕНТОВ". Добавляем кнопки [Общий список версий] / [Узнать версию клиента]
    elif call.data == "button_clients_version":
        button_clients_version = ButtonClients.button_clients_version()
        bot.edit_message_text('Выберите раздел:', call.message.chat.id, call.message.message_id,reply_markup=button_clients_version)
    ### УРОВЕНЬ 4 "ОБЩИЙ СПИСОК ВЕРСИЙ". Добавляем ссылку на список
    elif call.data == "button_version_main_list":
        button_version_main_list = ButtonClients.button_version_main_list()
        bot.edit_message_text('Для просмотра списка версий клиентов, пожалуйста, перейдите по ссылке:\nhttps://apps.boardmaps.ru/app/creg/page1-63bd167887eafa565f728b82.', call.message.chat.id, call.message.message_id,reply_markup=button_version_main_list)
    ### УРОВЕНЬ 4 "УЗНАТЬ ВЕРСИЮ КЛИЕНТА"
    elif call.data == "button_version":  
        button_version = ButtonClients.button_version()
        bvers = bot.edit_message_text('Просьба отправить в чат сообщение с наименованием клиента, версию которого Вы хотите узнать.', call.message.chat.id, call.message.message_id,reply_markup=button_version)
        user_states[call.message.chat.id] = "waiting_for_client_name"
        bot.register_next_step_handler(bvers,send_text_version)
    elif call.data == "cancel_button_version":
        user_states[call.message.chat.id] = "canceled"
        # Возвращаемся на уровень выше
        button_clients_version = ButtonClients.button_clients_version()
        bot.edit_message_text('Выберите раздел:', call.message.chat.id, call.message.message_id,reply_markup=button_clients_version)
    # УРОВЕНЬ 3 "Квартальные отчеты за период". Добавляем кнопки [Теле2] / [ПСБ] / [РЭЦ] / [Почта России]
    elif call.data == "button_templates": 
        button_templates = ButtonClients.button_templates()
        bot.edit_message_text('Шаблон какого клиента необходимо выгрузить?', call.message.chat.id, call.message.message_id,reply_markup=button_templates)
    ### УРОВЕНЬ 4 "ТЕЛЕ2" 
    elif call.data == "button_tele2":
        bot.send_message(call.message.chat.id, text='Пожалуйста, ожидайте. По завершении процесса, в чат будет отправлен файл отчета.')
        client_report_id = 9
        create_report_tele2(client_report_id)
        with open("./Temp_report_tele2_final.docx", 'rb') as report_file:
            bot.send_document(call.message.chat.id, report_file)
    ### УРОВЕНЬ 4 "ПСБ"
    elif call.data == "button_psb":  
        bot.send_message(call.message.chat.id, text='Пожалуйста, ожидайте. По завершении процесса, в чат будет отправлен файл отчета.')
        client_report_id = 11
        create_report_tele2(client_report_id)
        with open("./Temp_report_PSB_final.docx", 'rb') as report_file:
            bot.send_document(call.message.chat.id, report_file)
    ### УРОВЕНЬ 4 "РЭЦ"
    elif call.data == "button_rez":  
        bot.send_message(call.message.chat.id, text='Пожалуйста, ожидайте. По завершении процесса, в чат будет отправлен файл отчета.')
        client_report_id = 12
        create_report_tele2(client_report_id)
        with open("./Temp_report_REC_final.docx", 'rb') as report_file:
            bot.send_document(call.message.chat.id, report_file)
        # setup_script = 'Скрипт_формирования_отчёта_клиента_РЭЦ.ps1'
        # try:
        #     result_rez = subprocess.run(["pwsh", "-File", setup_script],stdout=sys.stdout, check=True)
        #     # Записываем в лог информацию о пользователе, сформировавшем отчет
        #     xml_data = None
        #     with open('data.xml', encoding='utf-8-sig') as file_data:
        #         xml_data = file_data.read()
        #         root = ET.fromstring(xml_data)
        #         chat_id = root.find('chat_id').text
        #         if str(call.message.chat.id) == chat_id:
        #             name = root.find('header_footer/name').text
        #             info_logger.info("Пользователь: %s сформировал отчет.", name)
        # except subprocess.CalledProcessError as error_message:
        #     error_logger.error("Ошибка при запуске скрипта %s: %s", setup_script, error_message)
        #     bot.send_message(call.message.chat.id, text='Произошла ошибка при формировании отчета.')
        # else:
        #     if platform.system() == 'Windows':
        #         # формируем путь к файлу отчета в директории AppData\Local
        #         report_path = os.path.join(local_appdata_path, 'Отчёт_клиента_РЭЦ.docx').replace('\\', '/')
        #     elif platform.system() == 'Linux':
        #         report_path = os.path.join(local_appdata_path, 'Отчёт_клиента_РЭЦ.docx')
        #     with open(report_path, 'rb') as report_file:
        #         bot.send_document(call.message.chat.id, report_file)
    ### УРОВЕНЬ 4 "ПОЧТА РОССИИ" ///////////////////////////////////////// в работе
    elif call.data == "button_pochtaR":
        bot.send_message(call.message.chat.id, text='Пожалуйста, ожидайте. По завершении процесса, в чат будет отправлен файл отчета.')
        client_report_id = 13
        create_report_tele2(client_report_id)
        with open("./Temp_report_PR_final.docx", 'rb') as report_file:
            bot.send_document(call.message.chat.id, report_file)
# Добавляем подуровни к разделу Обновление версии
@bot.callback_query_handler(func=lambda call: call.data in ["button_SD_update", "button_release", "button_choise_yes", "cancel_SD_update", "button_localizable", "button_AFK_localizable", "button_reply_request", "button_reply_request_yes", "button_update_statistics", "cancel_SD_update_statistics", "button_update_statistics_yes"])
def inline_button_SD_update(call):
    if call.data == "button_SD_update":
        """ УРОВЕНЬ 2: ОБНОВЛЕНИЕ ВЕРСИИ. Добавляем кнопки [ Отправить рассылку | Повторный запрос сервисного окна (G&P) | Статистика по тикетам ] """
        button_SD_update = ButtonUpdate.button_SD_update()
        bot.edit_message_text('Выберите раздел:', call.message.chat.id, call.message.message_id,reply_markup=button_SD_update)
    elif call.data == "button_release":
        """ УРОВЕНЬ 3: ОБНОВЛЕНИЕ ВЕРСИИ. """
        button_release = ButtonUpdate.button_release()
        ask_version_update = bot.edit_message_text('Пожалуйста, напишите в чат номер версии. Пример: 2.60.', call.message.chat.id, call.message.message_id,reply_markup=button_release)
        user_states[call.message.chat.id] = "waiting_for_client_name"
        bot.register_next_step_handler(ask_version_update, send_text_for_create)
    elif call.data == "button_choise_yes":
        """ ДОПОЛНИТЕЛЬНО: при нажатии кнопки ДА по корректности темы в рассылке тикетов по обновлению"""
        support_response_id = get_header_footer_id(call.message.chat.id)
        if support_response_id is None:
            bot.edit_message_text('У Вас нет прав на отправку рассылки. Пожалуйста, обратитесь к администратору.', call.message.chat.id, call.message.message_id)
            return
        bot.edit_message_text('Отлично! Начат процесс отправки рассылки. Пожалуйста, ожидайте.', call.message.chat.id, call.message.message_id)
        setup_script = Path('Automatic_email.ps1')
        try:
            name_who_run_script = get_name_by_chat_id(call.message.chat.id)
            # Замена {version_SB} на соответствующую версию и добавление обновленных папок в новый список
            updated_folder_paths = [folder_path.format(version_SB=version_release) for folder_path in YANDEX_DISK_FOLDERS]
            # Запускаем процесс перемещения предыдущей папки документации в другую директорию и создания и заполнения новой папки документации
            info_logger.info("Запуск скрипта по перемещению документации, пользователем: %s, номер версии рассылки: %s", name_who_run_script, version_release)
            download_and_upload_pdf_files(YANDEX_OAUTH_TOKEN, NEXTCLOUD_URL, NEXTCLOUD_USER, NEXTCLOUD_PASSWORD, version_release, updated_folder_paths)
            # Запускаем процесс перемещения дистрибутива на NextCloud
            info_logger.info("Запуск скрипта по перемещению дистрибутива, пользователем: %s, номер версии рассылки: %s", name_who_run_script, version_release)
            move_distr_and_manage_share(version_release)
            info_logger.info("Запуск скрипта по отправке рассылки, пользователем: %s, номер версии рассылки: %s", name_who_run_script, version_release)
            release_result = subprocess.run(["pwsh", "-File", setup_script, str(version_release), str(support_response_id)], stdout=subprocess.PIPE, check=True).stdout.decode('utf-8')
            upload_db_result(version_release, release_result)
        except subprocess.CalledProcessError as error_message:
            error_logger.error("Ошибка запуска скрипта по отправке рассылки: %s", error_message)
            print("Ошибка запуска скрипта по отправке рассылки:", error_message)
        # Записываем вывод из терминала PowerShell, чтобы потом сформировать в файл и отправить в телегу
        with open(f'/app/logs/report_send({version_release}).log', 'a+', encoding='utf-8-sig') as file_send:
            file_send.write(release_result)
            file_send.seek(0)  # перематываем указатель в начало файла
            # Отправляем вывод всего результата в телеграмм бота
            bot.send_document(call.message.chat.id, file_send)
        button_choise_yes = types.InlineKeyboardMarkup()
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_choise_yes.add(main_menu, row_width=2)
        info_logger.info("Рассылка клиентам успешно отправлена.")
        bot.send_message(call.from_user.id, text='Процесс отправки рассылки завершен. Файл с результатами отправлен на почту.', reply_markup=button_choise_yes)   
        try:
            os.remove(f'/app/logs/report_send({version_release}).log')
        except FileNotFoundError as error_message:
            error_logger.error('Файл не найден: %s', error_message)
            print('Файл не найден: %s', error_message)
        except PermissionError as error_message:
            error_logger.error('Недостаточно прав для удаления файла: %s', error_message)
            print('Недостаточно прав для удаления файла: %s', error_message)
        except OSError as error_message:
            error_logger.error('Ошибка при удалении файла: %s', error_message)
            print('Ошибка при удалении файла: %s', error_message)
    elif call.data == "cancel_SD_update":
        user_states[call.message.chat.id] = "canceled"
        # Возвращаемся на уровень выше
        button_SD_update = ButtonUpdate.button_SD_update()
        bot.edit_message_text('Выберите раздел:', call.message.chat.id, call.message.message_id,reply_markup=button_SD_update)
    elif call.data == "button_localizable":
        button_localizable = ButtonUpdate.button_localizable()
        bot.edit_message_text('Выберите раздел:', call.message.chat.id, call.message.message_id,reply_markup=button_localizable)
    elif call.data == "button_AFK_localizable":
        button_AFK_localizable = ButtonUpdate.button_AFK_localizable()
        bot.edit_message_text('Выберите раздел:', call.message.chat.id, call.message.message_id,reply_markup=button_AFK_localizable)
    elif call.data == "button_reply_request":
        """ УРОВЕНЬ 3: ПОВТОРНЫЙ ЗАПРОС СЕРВИСНОГО ОКНА" (G&P) """
        button_reply_request = ButtonUpdate.button_reply_request()
        bot.edit_message_text('Вы собираетесь запустить повторную отправку запросов на предоставление сервисного окна для Gold и Platinum клиентов. Подтвердите свой выбор.', call.message.chat.id, call.message.message_id,reply_markup=button_reply_request)
    elif call.data == "button_reply_request_yes":
        """ УРОВЕНЬ 5: при нажатии кнопки ДА по повторной отправке запроса сервисного окна для G&P """
        bot.send_message(call.message.chat.id, text='Процесс запущен, ожидайте.')
        setup_script = 'Auto_ping_test.ps1'
        subprocess.run(["pwsh", "-File", setup_script],stdout=sys.stdout)
        bot.send_message(call.message.chat.id, text='Процесс завершен. Повторные запросы направлены клиентам.')
    elif call.data == "button_update_statistics":
        """ УРОВЕНЬ 3: СТАТИСТИКА ПО ОБНОВЛЕНИЮ """
        button_update_statistics = ButtonUpdate.button_update_statistics()
        ask_stat_number_version = bot.edit_message_text('Введите номер версии, по которой необходимо сформировать статистику. Например: 2.60.', call.message.chat.id, call.message.message_id, reply_markup=button_update_statistics)
        user_states[call.message.chat.id] = "waiting_for_client_name"
        bot.register_next_step_handler(ask_stat_number_version, send_text_for_stat_update)
    elif call.data == "cancel_SD_update_statistics":
        user_states[call.message.chat.id] = "canceled"
        # Возвращаемся на уровень выше
        button_SD_update = ButtonUpdate.button_SD_update()
        bot.edit_message_text('Выберите раздел:', call.message.chat.id, call.message.message_id,reply_markup=button_SD_update)
    elif call.data == "button_update_statistics_yes":
        """ ДОПОЛНИТЕЛЬНО: при нажатии кнопки ДА по формированию статистики по тикетам update """
        bot.edit_message_text('Отлично! Произвожу расчеты. Пожалуйста, ожидайте.', call.message.chat.id, call.message.message_id)
        setup_script = Path('Ticket_Check_update_statistics.ps1')
        try:
            result = subprocess.run(["pwsh", "-File", setup_script,str(version_stat) ],stdout=sys.stdout, check=True)
            name_who_run_script = get_name_by_chat_id(call.message.chat.id)
            info_logger.info("Запуск скрипта по формированию статистики, пользователем: %s", name_who_run_script)
        except subprocess.CalledProcessError as error_message:
            error_logger.error("Ошибка запуска скрипта по формированию статистики: %s", error_message)
        bot.edit_message_text(('Статистика по обновлению версии  "' + str(version_stat) + '" :\n' + str(result.stdout)), call.message.chat.id, call.message.message_id,reply_markup=button_SD_update)
# ФУНКЦИИ К КНОПКЕ СОЗДАНИЯ ТИКЕТОВ [общ.]
@bot.chosen_inline_handler(func=lambda result_update_version: True)
def send_text_for_create(result_update_version):
    """Функция по обработке номера версии от пользака и подтверждению темы"""
    user_state = user_states.get(result_update_version.chat.id)
    if user_state == "waiting_for_client_name":
        global version_release
        version_release = result_update_version.text 
        if '.' in version_release:
            button_release, question = ButtonUpdate.button_release(version_release)
            bot.send_message(result_update_version.from_user.id, text=question, reply_markup=button_release)   
        else:
            button_release = types.InlineKeyboardMarkup()
            back_from_result_update_version= types.InlineKeyboardButton(text= 'Назад', callback_data='button_release')
            main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
            button_release.add(back_from_result_update_version, main_menu, row_width=2)
            bot.send_message(result_update_version.from_user.id, text='Запрос не соответствует условиям. Пожалуйста, вернитесь назад и повторите попытку.', reply_markup=button_release) 
    else:
        pass

# ФУНКЦИИ К КНОПКЕ ФОРМИРОВАНИЯ СТАТИСТИКИ []
@bot.chosen_inline_handler(func=lambda button_update_statistics: True)
def send_text_for_stat_update(result_update_statistic):
    """Функция по обработке номера версии от пользака и подтверждению темы"""
    user_state = user_states.get(result_update_statistic.chat.id)
    if user_state == "waiting_for_client_name":
        global version_stat
        version_stat = result_update_statistic.text 
        if '.' in version_stat:
            button_update_statistics1, question = ButtonUpdate.button_update_statistics1(version_stat)
            bot.send_message(result_update_statistic.from_user.id, text=question, reply_markup=button_update_statistics1) 
        else:
            button_update_statistics = types.InlineKeyboardMarkup()
            back_from_result_update_statistic = types.InlineKeyboardButton(text= 'Назад', callback_data='button_SD_update')
            main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
            button_update_statistics.add(back_from_result_update_statistic, main_menu, row_width=2)
            bot.send_message(result_update_statistic.from_user.id, text='Запрос не соответствует условиям. Пожалуйста, вернитесь назад и повторите попытку.', reply_markup=button_update_statistics) 
    else:
        pass

# УРОВЕНЬ 3 "УЗНАТЬ ВЕРСИЮ КЛИЕНТА" - ФОРМИРОВАНИЕ СПИСКА И ВЫЗОВ ФУНКЦИИ:
@bot.chosen_inline_handler(func=lambda result_client_version: True)
# ФУНКЦИИ К КНОПКЕ ВЕРСИИ КЛИЕНТА
def send_text_version(result_client_version):
    """Функция по созданию списка версий и формирования ответа"""
    user_state = user_states.get(result_client_version.chat.id)
    if user_state == "waiting_for_client_name":
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
                button_version = ButtonClients.button_version_answer()
                question = (''.join(map(str, list)) + '\nХотите запросить версию другого клиента?')
                bot.send_message(result_client_version.from_user.id, text=question, reply_markup=button_version) 
            elif counter > 1:
                button_version = ButtonClients.button_version_answer()
                question = ('В списке клиентов обнаружено несколько совпадений c запросом "' + result_client_version.text + '":\n' + ('\n'.join(map(str, list))) + '\nХотите запросить версию другого клиента?')
                bot.send_message(result_client_version.from_user.id, text=question, reply_markup=button_version)
        else:
            button_version = ButtonClients.button_version_answer()
            question = 'Не найдено совпадений.\nХотите направить запрос ещё раз?'
            bot.send_message(result_client_version.from_user.id, text=question, reply_markup=button_version) 
    else:
        pass


@bot.callback_query_handler(func=lambda call: call.data in ["button_else_tickets", "button_else_tickets_stat", "button_one_ticket_stat"])
def inline_button_else_tickets(call):
    """УРОВЕНЬ 2 "ОСТАЛЬНЫЕ ТИКЕТЫ"""
    if call.data == "button_else_tickets":
        button_else_tickets = ButtonElseTickets.get_info_else_tickets()
        bot.edit_message_text('Выберите раздел:', call.message.chat.id, call.message.message_id, reply_markup=button_else_tickets)
    ### УРОВЕНЬ 3. Статистика по остальным тикетам
    elif call.data == "button_else_tickets_stat":
        button_else_tickets_stat, all_ticket_count, new_ticket, without_support_answer, without_client_ansrew = ButtonElseTickets.button_else_tickets_stat()
        bot.edit_message_text('Всего "в работе": ' + all_ticket_count + '. Из них:\n- Новые без исполнителя: ' + new_ticket + '\n- Без ответа от саппорта: ' + without_support_answer + '\n- Без ответа от клиента: ' + without_client_ansrew, call.message.chat.id, call.message.message_id, reply_markup=button_else_tickets_stat)
    ### УРОВЕНЬ 3. Статистика по отдельному тикету
    elif call.data == "button_one_ticket_stat":
        button_one_ticket_stat = ButtonElseTickets.get_info_else_tickets_stat()
        info_about_ticket = bot.edit_message_text('Напишите номер тикета. Например: 5886', call.message.chat.id, call.message.message_id, reply_markup=button_one_ticket_stat)
        bot.register_next_step_handler(info_about_ticket, get_number_else_ticket)
    elif call.data == "cancel_else_tickets":
        user_states[call.message.chat.id] = "canceled"
        # Возвращаемся на уровень выше
        button_else_tickets = ButtonElseTickets.get_info_one_ticket_stat()
        bot.edit_message_text('Выберите раздел:', call.message.chat.id, call.message.message_id,reply_markup=button_else_tickets)

@bot.chosen_inline_handler(func=lambda get_number_else_ticket: True)
def get_number_else_ticket(result_number_else_ticket):
    user_state = user_states.get(result_number_else_ticket.chat.id)
    if user_state == "waiting_for_client_name":
        button_else_tickets = ButtonElseTickets.button_else_tickets()
        bot.send_message(result_number_else_ticket.from_user.id, text="Скоро здесь будет инфо тикета.", reply_markup=button_else_tickets).text.lower()
    else:
        pass


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
