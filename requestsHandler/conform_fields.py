from pprint import pprint
import requests
import re

from django.conf import settings

# from dadata.plugins.django import DjangoDaDataClient
from utils import one_by_one, not_chosen, default_name, phone_field, email_field

digits_to_query = 7
def conform_fields(data, conformity, rights, ip=None):
    city = ''
    region = ''
    if ip:
        resp = requests.get('https://suggestions.dadata.ru/suggestions/api/4_1/rs/detectAddressByIp?ip='+ip, headers={
            'Accept' : 'application/json',
            'Authorization' : 'Token ' + settings.DADATA_KEY
        })
        try:
            city = resp.json()['location']['data']['city']
            region = resp.json()['location']['data']['region']
        except Exception as e:
            pass

    data_to_send = {
        'contact_data' : {},
        'company_data' : {},
        'lead_data' : {}
    }

    for data_type in data_to_send.keys():
        if data_type in conformity and conformity[data_type]:
            if 'name' in conformity[data_type] and conformity[data_type]['name'] in data \
                and data[conformity[data_type]['name']]:
                data_to_send[data_type]['name'] = data[conformity[data_type]['name']]
            elif 'default_name' in conformity[data_type] and conformity[data_type]['default_name']:
                data_to_send[data_type]['name'] = conformity[data_type]['default_name']
            elif data_type == 'lead_data':
                data_to_send[data_type]['name'] = None
            else:
                data_to_send[data_type]['name'] = default_name

            data_to_send[data_type]['custom_fields'] = {}
            for field, field_alias in conformity[data_type].items():
                if not field in ['name', 'default_name', 'tags']:
                    if field_alias in data and data[field_alias]:
                        if not field in [phone_field, email_field]:
                            data_to_send[data_type]['custom_fields'][field] = data[field_alias]
                        else:
                            data_to_send[data_type]['custom_fields'][field] = {
                                'WORK' : data[field_alias]
                            }
                    elif not field in [phone_field, email_field]:
                        if field_alias == '@ip_city':
                            data_to_send[data_type]['custom_fields'][field] = city
                        elif field_alias == '@ip_region':
                            data_to_send[data_type]['custom_fields'][field] = region

            if 'tags' in conformity[data_type]:
                data_to_send[data_type]['tags'] = conformity[data_type]['tags']
            else:
                data_to_send[data_type]['tags'] = ''

    generate_tasks_for_rec = False
    if 'generate_tasks_for_rec' in conformity:
        generate_tasks_for_rec = conformity['generate_tasks_for_rec']

    department_id = -1
    if 'department_id' in conformity and conformity['department_id'] != not_chosen:
        department_id = conformity['department_id']

    internal_kwargs = {'additional_data_to_query' : {
        'contacts' : {},
        'companies' : {}
    }}
    if 'responsible_user_id' in conformity and conformity['responsible_user_id'] != one_by_one:
        internal_kwargs['responsible_user_id'] = conformity['responsible_user_id']

    additional_params = ['pipelines', 'tag_for_rec', 'time_to_complete_rec_task',
        'rec_lead_task_text', 'fields_to_check_dups']
    for param in additional_params:
       if param in conformity:
           internal_kwargs[param] = conformity[param]

    internal_kwargs['additional_data_to_query']['contacts'][phone_field] = []
    internal_kwargs['additional_data_to_query']['companies'][phone_field] = []
    # if 'dadata_phone_check' in rights and rights['dadata_phone_check']:
    #     client = DjangoDaDataClient()

    tdict = {
        'contact_data' : 'contacts',
        'company_data' : 'companies'
    }
    for data_type in ['contact_data', 'company_data']:
        if 'custom_fields' in data_to_send[data_type] and phone_field in \
            data_to_send[data_type]['custom_fields']:

            for key,value in data_to_send[data_type]['custom_fields'][phone_field].items():
                # if 'dadata_phone_check' in rights and rights['dadata_phone_check']:
                #     client.phone = value
                #     client.phone.request()
                #
                #     if client.result.phone != None:
                #         data_to_send[data_type]['custom_fields'][phone_field][key] = client.result.phone
                #
                #     if client.result.number != None:
                #         internal_kwargs['additional_data_to_query'][tdict[data_type]][phone_field].append({
                #             'WORK' : client.result.number
                #         })
                digits = re.findall(r'\d+', value)
                digits = ''.join(digits)
                if len(digits) > 6:
                    internal_kwargs['additional_data_to_query'][tdict[data_type]][phone_field].append({
                        'WORK' : digits[-digits_to_query:]
                    })

    return (data_to_send, generate_tasks_for_rec, department_id, internal_kwargs)

def find_pipline_id(pipelines, name):
    for pipeline_id, pipeline in pipelines.items():
        for status_id, status in pipeline['statuses'].items():
            if pipeline['name'] == name.split('/')[0] and status['name'] == name.split('/')[1]:
                return status_id

def unflatten(dictionary):
    resultDict = dict()
    for key, value in dictionary.items():
        parts = key.split("[")
        d = resultDict
        for part in parts[:-1]:
            part = part[:-1]
            if part not in d:
                d[part] = dict()
            d = d[part]
        d[parts[-1][:-1]] = value
    return resultDict
