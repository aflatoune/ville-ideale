import argparse
import pandas as pd
from utils.villeideale import VilleIdeale


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--selenium", action="store_true",
                        help="Whether to use selenium or not.")
    return parser.parse_args()


def read_city_list(path, n=20):
    city_list = pd.read_csv(path, sep=";", index_col=0)

    if n > city_list.shape[0]:
        n = city_list.shape[0]

    cities = city_list.id_city[:n]
    return cities


def update_city_list(path, n):
    city_list = pd.read_csv(path, sep=";", index_col=0)
    city_list = city_list.iloc[n:]
    city_list.to_csv(path, sep=";", encoding='utf-8')


def update_city_info(path, df):
    with open(path, "a") as file:
        df.to_csv(file, header=file.tell() == 0)


def main():
    args = parse_arguments()
    selenium = args.selenium

    if selenium:
        driver = VilleIdeale.create_webdriver()
        vi = VilleIdeale(driver=driver, verbose=False)
    else:
        vi = VilleIdeale(verbose=False)

    cities = read_city_list("data/city_list.csv")
    output = vi.download(cities)
    update_city_list("data/city_list.csv", n=output.shape[0])
    update_city_info("data/city_info.csv", output)


if __name__ == "__main__":
    main()
