import os
import unidecode
import re
import time
import requests
import pandas as pd

from utils import create_webdriver
from tqdm import tqdm
from bs4 import BeautifulSoup


class VilleIdeale():
    """
    Download comments and ratings from https://www.ville-ideale.fr/
    """

    def __init__(self, driver, time_sleep=1, verbose=True, close_driver=True):
        """
        Parameters:
        -----------
        driver : Selenium webdriver.
        time_sleep : int, default=1
            Waiting time in second.
        verbose: bool, defaut=True
            Show progress bar.
        close_driver: bool, default=True
            Whether to close driver after downloading

        Example
        -------
        >>>> from utils import create_webdriver
        >>>> driver = create_webdriver()
        >>>> ville_ideale = VilleIdeale(driver=driver)
        >>>> cities = ['morangis_91432', 'wissous_91689']
        >>>> ville_ideale.get_city(cities)
        """
        self.driver = driver
        self.time_sleep = time_sleep
        self.verbose = verbose
        self.close_driver = close_driver

    def close(self):
        self.driver.close()

    def _create_url(self, id_city, page=1):
        url_root = 'https://www.ville-ideale.fr/'
        url = url_root + id_city

        if page != 1:
            url_end = f'?page={page}#commentaires'
            url += url_end

        return url

    def _get_page_source(self, url, get_page_max=False):
        self.driver.get(url)
        page_source = self.driver.page_source

        if get_page_max:
            page_max = int(BeautifulSoup(page_source, 'lxml').find(
                'nav', {'id': 'pages'}).find_all('a')[-2].text)

        return (page_source, page_max) if get_page_max else page_source

    def _extract_page_info(self, page_source):
        d = {}
        index = 0
        r = re.compile(r"[0-9]{2}-[0-9]{2}-[0-9]{4}")
        criteria = [
            'environment',
            'transport',
            'security',
            'health',
            'leisure',
            'culture',
            'education',
            'shop',
            'quality_of_life'
        ]
        soup = BeautifulSoup(page_source, 'lxml')
        comment = soup.find_all('div', class_='comm')

        for ct in comment:
            all_p = ct.find_all('p')
            note = comment[1].find_all('td')
            scores = ct.find_all('td')
            d[index] = {
                'date': r.findall(ct.span.text)[0],
                'average': ct.find(class_='moyenne').text,
                'ct_pos': all_p[1].text,
                'ct_neg': all_p[2].text,
                'feedback_pos': all_p[3].find_all('strong')[0].text,
                'feedback_neg': all_p[3].find_all('strong')[1].text
            }
            d_score = {crit: score.text for crit,
                       score in zip(criteria, scores)}
            d[index].update(d_score)
            index += 1

        page_info = pd.DataFrame.from_dict(d, orient='index')
        return page_info

    def _extract_all_info(self, id_city):
        all_info = []
        url = self._create_url(id_city)
        page_source, page_max = self._get_page_source(url, get_page_max=True)
        page_info = self._extract_page_info(page_source)
        all_info.append(page_info)

        for page in range(2, page_max+1):
            url = self._create_url(id_city, page=page)
            page_source = self._get_page_source(url)
            page_info = self._extract_page_info(page_source)
            all_info.append(page_info)
            time.sleep(self.time_sleep)

        all_info = pd.concat(all_info, ignore_index=True)
        return all_info

    def get_city(self, cities):
        self.cities = cities
        self.n_cities = len(cities)
        dict_city = {}

        if self.verbose:
            cities = tqdm(cities)

        for city in cities:
            city_all_info = self._extract_all_info(city)
            dict_city[city] = city_all_info

        if self.close_driver:
            self.close()

        return dict_city
