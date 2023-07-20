import requests
import json
import emoji

# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"

# Читаем данные из файла
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
    DATA = json.load(file)

# Получаем значение ключа BOT_TOKEN в TELEGRAM_SETTINGS
BOT_TOKEN = DATA['TELEGRAM_SETTINGS']['BOT_TOKEN']

def send_telegram_message(alert_chat_id, alert_text):
    """
    Отправляет сообщение в телеграм-бот.
    На себя принимает два аргумента:
    alert_chat_id - чат айди, куда мы будем отправлять сообщение,
    alert_text - текст сообщения, которое мы хотим отправить.
    """
    # Адрес для отправи сообщение напрямую через API Telegram
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    # Задаём стандартный заголовок отправки
    headers_server = {'Content-type': 'application/json'}
    # Создаём тело запроса, которое мы отправляем
    data = {
        'chat_id': alert_chat_id,
        'text': f'{alert_text}',
        'parse_mode': 'Markdown'
    }
    # Отправляем запрос через наш бот
    response = requests.post(url, headers=headers_server, data=json.dumps(data), timeout=30)
    # Добавляем логгирование для отладки
    print(response)


ticket_id = "BCS00006280"
subject = 'Просим оказать содействие с установкой сертификата.'
client_name = 'Дмитрий Попов'
priority_name = 'Medium'
assignee_name = 'Oleg Eliseev'
assigned_name = 'Oleg Eliseev'
client_email = 'Email'
company = 'Тестовое название компании'
status = 'In Progress'
last_message_time = '07:41, 11-07-2023'
truncated_message = 'Тут большое сообщение в ограничение 500 символов'
agent_ticket_url = 'https://boardmaps.happyfox.com/staff/ticket/6280'
ping_ticket_message = (
    f"{emoji.emojize(':double_exclamation_mark:')} Тикет [{ticket_id}]({agent_ticket_url}) без ответа *три* часа.\n"
    f"{emoji.emojize(':man_tipping_hand:')}Тема: {subject}\n"
    f"{emoji.emojize(':man_mechanic:')}Автор: {client_name}\n"
    f"{emoji.emojize(':high_voltage:')}Приоритет: {priority_name}\n"
    f"{emoji.emojize(':clown_face:')} Назначен: {assignee_name}\n"
)

ticket_message = (
    f"{emoji.emojize(':hand_with_fingers_splayed:')}Новое сообщение в тикете "
    f"[{ticket_id}]({agent_ticket_url})\n"
    f"{emoji.emojize(':man_tipping_hand:')}Тема: {subject}\n"
    f"{emoji.emojize(':man_mechanic:')}Автор: {client_name}\n"
    f"{emoji.emojize(':high_voltage:')}Приоритет: {priority_name}\n"
    f"{emoji.emojize(':man_technologist:')}Назначен: {assignee_name}\n"
)

new_ticket_message = (
    f"{emoji.emojize(':tired_face:')}Новый тикет: "
    f"[{ticket_id}]({agent_ticket_url})\n"
    f"{emoji.emojize(':man_tipping_hand:')}Тема: {subject}\n"
    f"{emoji.emojize(':man_mechanic:')}Автор: {client_name} ({client_email})\n"
    f"{emoji.emojize(':high_voltage:')}Приоритет: {priority_name}\n"
)

# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"

# Читаем данные из файла
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
    DATA = json.load(file)

alert_chat_id = DATA['SEND_ALERT']['GROUP_RELEASE']

print(alert_chat_id)

version_release = 2.65

alert_message_for_release = (
    f"{emoji.emojize(':check_mark_button:')} "
    f"{emoji.emojize(':check_mark_button:')} "
    f"{emoji.emojize(':check_mark_button:')}\n\n"
    f"Рассылка версии *BM {version_release}* успешно отправлена!\n\n"
    f"Отчёт по рассылки можно посмотреть в разделе\n"
    f'"Информация об отправке релиза" здесь:\n'
    f"https://creg.boardmaps.ru/\n\n"
    f"Всем спасибо!"
)

ticket_info = (
            f"{emoji.emojize(':eyes:')} Тема: {subject}\n"
            f"{emoji.emojize(':department_store:')} Компания: {company}\n"
            f"{emoji.emojize(':credit_card:')} Статус: {status}\n"
            f"{emoji.emojize(':disguised_face:')} Назначен: {assigned_name}\n"
            f"{emoji.emojize(':eight_o’clock:')} Дата: {last_message_time}\n"
            f"{emoji.emojize(':envelope_with_arrow:')} Сообщение: {truncated_message}"
        )

send_telegram_message(320851571, ticket_info)
