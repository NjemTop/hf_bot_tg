from docxtpl import DocxTemplate
import locale
import requests
from datetime import datetime
import subprocess, sys
from formirovanie_otcheta_tele2 import list_of_rows

# Прописываем id клиента для ссылки на отчет
client_report_id = 13
## Создаем файл и делаем русскую локализацию для даты
docx = DocxTemplate("Temp_report_PR.docx")
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
### Авторизация в HappyFox
# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"
# Открываем файл и загружаем данные
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
    data_config = json.load(f)
# Извлекаем значения API_KEY и API_SECRET
API_ENDPOINT = data_config['HAPPYFOX_SETTINGS']['API_ENDPOINT']
API_KEY = data_config['HAPPYFOX_SETTINGS']['API_KEY']
API_SECRET = data_config['HAPPYFOX_SETTINGS']['API_SECRET']
# Прохождение кол-ва страниц по url первой страницы
headers = {'Content-Type': 'application/json'}
param = {'period_type' : 'srp'}
url_0 = f"https://boardmaps.happyfox.com/api/1.1/json/report/{client_report_id}/tabulardata/?size=50&page=1"
res_0 = requests.get(url_0, auth=(API_KEY, API_SECRET), headers=headers, params=param).json()
# Находим кол-во страниц
pages_len = res_0.get('page_count')
### ЗАПОЛНЯЕМ ШАПКУ
## Находим дату (Отчет об оказанных услугах ОТ [___] )
today = datetime.now().date().strftime('%d %B %Y')
# start_date
# end_date

# Номера тикетов для вывода в файл
all_tickets_id_list = list_of_rows(client_report_id, pages_len)


# Нарушение сроков общее all_sla



## перебираем тикеты и вытягиваем инфу по ним
def info_from_ticket_id(ticket_id):
    url = f"https://boardmaps.happyfox.com/api/1.1/json/ticket/{ticket_id}"
    res = requests.get(url, auth=auth, headers=headers, params=param).json()
    # Полный номер заявки
    display_id = res.get('display_id')
    # Дата создания тикета
    date_ticket_start_0 = res.get('created_at')
    datetime_object_start = datetime.strptime(date_ticket_start_0, '%Y-%m-%d %H:%M:%S')
    date_ticket_start = str(datetime_object_start.strftime('%d.%m.%Y'))
    # Дата закрытия тикета
    date_ticket_close_0 = res.get('last_modified')
    datetime_object_close = datetime.strptime(date_ticket_close_0, '%Y-%m-%d %H:%M:%S')
    date_ticket_close = str(datetime_object_close.strftime('%d.%m.%Y')) 
    # Вид запроса 
    request_type = 'request_type'
    # Тема 
    subject = (res.get('subject')).replace('RE: ', '').replace('FW: ', '')
    # Заявитель
    client_user = res.get('user').get('name')
    # Статус 
    status_eng = res.get('status').get('name')
    if status_eng == 'Closed':
        status = 'Закрыт'
    else:
        status = 'В работе'
    # Время решения тикета + конвертация в минуты fact_resp_time
    setup_script = 'Response_time_2.ps1'
    result_time = subprocess.run([ "pwsh", "-File", setup_script, str(ticket_id) ], capture_output=True, text=True)
    fact_resp_time = str(result_time.stdout).rstrip()
    # Приоритет
    priority_eng = res.get('priority').get('name')
    if priority_eng == 'Low':
        priority = 'Низкий'
    elif priority_eng == 'Medium':
        priority = 'Средний'
    elif priority_eng == 'High':
        priority = 'Высокий'
    elif priority_eng == 'Critical':
        priority = 'Критический'
    else:
        priority = 'Не установлен'

    return display_id, date_ticket_start, date_ticket_close, request_type, subject, client_user, status, fact_resp_time, priority

# Формируем общий список для добавления в файл
table_rows = []
# Задаем порядковый номер строки
num = 0
# Счетчик общего кол-ва запросов
len_tickets_list_28 = 0
# Счетчик общего кол-ва инцедентов
len_tickets_list_27 = 0
# Счетчики на "Зарегистрировано в отчетный период Запросы на обслуживание" по приоритетам
len_tickets_list_28_H = 0
len_tickets_list_28_M = 0
len_tickets_list_28_L = 0
# Счетчики на "Зарегистрировано в отчетный период Инциденты" по приоритетам
len_tickets_list_27_C = 0
len_tickets_list_27_H = 0
len_tickets_list_27_M = 0
len_tickets_list_27_L = 0

# Перебираем каждый тикет и создаем список (строку в таблице word)
new_tickets_list = []
for ticket_id in all_tickets_id_list:
    # получаем результат функции с данными по тикету
    display_id, date_ticket_start, date_ticket_close, request_type, subject, client_user, status, fact_resp_time, priority = info_from_ticket_id(ticket_id)
    num += 1
    # добавляем соответствие и добавляем список в table_rows
    table_rows.append({'num': num, 'display_id' : display_id, 'date_ticket_start' : date_ticket_start, 'date_ticket_close' : date_ticket_close, 'request_type' : request_type,
    'subject' : subject, 'client_user' : client_user, 'status' : status, 'fact_resp_time' : fact_resp_time, 'priority' : priority})

    ## Определение данных по полученным в отчетный период тикетам
    url_new = f"https://boardmaps.happyfox.com/api/1.1/json/ticket/{ticket_id}"
    param_new = {'period_type' : 'cr'}
    res_new = requests.get(url_new, auth=auth, headers=headers, params=param_new).json()
    # Зарегистрировано в отчетный период всего 
    len_tickets_list = len(all_tickets_id_list)
    request_type_find_id = res_new.get('custom_fields')
    request_type = ''
    for a in range(len(request_type_find_id)):
        priority_27_28 = res_new.get('priority').get('name')
        # Зарегистрировано в отчетный период Запросы на обслуживание
        if request_type_find_id[a].get('id') == 28:
            len_tickets_list_28 += 1
            new_tickets_list.append(ticket_id)
            # Зарегистрировано в отчетный период Запросы на обслуживание Высокий
            if priority_27_28 == 'High':
                len_tickets_list_28_H += 1
            # Зарегистрировано в отчетный период Запросы на обслуживание Средний
            elif priority_27_28 == 'Medium':
                len_tickets_list_28_M += 1
            # Зарегистрировано в отчетный период Запросы на обслуживание Низкий
            elif priority_27_28 == 'Low':
                len_tickets_list_28_L += 1
        # Зарегистрировано в отчетный период Инциденты len_tickets_list_27
        elif request_type_find_id[a].get('id') == 27:
            len_tickets_list_27 += 1
            new_tickets_list.append(ticket_id)
            # Зарегистрировано в отчетный период Инциденты Критичный len_tickets_list_27_C
            if priority_27_28 == 'Critical':
                len_tickets_list_27_C += 1
            # Зарегистрировано в отчетный период Инциденты Высокий len_tickets_list_27_H
            elif priority_27_28 == 'High':
                len_tickets_list_27_H += 1
            # Зарегистрировано в отчетный период Инциденты Средний len_tickets_list_27_M 
            elif priority_27_28 == 'Medium':
                len_tickets_list_27_M += 1
            # Зарегистрировано в отчетный период Инциденты Низкий len_tickets_list_27_L
            elif priority_27_28 == 'Low':
                len_tickets_list_27_L += 1
        else:
            continue
#print(len_tickets_list_27, len_tickets_list_27_C, len_tickets_list_27_H, len_tickets_list_27_M, len_tickets_list_27_L)
#print(len_tickets_list_28, len_tickets_list_28_H, len_tickets_list_28_M, len_tickets_list_28_L)

    ## Определение данных по всем тикетам
    url = f"https://boardmaps.happyfox.com/api/1.1/json/ticket/{ticket_id}"
    param = {'period_type' : 'srp'}
    res = requests.get(url, auth=auth, headers=headers, params=param).json()
    if ticket_id in new_tickets_list:
        print('Уже было')
    # Перешло с прошлого периода всего len_tickets_list_old 
    # Перешло с прошлого периода Запросы на обслуживание len_tickets_list_28_old 
    # Перешло с прошлого периода Запросы на обслуживание Высокий len_tickets_list_28_H_old
    # Перешло с прошлого периода Запросы на обслуживание Средний len_tickets_list_28_M_old
    # Перешло с прошлого периода Запросы на обслуживание Низкий len_tickets_list_28_L_old
    # Перешло с прошлого периода Инциденты len_tickets_list_27_old 
    # Перешло с прошлого периода Инциденты Критичный len_tickets_list_27_C_old
    # Перешло с прошлого периода Инциденты Высокий len_tickets_list_27_H_old
    # Перешло с прошлого периода Инциденты Средний len_tickets_list_27_M_old
    # Перешло с прошлого периода Инциденты Низкий len_tickets_list_27_L_old 
    # Выполнено в срок всего len_tickets_list_1
    # Выполнено в срок Запросы на обслуживание len_tickets_list_28_1
    # Выполнено в срок Запросы на обслуживание Высокий len_tickets_list_28_H_1
    # Выполнено в срок Запросы на обслуживание Средний len_tickets_list_28_M_1
    # Выполнено в срок Запросы на обслуживание Низкий len_tickets_list_28_L_1
    # Выполнено в срок Инциденты len_tickets_list_27_1
    # Выполнено в срок Инциденты Критичный len_tickets_list_27_C_1
    # Выполнено в срок Инциденты Высокий len_tickets_list_27_H_1
    # Выполнено в срок Инциденты Средний len_tickets_list_27_M_1
    # Выполнено в срок Инциденты Низкий len_tickets_list_27_L_1

    # Закрыто с нарушением срока всего len_tickets_list_2
    # Закрыто с нарушением срока Запросы на обслуживание len_tickets_list_28_2
    # Закрыто с нарушением срока Запросы на обслуживание Высокий len_tickets_list_28_H_2
    # Закрыто с нарушением срока Запросы на обслуживание Средний len_tickets_list_28_M_2
    # Закрыто с нарушением срока Запросы на обслуживание Низкий len_tickets_list_28_L_2
    # Закрыто с нарушением срока Инциденты len_tickets_list_27_2
    # Закрыто с нарушением срока Инциденты Критичный len_tickets_list_27_C_2
    # Закрыто с нарушением срока Инциденты Высокий len_tickets_list_27_H_2
    # Закрыто с нарушением срока Инциденты Средний len_tickets_list_27_M_2
    # Закрыто с нарушением срока Инциденты Низкий len_tickets_list_27_L_2

    # Выполняется без нарушения срока всего len_tickets_list_3
    # Выполняется без нарушения срока Запросы на обслуживание len_tickets_list_28_3
    # Выполняется без нарушения срока Запросы на обслуживание Высокий len_tickets_list_28_H_3
    # Выполняется без нарушения срока Запросы на обслуживание Средний len_tickets_list_28_M_3
    # Выполняется без нарушения срока Запросы на обслуживание Низкий len_tickets_list_28_L_3
    # Выполняется без нарушения срока Инциденты len_tickets_list_27_3
    # Выполняется без нарушения срока Инциденты Критичный len_tickets_list_27_C_3
    # Выполняется без нарушения срока Инциденты Высокий len_tickets_list_27_H_3
    # Выполняется без нарушения срока Инциденты Средний len_tickets_list_27_M_3
    # Выполняется без нарушения срока Инциденты Низкий len_tickets_list_27_L_3

    # Выполняется с нарушением срока всего len_tickets_list_4
    # Выполняется с нарушением срока Запросы на обслуживание len_tickets_list_28_4
    # Выполняется с нарушением срока Запросы на обслуживание Высокий len_tickets_list_28_H_4
    # Выполняется с нарушением срока Запросы на обслуживание Средний len_tickets_list_28_M_4
    # Выполняется с нарушением срока Запросы на обслуживание Низкий len_tickets_list_28_L_4
    # Выполняется с нарушением срока Инциденты len_tickets_list_27_4
    # Выполняется с нарушением срока Инциденты Критичный len_tickets_list_27_C_4
    # Выполняется с нарушением срока Инциденты Высокий len_tickets_list_27_H_4
    # Выполняется с нарушением срока Инциденты Средний len_tickets_list_27_M_4
    # Выполняется с нарушением срока Инциденты Низкий len_tickets_list_27_L_4

    # Процент SLA всего len_tickets_list_result
    # Процент SLA Запросы на обслуживание len_tickets_list_28_result
    # Процент SLA Запросы на обслуживание Высокий len_tickets_list_28_H_result
    # Процент SLA Запросы на обслуживание Средний len_tickets_list_28_M_result
    # Процент SLA Запросы на обслуживание Низкий len_tickets_list_28_L_result
    # Процент SLA Инциденты len_tickets_list_27_result
    # Процент SLA Инциденты Критичный len_tickets_list_27_C_result
    # Процент SLA Инциденты Высокий len_tickets_list_27_H_result
    # Процент SLA Инциденты Средний len_tickets_list_27_M_result
    # Процент SLA Инциденты Низкий len_tickets_list_27_L_result

# передаем параметры и заполняем файл
context = {'today' : today, 'table_rows' : table_rows}
docx.render(context)
# сохраняем файл
docx.save("./Temp_report_PR_final.docx")


#### Нет разграничения по параметрам на новые и прошлого периода. Выводит все тиакеты. Парамс.