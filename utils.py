import os
import logging as lg
import pandas as pd
import requests

from bs4 import BeautifulSoup
from unidecode import unidecode
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


url_list = ['https://fr.wikipedia.org/wiki/Liste_des_communes_de_Seine-et-Marne',
            'https://fr.wikipedia.org/wiki/Liste_des_communes_des_Yvelines',
            'https://fr.wikipedia.org/wiki/Liste_des_communes_de_l%27Essonne',
            'https://fr.wikipedia.org/wiki/Liste_des_communes_des_Hauts-de-Seine',
            'https://fr.wikipedia.org/wiki/Liste_des_communes_de_la_Seine-Saint-Denis',
            'https://fr.wikipedia.org/wiki/Liste_des_communes_du_Val-de-Marne',
            'https://fr.wikipedia.org/wiki/Liste_des_communes_du_Val-d%27Oise']


def scrap_city(url_list=url_list, process=True, save=False):
    data = []
    for url in url_list:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'lxml')
        table_rows = soup.find_all('table')[1].find_all('tr')
        for row in table_rows:
            try:
                data.append([t.text.strip().lower()
                             for t in row.find_all('td')][:3])
            except IndexError:
                lg.warning('beginning or end of table')
    df = pd.DataFrame(data, columns=['name', 'insee_code', 'postal_code'])

    if process:
        df.dropna(inplace=True)
        df['postal_code'] = df['postal_code'].map(lambda x: x[:5])
        df['name'] = df['name'].map(lambda x: unidecode(
            x, 'utf-8')).replace('\(prefecture\)', '', regex=True)
        df['id_city'] = df['name'] + '_' + df['insee_code']

    if save:
        df.to_csv(os.path.join('data', 'city_info.csv'),
                  sep=';', encoding='utf-8')
    else:
        return df


def create_webdriver(driver_path=None, active_options=False):
    if active_options:
        options = Options()
        options.add_argument('--headless')
    else:
        options = None
    if driver_path is not None:
        path_driver = driver_path
    else:
        path_driver = 'geckodriver'
    driver = webdriver.Firefox(executable_path=path_driver, options=options)
    return driver
