entity_optional_params = {
    'contacts' : ['tags', 'created_at', 'updated_at', 'created_by',
        'company_name', 'leads_id', 'customers_id', 'company_id'],
    'leads' : ['tags', 'created_at', 'updated_at', 'status_id', 'pipeline_id',
        'sale', 'contacts_id', 'company_id'],
    'companies' : ['tags', 'created_at', 'updated_at', 'created_by', 'leads_id',
        'customers_id', 'contacts_id'],
    'customers' : ['tags', 'next_date', 'created_at', 'updated_at', 'created_by',
        'next_price', 'periodicity', 'period_id', 'contacts_id', 'company_id',]
}

update_optional_params = {
    'contacts' : ['name', 'unlink', 'responsible_user_id'],
    'leads' : ['name', 'unlink', 'responsible_user_id'],
    'companies' : ['name', 'unlink', 'responsible_user_id'],
    'customers' : ['name', 'unlink', 'responsible_user_id']
}

get_optional_params = {
    'contacts' : ['id[]', 'id', 'limit_rows', 'limit_offset',
        'responsible_user_id', 'query'],
    'leads' : ['id[]', 'limit_rows', 'limit_offset', 'id', 'query',
        'responsible_user_id', 'status'],
    'companies' : ['id[]', 'limit_rows', 'limit_offset', 'id', 'query',
        'responsible_user_id'],
    'tasks' : ['id[]', 'id', 'limit_rows', 'limit_offset', 'element_id',
        'responsible_user_id', 'type']
}

def time_in_range(now, start, end):
    start = start.split(':')
    end = end.split(':')
    start = now.replace(hour=int(start[0]), minute=int(start[1]))
    end = now.replace(hour=int(end[0]), minute=int(end[1]))
    if start <= end:
        return start <= now <= end
    else:
        return end <= now <= start

def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

config_types = {
    'site_forms' : [],
    'jivo_site' : ['event_name', 'chat_id', 'widget_id', 'visitor.name'],
    'onpbx' : ['phone', 'Телефония', 'caller_number', 'caller_name', 'domain',
        'type', 'trunk', 'uuid', 'dtmf', 'rec_link'],
    'email' : ['recipient', 'sender', 'from.name', 'from.email', 'subject', \
        'body-plain', 'stripped-text', 'stripped-signature', 'body-html', \
        'stripped-html', 'attachment-count', 'Email']
}
def get_config_forms(config):
    config_names = []
    for key in config_types:
        if key in config:
            config_names += config[key].keys()

    return config_names

one_by_one = 'По очереди'
zero_department = 'Отдел продаж'
not_chosen = 'Не выбрано'
ending_statuses = [142, 143]
succes_status = 142
no_form = 'no_form'
no_form_type = 'no_type'
weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
default_name = 'Имя не указано'
phone_field = 'Телефон'
email_field = 'Email'
