import requests
from bs4 import BeautifulSoup
import re
import ssl
import json
import pymongo
import pprint


def request_to_site(topic):
    print('Programs starts requesting from url topic: ', topic)
    url = 'https://www.avito.ru/rossiya/avtomobili?q='
    try:
        print(url+topic)
        request = requests.get(url + topic)
        if request.status_code == '200':
            print('Request was successful')
        return request.content.decode('utf-8')
    except requests.exceptions.ConnectionError:
        print('Check your internet connection!')
        exit(1)


def parse_html(topic):
    print('Program starts parsing html with topic', topic)
    html = request_to_site(topic)
    soup = BeautifulSoup(html, 'html.parser')
    parsed_text = soup.findAll('div', {'class': 'description item_table-description'})
    print('Program parsed successfully')
    return parsed_text


def get_advertisements(parsed_text):
    print('Program starts getting data')
    car_dict = dict()
    counter = 0
    for text in parsed_text:
        counter += 1
        car_title = text.find('a', {'class': 'item-description-title-link'})['title']
        car_title2 = text.find('span', {'itemprop': 'name'}).string
        car_url = 'https://www.avito.ru' + text.find('a', {'class': 'item-description-title-link'})['href']
        car_currency = text.find('span', {'itemprop': 'priceCurrency'})['content']
        car_price = text.find('span', {'class': re.compile(r'price.*')})['content']
        car_price2 = text.find('span', {'class': 'font_arial-rub'}).string
        car_info = text.find('div', {'class': 'specific-params specific-params_block'}).text.replace('\n', '').replace(
            '\xa0', '').replace('  ', '').split(',')
        try:
            car_info2 = text.find('div', {'class': 'js-autoteka-serp'})['data-state'].replace("\\", '')
            car_info2 = json.loads(car_info2)
        except TypeError:
            car_info2 = 'could not get json'
        for i in range(len(car_info)):
            car_info[i] = car_info[i].strip()
        car_dict.setdefault(counter, [{'car_title': car_title,
                                       'car_title2': car_title2,
                                       'car_currency': car_currency,
                                       'car_price': car_price + ' ' + car_price2,
                                       'car_url': car_url,
                                       'car_info': car_info,
                                       'car_info2': car_info2}])
    print('Program finished getting data')
    return car_dict


def upload_to_mongo(car_ads_db):
    mongo_url = 'mongodb+srv://test2:test2@cluster0-bvxkt.gcp.mongodb.net/test?retryWrites=true&w=majority'
    client = pymongo.MongoClient(mongo_url, ssl=True, ssl_cert_reqs=ssl.CERT_NONE)
    db = client.get_database('avito_ru')
    records = db.avito_ads
    count_before_adding: int = records.count_documents({})
    print('Number of records in avito_ru DB: ', count_before_adding)
    # records.drop()
    for key in car_ads_db:
        records.insert_many(car_ads_db[key])
    count_after_adding = records.count_documents({})
    print('Number of records in avito_ru DB: ', count_after_adding)
    print('Data was successfully added: ', count_after_adding-count_before_adding)


def input_search_word():
    input_topic = input(
        'Please enter car company and model(if left blank automatically will search for hyunday solaris):').rstrip()
    print(input_topic)
    if input_topic == '':
        input_topic: str = 'hyundai%20solaris'
    else:
        print('%20')
        input_topic = input_topic.replace(' ', '%20')
    return input_topic


search_topic = input_search_word()
parsed_text_avito = parse_html(search_topic)
car_ads = get_advertisements(parsed_text_avito)
upload_to_mongo(car_ads)
pprint.pprint(car_ads)
