import json,pickle
from bs4 import BeautifulSoup
import requests, re
import time
from headers import headers

def companing(item_url):
    try:
        price_data = []
        
        r = requests.get(item_url, headers=headers).text
        soup = BeautifulSoup(r, "lxml")
        price_items = soup.find_all('span', class_='market_table_value normal_price')
        for price_item in price_items:
            
            price_item = price_item.find('span', class_='normal_price').text
            price_item = re.findall(r'\d+', price_item) 
            if len(price_item) == 1:
                price_item = price_item + [0]
            price_item = float(price_item[0]) + float(price_item[1])/100
            price_data.append(price_item)
        
        # сделать распределение по цене
        price = price_data[0]
        price -= price * 0.13
        price = round(price,2)
        price_data[0] = price
        if price_data[0] > price_data[1]:
            return price_data
        else:
            return None
    except:
        print('ошибка подключения')
        time.sleep(5)
        price_data = companing(item_url)
    

def main():
    
    with open('items_list.json', 'r', encoding='utf-8') as fh:
        item_list = json.load(fh)
    
    for item in item_list:
        urrr = item.replace('Inscribed ','')
        item_url = f'https://steamcommunity.com/market/search?category_570_Hero%5B%5D=any&category_570_Slot%5B%5D=any&category_570_Type%5B%5D=any&category_570_Quality[]=tag_unique&category_570_Quality[]=tag_strange&appid=570&q={urrr}'

        price_data = companing(item_url)

        if price_data != None:
            print(item,' ', item_list[item]['url'])
            price = price_data[0] - price_data[1] 
            price = round(price,2)
            print(price, '\n')
        else:
            print('не нада')

if __name__ == "__main__":
    main()
    
