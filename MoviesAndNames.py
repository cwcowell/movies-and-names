from bs4 import BeautifulSoup
import os
import pandas as pd
import re
import requests

START_YEAR = 1880
END_YEAR = 2017
POPULARITY_WINDOW = 1


# --- name data ---

def download_name_data():
    # add code to download zip file from gov site
    # add code to unzip data
    pass


def read_name_data():
    data = {}
    for year in range(START_YEAR, END_YEAR + 1):
        fpath = os.path.join(os.getcwd(), 'names', f'yob{year}.txt')
        names_df = pd.read_csv(fpath,
                               header=None,
                               names=['name', 'sex', 'num_births'],
                               usecols=['name', 'num_births'],
                               index_col='name')
        data[year] = names_df
    return data


def get_popularity(data, name, year):
    """ return percent, to two decimal places,
    of all births in the specified year that have the specified name """
    name_count = 0
    total_count = 0
    year_data = data[year]

    # in case there are separate entries for male and female, add all counts for the name
    name_count_this_year = year_data.loc[name, 'num_births'].sum()
    total_count_this_year = year_data['num_births'].sum()

    name_count += name_count_this_year
    total_count += total_count_this_year

    return round(name_count / total_count * 100, 2)


# --- character data ---

def download_character_data():
    download_top_titles_and_years()
    # return download_characters(title_and_year_data)
    # return character_data


def download_top_titles_and_years():
    top_titles_html_fname = 'top100films.html'
    top_titles_fname = 'top100films.csv'

    download_html(top_titles_html_fname)
    top_titles_data = parse_html(top_titles_html_fname)
    write_top_titles(top_titles_data, top_titles_fname)


def download_html(fname):
    if not os.path.isfile(fname):
        url = 'https://www.filmsite.org/boxoffice3.html'
        html = requests.get(url).text
        with open(fname, 'w') as html_file:
            html_file.write(html)


def parse_html(fname):
    with open(fname, 'r') as html_file:
        html = html_file.read()

    soup = BeautifulSoup(html, 'html.parser')
    div = soup.find(id='mainBodyWrapper')
    movie_details_with_markup = div.find_all('li')
    all_movie_details_text = [movie_details_with_markup.get_text().strip() for movie_details_with_markup in movie_details_with_markup]
    all_movie_details_text = [single_movie_details_text.replace('\n', ' ') for single_movie_details_text in all_movie_details_text]
    all_movie_details_text = [single_movie_details_text.replace('  ', '') for single_movie_details_text in all_movie_details_text]

    titles_years = []
    for single_movie_details_text in all_movie_details_text:
        details_regex = re.compile('^(.*)\((\d*)\)')  # group #1 is title, group #2 is year
        match = details_regex.match(single_movie_details_text)
        title = match.group(1)
        year = match.group(2)
        titles_years.append((title, year))
    print('hi')


def write_top_titles(top_titles_data, top_titles_fname):
    pass


def download_characters():
    pass


def read_character_data():
    data = {}
    for year in range(START_YEAR, END_YEAR + 1):
        fpath = os.path.join(os.getcwd(), 'characters', f'characters{year}.csv')
        # names_df = pd.read_csv(fpath,
        #                        header=None,
        #                        names=['name', 'sex', 'num_births'],
        #                        usecols=['name', 'num_births'],
        #                        index_col='name')
        # data[year] = names_df
    # return data
    return None


# --- MAIN ---

# name_data = read_name_data()
# for name_year in range(1880, 2017):
#     print(f'{name_year}: {get_popularity(name_data, "David", name_year)}%')

download_character_data()
# character_data = read_character_data()
print('hi')
