import json,pickle
from steampy.models import GameOptions, Currency
from bs4 import BeautifulSoup
import requests, re
import time, asyncio
from headers import headers

def proxies_list(n):
    login = ''
    password = ''

    proxies_list = [
        {
            'http': f'socks5://{login}:{password}@',
            'https': f'socks5://{login}:{password}@'            
        },
        {
            'http': f'socks5://{login}:{password}@',
            'https': f'socks5://{login}:{password}@'            
        },
        {
            'http': f'socks5://{login}:{password}@',
            'https': f'socks5://{login}:{password}@'            
        },
        {
            'http': f'socks5://{login}:{password}@',
            'https': f'socks5://{login}:{password}@'            
        },
        {
            'http': f'socks5://{login}:{password}@',
            'https': f'socks5://{login}:{password}@'            
        },

        ]
    
    proxies = proxies_list[n]
    return proxies

def comparing(item_url,item,item_list):
    
    r = requests.get(item_url, headers=headers)
    
    if r.status_code != 200:
        print('\n' + 'Подождите немного' + '\n')
        time.sleep(45)
        price_ob,price_ins = comparing(item_url,item,item_list)
        
        return price_ob, price_ins
        
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

def purchase_order_one(item_list,item,proxies,n):
    
    try:
        price_order_buy,n = purchase_order(item_list,item,proxies,n)
    except:
        n += 1
        if n == 5:
            n = 0
        proxies = proxies_list(n)
        print("Смена IP")
        time.sleep(2)
        price_order_buy,n = purchase_order_one(item_list,item,proxies,n)
    
    return price_order_buy,n

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

    time.sleep(1)

    soup = BeautifulSoup(response, "lxml")
    
    a = soup.find_all('tr')
        
    price = a[-6].text
    price =price.partition(' ')[0].replace(',','.')
    
    item_list[item]['price_order'] = price
    file = open("items_list.json", 'w')
    json.dump(item_list,file)
    file.close()
    return price,n


def main():
    
    with open(f"steamClient.pkl", 'rb') as file:
        steam_client = pickle.load(file)
    
    with open('items_list.json', 'r', encoding='utf-8') as fh:
        item_list = json.load(fh)
        
    n = 0
    proxies = proxies_list(n)
        
    for item in item_list:
        urrr = item.replace('Inscribed ','')
        item_url = f'https://steamcommunity.com/market/search?category_570_Hero%5B%5D=any&category_570_Slot%5B%5D=any&category_570_Type%5B%5D=any&category_570_Quality[]=tag_unique&appid=570&q={urrr}'
        
        listings_item = steam_client.market.get_my_market_listings()
        
        i = 0
        for el in listings_item["buy_orders"]:
            item_name = listings_item["buy_orders"][el]['item_name']
            if item == item_name:
                print(f'предмет {item} есть')
                i = 1
                break
            
        time.sleep(0.5)
        
        if i == 0:
            
            price_ob = comparing(item_url,item,item_list)
            price_ob = price_ob * 100
            price_order_buy,n = purchase_order_one(item_list,item,proxies,n)
            
            price_order_buy = re.findall(r'\d+', price_order_buy) 
            if len(price_order_buy) == 1:
                price_order_buy = price_order_buy + [0]
            price_order_buy = float(price_order_buy[0]) + float(price_order_buy[1])/100
            price_order_buy = price_order_buy*100 
            price_order_buy = price_order_buy + 2
            
            if price_order_buy < (price_ob - (price_ob * 0.15)):
                
                response = steam_client.market.create_buy_order(f'{item}', f'{price_order_buy}', 1, GameOptions.DOTA2, Currency.RUB)
                buy_order_id = response["buy_orderid"]
                item_list[item]['buy_order_id'] = buy_order_id
                file = open("items_list.json", 'w')
                json.dump(item_list,file)
                file.close()

                print(f"предмет выставлен {item}")
                
                asyncio.sleep(3000)
                time.sleep(2)
            else:
                print(f'цена не подходит ({item})')
                asyncio.sleep(3000)
                time.sleep(2)
    
if __name__ == "__main__":
    main()
    