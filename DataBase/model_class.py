import peewee

# Путь к файлу базы данных
db_filename = 'DataBase/database.db'
# db_filename = './DataBase/database.db'

# Подключение к базе данных SQLite
conn = peewee.SqliteDatabase(f'file:{db_filename}')

# Определяем базовую модель о которой будут наследоваться остальные
class BaseModel(peewee.Model):
    class Meta:
        database = conn  # соединение с базой

    @property
    def columns(self):
        return {field.column_name: field for field in self._meta.sorted_fields}

    @classmethod
    def rename_table(cls, old_name, new_name):
        with cls._meta.database:
            cls._meta.database.execute_sql(f"ALTER TABLE {old_name} RENAME TO {new_name}")

# Определяем модель для таблицы "release_info"
class Release_info(BaseModel):
    """Класс для таблицы БД release_info"""
    date = peewee.DateField(column_name='Дата_рассылки')
    release_number = peewee.IntegerField(column_name='Номер_релиза', primary_key=True)
    client_name = peewee.TextField(column_name='Наименование_клиента')
    main_contact = peewee.TextField(column_name='Основной_контакт')
    copy = peewee.TextField(column_name='Копия')

    # Список наименований столбцов
    COLUMN_NAMES = [
        'date',
        'release_number',
        'client_name',
        'main_contact',
        'copy'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = Release_info.COLUMN_NAMES

    class Meta:
        table_name = 'release_info'

class ClientsInfo(BaseModel):
    """Класс для таблицы БД clients_info"""
    client_name = peewee.TextField(column_name='Название_клиента', primary_key=True)
    contract_status = peewee.BooleanField(column_name='Активность')
    client_info = peewee.IntegerField(column_name='Карточка_клиента')
    Service = peewee.IntegerField(column_name='Обслуживание')
    technical_information = peewee.IntegerField(column_name='Техническая_информация')
    integration = peewee.IntegerField(column_name='Интеграции')
    notes = peewee.TextField(column_name='Примечания')

    # Список наименований столбцов
    COLUMN_NAMES = [
        'client_name',
        'contract_status',
        'client_info',
        'Service',
        'technical_information',
        'integration',
        'notes'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = ClientsInfo.COLUMN_NAMES
    
    class Meta:
        table_name = 'BM_info_on_clients'
