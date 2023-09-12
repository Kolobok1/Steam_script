import json,pickle
from steampy.models import GameOptions, Currency
from bs4 import BeautifulSoup
import requests, re
import time
from headers import headers


def proxies_list(n):

    login = ''
    password = ''

    proxies_list = [
        {
            'http': f'http://{login}:{password}@',
            'https': f'http://{login}:{password}@'            
        },
        {
            'http': f'http://{login}:{password}@',
            'https': f'http://{login}:{password}@'            
        },
        {
            'http': f'http://{login}:{password}@',
            'https': f'http://{login}:{password}@'            
        },
    ]
    
    proxies = proxies_list[n]
    return proxies

# получаем цену для продажи предмета с учётом комиссии
def comparing(item_url,item,item_list):
    try:
        r = requests.get(item_url, headers=headers)
        src = r.text
        soup = BeautifulSoup(src, "lxml")
        
        name_item = soup.find('a', class_='market_listing_row_link')
        
        price = name_item.find('span', class_='market_table_value normal_price')
        price = price.find('span', class_='normal_price').text
        price = re.findall(r'\d+', price) 
        if len(price) == 1:
            price = price + [0]
        price = float(price[0]) + float(price[1])/100
        
        item_list[item]['price_ob'] = price
        with open('items_list.json', 'w', encoding="utf-8") as file:
            json.dump(item_list, file)
        
        return price
    
    # переподключение при плохом соединении в Steam
    except AttributeError:
        print('Ошибка подключения ')
        time.sleep(5)
        price = comparing(item_url,item,item_list)
        return price

# парсим предметы на которые есть запрос на покупку
def get_order_list():
    url = 'https://steamcommunity.com/market/'
    
    data = []
    
    response = requests.get(url=url, headers=headers).text

    soup = BeautifulSoup(response, "lxml")

    src = soup.find_all('div', class_ = 'market_listing_row market_recent_listing_row')

    for el in src:
        item = el.find('a', class_='market_listing_item_name_link')
        data.append(item.text)
        
    return data
   
# получаем цену для выставления запроса на покупку     
def purchase_order(item_list,item,proxies,n):
    
    id = item_list[item]['id']

    params = {
        'country': 'RU',
        'language': 'russian',
        'currency': '5',
        'item_nameid': id,
        'two_factor': '0',
    }

    response = requests.get('https://steamcommunity.com/market/itemordershistogram', params=params, headers=headers, proxies=proxies).text 

    soup = BeautifulSoup(response, "lxml")
    
    a = soup.find_all('tr')
        
    price = a[-6].text
    price =price.partition(' ')[0].replace(',','.')
    
    item_list[item]['price_order'] = price
    file = open("items_list.json", 'w')
    json.dump(item_list,file)
    file.close()
    
    # переводим из строки в число
    price_order_buy = re.findall(r'\d+', price) 
    if len(price_order_buy) == 1:
        price_order_buy = price_order_buy + [0]
    price_order_buy = float(price_order_buy[0]) + float(price_order_buy[1])/100
    price_order_buy = price_order_buy*100 
    price = price_order_buy + 2
    
    return price,n

def main():
    
    with open(f"steamClient.pkl", 'rb') as file:
        steam_client = pickle.load(file)
    
    with open('items_list.json', 'r', encoding='utf-8') as fh:
        item_list = json.load(fh)
        
    n = 0
    proxies = proxies_list(n)
    
    listings_item = get_order_list()

    for item in item_list:
        urrr = item.replace('Inscribed ','')
        item_url = f'https://steamcommunity.com/market/search?category_570_Hero%5B%5D=any&category_570_Slot%5B%5D=any&category_570_Type%5B%5D=any&category_570_Quality[]=tag_unique&appid=570&q={urrr}'
        
        
        i = 0
        # проверяем есть ли педмет в списке покупок
        for el in listings_item:

            if item == el:
                print(f'Предмет {item} ЕСТЬ')
                i = 1
                break
            
        time.sleep(1)
        
        if i == 0:
            
            price_ob = comparing(item_url,item,item_list)
            price_ob = price_ob * 100
            try:
                price_order_buy,n = purchase_order(item_list,item,proxies,n)
            
            # смена IP адреса 
            except IndexError:
                n += 1
                proxies = proxies_list(n)
                print("Смена IP")
                time.sleep(2)
                price_order_buy,n = purchase_order(item_list,item,proxies,n)
            
            # сравнение двух цен и выставление запроса
            if price_order_buy < (price_ob - (price_ob * 0.15)):
                
                response = steam_client.market.create_buy_order(f'{item}', f'{price_order_buy}', 1, GameOptions.DOTA2, Currency.RUB)
                buy_order_id = response["buy_orderid"]
                item_list[item]['buy_order_id'] = buy_order_id
                file = open("items_list.json", 'w')
                json.dump(item_list,file)
                file.close()
                print(f"Предмет ВЫСТАВЛЕН {item}")
                
            else:
                print(f'ЦЕНА НЕ ПОДХОДИТ ({item})')
            
if __name__ == "__main__":
    main()
        
