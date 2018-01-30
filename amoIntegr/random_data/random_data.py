    statuses_id = [status for status in user_cfg.cache["_embedded"]["pipelines"]["179028"]["statuses"]]
    
    statuses_id = ["142", "143"]
    
    prodaja = ["Продажа", "Поставка", "Отгрузка", "Заказ"]
    ovoschy = ["картошки", "овощей", "грибов", "мяса", "курицы", "сухофруктов", 
        "ягод", "консервов", "круассанов", "джема", "специй", "рыбы", "тунца"]
        
    tags = ["Повторный заказ", "Постоянный клиент", "Склад в Вологде", "Доставка СНГ", ""]
    
    from random import randint
    import random  
    import time
    for i in range(1, 35):
 
        lines = open(file_path).read().splitlines()
        myline =random.choice(lines)
        print(myline)
        
        contact_data["custom_fields"]["Телефон"]["WORK"] = '+7 495' + str(randint(1111111, 9999999))
    
        resp = api.add_entity("contacts", myline, -1, contact_data["custom_fields"], call = False)
        id123 = resp["_embedded"]["items"][0]["id"]
        price = randint(1, 300)*1000 + randint(1,5)*250
        tag = random.choice(tags)
        if price > 150000:
            tag += ", VIP"
        api.add_entity(
            "leads", 
            random.choice(prodaja)+" "+random.choice(ovoschy), 
            -1, lead_data["custom_fields"], 
            call = False,
            contacts_id=id123, 
            status_id=random.choice(statuses_id), 
            sale = price,
            tags=tag,
            created_at = randint(int(time.time() - 360*24*60*60), int(time.time()))
        )
        
    # users = list(user_cfg.cache['_embedded']['users'].keys())
    # pprint(users)
    
    # contacts = api.get_entity('contacts', limit_rows=500)['_embedded']['items']
    # contacts += api.get_entity('contacts', limit_offset=500, limit_rows=500)['_embedded']['items']
    # ids = [contact['id'] for contact in contacts]
    # pprint(len(set(ids)))
    
    # companies = api.get_entity('companies', limit_rows=500)['_embedded']['items']
    # companies += api.get_entity('companies', limit_offset=500, limit_rows=500)['_embedded']['items']
    # ids = [company['id'] for company in companies]
    # pprint(len(set(ids)))
    
    # resp_companies = {}
    # for company in companies:
    #     resp_companies[company['id']] = company['responsible_user_id']
    
    # for contact in contacts:
    #     resp_user = contact['responsible_user_id']
    #     if 'company' in contact and 'id' in contact['company']:
    #         if resp_companies[contact['company']['id']] != resp_user:
    #             pprint('Butthurt!')
    #             pprint(contact['id'])

    # pprint('Done!')
    
    # import random
    # a=0
    # b=0
    # for contact in contacts:
    #     id = str(contact['id'])
    #     resp_user = str(contact['responsible_user_id'])
    #     if not resp_user in users:
    #         resp_user = random.choice(users)
    #         api.update_entity('contacts', id, responsible_user_id=resp_user)
    #         a += 1
        
    #     if 'company' in contact and 'id' in contact['company']:
    #         api.update_entity('companies', contact['company']['id'], responsible_user_id=resp_user)
    #         b+=1 
    
    # pprint(a)
    # pprint(b)