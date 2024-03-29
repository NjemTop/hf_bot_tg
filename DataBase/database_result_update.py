import locale
from datetime import datetime
from DataBase.model_class import Release_info, conn

def upload_db_result(version_number, result):
    """Функция получения данных из рассылки (PS) и заполнения этих данных в БД"""
    # Соеденимся с БД, по завершению закроем соединение
    with conn:
        # Запись месяца в дате по-русски
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        # Определяем дату рассылки = текущая дата запуска скрипта
        today = datetime.now().date().strftime('%d %B %Y')

        # Создаем из построчного вывода общий список
        item = result.split('\n')
        # Перебираем списки внутри общего списка
        for i in item:
            # Исключаем пустой список
            if i != '':
                # Проверяем наличие символа '|' в строке
                if '|' in i:
                    # Делим список по параметрам с пом. разделителя
                    l = i.split('|')
                    # Наименование клиента
                    client_name = l[0]
                    # Основной контакт
                    main_contact = l[1]
                    # Копия
                    if len(l) == 3:
                        copy_contact = l[2].replace(',', ', ')
                    else:
                        copy_contact = None

                    # Создаем новую запись и сохраняем ее в базе данных
                    new_info = Release_info.create(
                        date=today,
                        release_number=version_number,
                        client_name=client_name,
                        main_contact=main_contact,
                        copy=copy_contact
                    )
                continue
