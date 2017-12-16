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