import os
import pickle
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup

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

def get_character_data():
    """ character data is a list of dicts with keys: movie, year, character """
    titles_years = get_titles_years()
    character_data = []
    for title, year in titles_years:
        characters_from_one_movie = get_characters_from_movie(title, year)
        character_data.append((title, year, characters_from_one_movie))
    return character_data


def get_titles_years():
    # don't download the HTML if it already exists on disk
    titles_years_html_fname = 'titles_and_years.html'
    if not os.path.isfile(titles_years_html_fname):
        print('downloading titles and years HTML')
        download_titles_years_html(titles_years_html_fname)
    else:
        print('titles and years HTML already eists on disk')
    titles_years = parse_titles_years_html(titles_years_html_fname)
    return titles_years


def download_titles_years_html(fname):
    url = 'https://www.filmsite.org/boxoffice3.html'
    html = requests.get(url).text
    with open(fname, 'w') as html_file:
        html_file.write(html)


def parse_titles_years_html(fname):
    print('parsing titles and years HTML')
    with open(fname, 'r') as html_file:
        html = html_file.read()

    soup = BeautifulSoup(html, 'html.parser')
    div = soup.find(id='mainBodyWrapper')
    all_movie_details_raw = div.find_all('li')
    all_movie_details = [one_movie_details_raw.get_text() for one_movie_details_raw in all_movie_details_raw]
    all_movie_details = replace_chars(all_movie_details, '\n', ' ')
    all_movie_details = replace_chars(all_movie_details, '[ ]+', ' ')
    all_movie_details = replace_chars(all_movie_details, '^ ', '')
    all_movie_details = replace_chars(all_movie_details, ',', ' ')

    titles_years = []
    for single_movie_details_text in all_movie_details:
        details_regex = re.compile(r'^(.+?) \((\d+)')  # group #1 is title, group #2 is year
        match = details_regex.match(single_movie_details_text)
        title = match.group(1)
        year = match.group(2)
        titles_years.append((title, year))
    print(f'  parsed {len(titles_years)} movies')
    return titles_years


def replace_chars(all_movie_details, old_regex, new_char):
    return [re.sub(old_regex, new_char, one_movie_details) for one_movie_details in all_movie_details]


def get_characters_from_movie(title, year):
    print(f'getting top chararacters in {title}')
    download_characters_from_movie(title, year)
    return parse_characters_file(title)


def download_characters_from_movie(title, year):
    api_key = '3d6eccec0139d67ab5299bc4c98ec777'
    pickle_dir = 'all_characters'
    pickle_fname = f'{title}.pickle'
    pickle_path = os.path.join(os.getcwd(), pickle_dir, pickle_fname)

    if not os.path.isfile(pickle_path):
        # get the movie's ID
        print(f'  getting ID of {title}')
        url = f'https://api.themoviedb.org/3/search/movie?query={title}&year={year}&api_key={api_key}'
        response = requests.get(url)
        movie_id = response.json()['results'][0]['id']

        # use the movie's ID to get the movie's cast
        print(f'  getting cast of {title}')
        url = f'https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={api_key}'
        response = requests.get(url)
        cast = response.json()['cast']

        # pickle the movie's entire cast so we don't have to spam the API during development
        with open(pickle_path, 'wb') as pickle_file:
            print(f'  pickling cast of {title}')
            pickle.dump(cast, pickle_file)
    else:
        print(f'  pickle file already exists for {title}')


def parse_characters_file(title):
    pickle_dir = 'all_characters'
    pickle_fname = f'{title}.pickle'
    pickle_path = os.path.join(os.getcwd(), pickle_dir, pickle_fname)
    with open(pickle_path, 'rb') as pickle_file:
        all_character_data = pickle.load(pickle_file)
        main_characters = []
        for one_character_data in all_character_data[:5]:
            one_character_full_name = one_character_data['character']
            one_character_first_name = one_character_full_name.split(' ')[0]
            main_characters.append(one_character_first_name)
        return main_characters


# --- MAIN ---

# name_data = read_name_data()
# for name_year in range(1880, 2017):
#     print(f'{name_year}: {get_popularity(name_data, "David", name_year)}%')

character_data = get_character_data()
print(character_data)
