import json
import logging
from flask import request, Response, jsonify
import emoji
from Web_Server.function import parse_json_message
from Web_Server.web_config import CONFIG_FILE
from System_func.send_telegram_message import Alert
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов для нашего файла с классами
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

# Создаем объект класса Alert
alert = Alert()

def handler_get_create_ticket():
        """Функция обработки GET запросов по URL"""
        ip_address = f"Request from {request.remote_addr}: {request.url}"
        user_agent = request.headers.get('User-Agent')
        user_who = f'User-Agent: {user_agent}'
        web_info_logger.info('Кто-то зашёл на сайт c IP-адреса: %s', ip_address)
        web_info_logger.info('Его данные подключения: %s', (user_who,))
        return Response('Этот URL для получения вэбхуков(создание)', mimetype='text/plain')

def handler_post_create_ticket():
        """Функция обработки создания тикета из HappyFox"""
        try:
            # message = request.data.decode('utf-8')
            # web_info_logger.info("Содержимое запроса: %s", message)

            json_data = request.get_json()
            if not json_data:
                web_error_logger.error("JSON не найден в запросе.")
                return Response("JSON не найден в запросе.", status=400)

            # # парсим JSON-строку
            # json_data, error = parse_json_message(message)
            # if error:
            #     return error, 400
            # находим значения для ключей
            display_id = json_data.get("display_id")
            subject = json_data.get("subject")
            priority_name = json_data.get("priority_name")
            agent_ticket_url = json_data.get("agent_ticket_url")
            client_name = json_data.get("client_details", {}).get("name")
            client_email = json_data.get("client_details", {}).get("email")
            # отправляем сообщение в телеграм-бот
            new_ticket_message = (
                f"{emoji.emojize(':tired_face:')} Новый тикет: "
                f'<a href="{agent_ticket_url}">{display_id}</a>\n'
                f"{emoji.emojize(':man_tipping_hand:')} Тема: {subject}\n"
                f"{emoji.emojize(':man_mechanic:')} Автор: {client_name} ({client_email})\n"
                f"{emoji.emojize(':high_voltage:')} Приоритет: {priority_name}\n"
            )
            # открываем файл и загружаем данные
            with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
                data = json.load(file)
            # извлекаем значения GROUP_ALERT_NEW_TICKET из SEND_ALERT
            alert_chat_id = data['SEND_ALERT']['GROUP_ALERT_NEW_TICKET']
            alert.send_telegram_message(alert_chat_id, new_ticket_message)
            web_info_logger.info('Направлена информация в группу о созданном тикете %s', display_id)
            # Отправляем ответ о том, что всё принято и всё хорошо
            return "OK", 201
        except Exception as error_message:
            web_error_logger.error("Ошибка при обработке создания тикета: %s", str(error_message))
            return Response("Ошибка на сервере", status=500)
