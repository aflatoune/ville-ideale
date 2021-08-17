import os
import unidecode
import re
import time
import requests
import pandas as pd

from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


class VilleIdeale():
    """
    Download comments and ratings from https://www.ville-ideale.fr/
    """

    def __init__(self,
                 driver,
                 time_sleep=2,
                 verbose=True,
                 close_driver=True):
        """
        Parameters:
        -----------
        driver : Selenium webdriver.
        time_sleep : int, default=2
            Waiting time in second.
        verbose: bool, defaut=True
            Show progress bar.
        close_driver: bool, default=True
            Whether to close driver after downloading

        Example
        -------
        >>>> driver = VilleIdeale.create_webdriver()
        >>>> ville_ideale = VilleIdeale(driver=driver)
        >>>> cities = ['morangis_91432', 'wissous_91689']
        >>>> ville_ideale.download(cities)
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
        page_info = {}
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
        comments = soup.find_all('div', class_='comm')

        for ct in comments:
            all_p = ct.find_all('p')
            note = comments[1].find_all('td')
            scores = ct.find_all('td')
            page_info[index] = {
                'date': r.findall(ct.span.text)[0],
                'average': ct.find(class_='moyenne').text,
                'ct_pos': all_p[1].text,
                'ct_neg': all_p[2].text,
                'feedback_pos': all_p[3].find_all('strong')[0].text,
                'feedback_neg': all_p[3].find_all('strong')[1].text
            }
            d_score = {crit: score.text for crit,
                       score in zip(criteria, scores)}
            page_info[index].update(d_score)
            index += 1

        page_info = pd.DataFrame.from_dict(page_info, orient='index')
        return page_info

    def _extract_city_info(self, id_city):
        city_info = []
        url = self._create_url(id_city)
        page_source, page_max = self._get_page_source(url, get_page_max=True)
        page_info = self._extract_page_info(page_source)
        city_info.append(page_info)
        time.sleep(self.time_sleep)

        for page in range(2, page_max+1):
            url = self._create_url(id_city, page=page)
            page_source = self._get_page_source(url)
            page_info = self._extract_page_info(page_source)
            city_info.append(page_info)
            time.sleep(self.time_sleep)

        city_info = pd.concat(city_info, ignore_index=True)
        return city_info

    def download(self, cities):
        self.cities = cities
        self.n_cities = len(cities)
        output = {}

        if self.verbose:
            cities = tqdm(cities)

        for city in cities:
            city_info = self._extract_city_info(city)
            output[city] = city_info

        if self.close_driver:
            self.close()

        return output

    @staticmethod
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
