import os
import logging as lg
import pandas as pd
import requests

from bs4 import BeautifulSoup
from unidecode import unidecode


URL_DICT = {77: 'https://fr.wikipedia.org/wiki/Liste_des_communes_de_Seine-et-Marne',
            78: 'https://fr.wikipedia.org/wiki/Liste_des_communes_des_Yvelines',
            91: 'https://fr.wikipedia.org/wiki/Liste_des_communes_de_l%27Essonne',
            92: 'https://fr.wikipedia.org/wiki/Liste_des_communes_des_Hauts-de-Seine',
            93: 'https://fr.wikipedia.org/wiki/Liste_des_communes_de_la_Seine-Saint-Denis',
            94: 'https://fr.wikipedia.org/wiki/Liste_des_communes_du_Val-de-Marne',
            95: 'https://fr.wikipedia.org/wiki/Liste_des_communes_du_Val-d%27Oise'}


def get_idf_cities(url_dict = URL_DICT,
                   process=True,
                   save=False,
                   path=None):
    data = []
    for url in url_dict.values():
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
        if path is not None:
            df.to_csv(path, sep=';', encoding='utf-8')
        else:
            if os.path.isdir('data/'):
                pass
            else:
                os.mkdir("data/")
            df.to_csv(os.path.join('data', 'city_list.csv'),
                      sep=';', encoding='utf-8')
    else:
        return df


if __name__ == "__main__":
    get_idf_cities(save=True)