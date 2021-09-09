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

    CRITERIA = [
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

    def __init__(self,
                 driver=None,
                 time_sleep=1,
                 verbose=True,
                 close_driver=True):
        """
        Parameters:
        -----------
        driver: Selenium webdriver, default: None
            If None http requests are made with the requests library.
        time_sleep : int, default: 1
            Waiting time in second.
        verbose: bool, default: True
            Show progress bar.
        close_driver: bool, default: True
            Whether to close driver after downloading.
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

        if self.driver is not None:
            self.driver.get(url)
            page_source = self.driver.page_source
        else:
            page_source = requests.get(url).text

        if get_page_max:
            page_max = int(BeautifulSoup(page_source, 'lxml').find(
                'nav', {'id': 'pages'}).find_all('a')[-2].text)

        return (page_source, page_max) if get_page_max else page_source

    def _get_city_average(self, page_source):
        soup = BeautifulSoup(page_source, 'html.parser')
        scores = soup.find('table', id='tablonotes').find_all('td')
        city_average = {crit: score.text for crit,
                        score in zip(VilleIdeale.CRITERIA, scores)}
        average_score = soup.find('p', id='ng').text.split('/')[0].strip()
        city_average["average_score"] = average_score
        return city_average

    def _get_page_comment(self, page_source):
        page_info = {}
        index = 0
        r = re.compile(r"[0-9]{2}-[0-9]{2}-[0-9]{4}")
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
                       score in zip(VilleIdeale.CRITERIA, scores)}
            page_info[index].update(d_score)
            index += 1

        page_info = pd.DataFrame.from_dict(page_info, orient='index')
        return page_info

    def _get_city_info(self, id_city, info):
        url = self._create_url(id_city)

        if info == "comment":
            city_info = []
            page_source, page_max = self._get_page_source(
                url, get_page_max=True)
            page_info = self._get_page_comment(page_source)
            city_info.append(page_info)
            time.sleep(self.time_sleep)
            for page in range(2, page_max+1):
                url = self._create_url(id_city, page=page)
                page_source = self._get_page_source(url)
                page_info = self._get_page_comment(page_source)
                city_info.append(page_info)
                time.sleep(self.time_sleep)
            city_info = pd.concat(city_info, ignore_index=True)
        elif info == "average":
            page_source = self._get_page_source(url)
            city_info = self._get_city_average(page_source)

        return city_info

    def download(self, cities, info="average", to_dataframe=True):
        """
        Download cities information.

        Parameters:
        -----------
        cities: list, str
            Cities of interest.
        info: str, "average" or "comment", default: "average"
            Whether to download the average scores of the city (defaults) or
            comments of the city (i.e. the comments as well as the associated
            indivuals scores).
        to_dataframe: bool, default: True
            Whether to return a pandas DataFrame or a dict.
        """
        self.cities = cities
        self.n_cities = len(cities)
        output = {}

        if self.verbose:
            cities = tqdm(cities)

        if info == "comment":
            for city in cities:
                city_info = self._get_city_info(city, info=info)
                output[city] = city_info
        elif info == "average":
            for city in cities:
                city_info = self._get_city_info(city, info=info)
                output[city] = city_info

        if to_dataframe:
            if info == "comment":
                output = pd.concat(output, axis=0).reset_index(drop=True)
            elif info == "average":
                output = pd.DataFrame.from_dict(output, orient="index")
                output = output.reset_index().rename(columns={"index": "city"})

        if self.driver is not None and self.close_driver:
            self.close()

        return output

    @staticmethod
    def create_webdriver(driver_path=None, active_options=False, proxy=None):

        if active_options:
            options = Options()
            options.add_argument('--headless')
        else:
            options = None

        if driver_path is not None:
            path_driver = driver_path
        else:
            path_driver = 'geckodriver'
        driver = webdriver.Firefox(
            executable_path=path_driver, options=options)

        return driver
