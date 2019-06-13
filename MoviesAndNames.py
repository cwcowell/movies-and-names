import os
import pickle
import re
import sys
import zipfile

import pandas as pd
import requests
from bs4 import BeautifulSoup

START_YEAR = 1880
END_YEAR = 2018
POPULARITY_WINDOW = 1

MAX_CHARS_PER_MOVIE = 10

NAME_BLACKLIST = ['1st',
                  'admiral',
                  'adolescent',
                  'adult',
                  'agent',
                  'airport',
                  'aunt',
                  'captain',
                  'baroness',
                  'big',
                  'bike',
                  'blue',
                  'butler',
                  'buying',
                  'capt',
                  'carjacker',
                  'carnival',
                  'chancellor',
                  'chief',
                  'cmdr',
                  'col',
                  'college',
                  'colonel',
                  'constable',
                  'count',
                  'cpl',
                  '(credit',
                  'criminologist',
                  'deputy',
                  'det',
                  'director',
                  'doc',
                  'doorman',
                  'dr',
                  'drill',
                  'elder',
                  'emperor',
                  'father',
                  'fbi',
                  'female',
                  'first',
                  'fräulein',
                  'friend',
                  'gen',
                  'general',
                  'gov',
                  'governor',
                  'grand',
                  'great',
                  'herself',
                  'high',
                  'himself',
                  'hot',
                  'insp',
                  'inspector',
                  'king',
                  'lady',
                  'leader',
                  'lieutenant',
                  'little',
                  'lord',
                  'lt',
                  'madame',
                  'maestro',
                  'maj',
                  'magic',
                  'major',
                  'mayor',
                  'moff',
                  'monsieur',
                  'mr',
                  'mrs',
                  'narrator',
                  'nurse',
                  'of',
                  'officer',
                  'old',
                  'only)',
                  'orderly',
                  'pirate',
                  'police',
                  'president',
                  'prince',
                  'princess',
                  'professor',
                  'project',
                  'purplehaired',
                  'pvt',
                  'queen',
                  'quizmaster',
                  'rev',
                  'reverend',
                  'ringmaster',
                  'saloon',
                  'school',
                  '(segment',
                  'senator',
                  'sergeant',
                  'soloist',
                  'sgt',
                  'sheriff',
                  'ssgt',
                  'supreme',
                  'the',
                  'train',
                  'turkish',
                  'usaf',
                  'warden',
                  'woman',
                  'young',
                  '(voice)',
                  '/']

NAME_DATA_DIR = 'name_data'
NAME_DATA_SAMPLE_FNAME = 'yob1900.txt'
NAME_DATA_URL = 'https://www.ssa.gov/oact/babynames/names.zip'
NAME_DATA_ZIP_FNAME = 'names.zip'

THE_MOVIE_DB_API_KEY = '3d6eccec0139d67ab5299bc4c98ec777'

TITLES_AND_YEARS_HTML_FNAME = 'titles_and_years.html'
TITLES_AND_YEARS_URL = 'https://www.filmsite.org/boxoffice3.html'

PICKLED_CHARS_DIR = 'pickled_characters'


# --- NAME DATA ---

def get_name_data():
    if not name_data_files_exist():
        if not name_data_zip_exists():
            download_name_data_zip()
        unzip_name_data_zip()

    data = {}
    for year in range(START_YEAR, END_YEAR + 1):
        fpath = os.path.join(os.getcwd(), NAME_DATA_DIR, f'yob{year}.txt')
        names_df = pd.read_csv(fpath,
                               header=None,
                               names=['name', 'sex', 'num_births'],
                               usecols=['name', 'num_births'],
                               index_col='name')
        names_df['name'] = names_df['name'].str.lower()  # make all names lower case
        data[year] = names_df
    return data


def name_data_files_exist():
    # if we have one sample data file, assume we have them all
    return dir_exists(NAME_DATA_DIR) and file_exists(os.path.join(os.getcwd(), NAME_DATA_DIR, NAME_DATA_SAMPLE_FNAME))


def name_data_zip_exists():
    return file_exists(NAME_DATA_ZIP_FNAME)


def download_name_data_zip():
    print(f"downloading '{NAME_DATA_ZIP_FNAME}' from '{NAME_DATA_URL}'")
    response = requests.get(NAME_DATA_URL)
    status_code = response.status_code
    expected_status_code = 200
    if status_code != expected_status_code:
        sys.exit(f"got status code '{status_code}' instead of '{expected_status_code}' " +
                 f"when downloading '{NAME_DATA_ZIP_FNAME}' from '{NAME_DATA_URL}'")
    with open(NAME_DATA_ZIP_FNAME, 'wb') as zip_file:
        zip_file.write(response.content)


def unzip_name_data_zip():
    print(f"unzipping '{NAME_DATA_ZIP_FNAME}' into dir '{NAME_DATA_DIR}'")
    if not dir_exists(NAME_DATA_DIR):
        os.mkdir(NAME_DATA_DIR)

    with zipfile.ZipFile(NAME_DATA_ZIP_FNAME, 'r') as zip_file:
        zip_file.extractall(NAME_DATA_DIR)


def get_popularity(name_data, name, start_year, num_years=1):
    """ return percent, to two decimal places, of all births in the specified years that have the specified name """
    name_count = 0
    total_count = 0
    available_years = name_data.keys()

    end_year = start_year + num_years - 1
    for year in range(start_year, end_year + 1):
        if year in available_years:
            year_data = name_data[year]

            # if there are no records for a given name in a given year,
            # consider there to be 0 instances of that name that year
            try:
                # in case there are separate entries for male and female, add all counts for the name
                name_count_this_year = year_data.loc[name, 'num_births'].sum()
            except KeyError:
                name_count_this_year = 0

            total_count_this_year = year_data['num_births'].sum()
            name_count += name_count_this_year
            total_count += total_count_this_year

    popularity = round(name_count / total_count * 100, 2)
    return popularity


# --- CHARACTER DATA ---

def get_character_data():
    """ character data is a list of dicts with keys: movie, year, character """
    titles_and_years = get_titles_and_years()
    character_data = []
    for title, year in titles_and_years:
        characters_from_one_movie = get_characters_in_movie(title, year)
        character_data_entry = {'title': title,
                                'year': year,
                                'characters': characters_from_one_movie}
        character_data.append(character_data_entry)
    return character_data


def get_titles_and_years():
    if not file_exists(TITLES_AND_YEARS_HTML_FNAME):
        download_titles_and_years_html()
    titles_and_years = parse_titles_and_years_html()
    return titles_and_years


def download_titles_and_years_html():
    response = requests.get(TITLES_AND_YEARS_URL)
    status_code = response.status_code
    expected_status_code = 200
    if status_code != expected_status_code:
        sys.exit(f"got status code '{status_code}' instead of '{expected_status_code}' " +
                 f"when downloading '{TITLES_AND_YEARS_HTML_FNAME}' from '{TITLES_AND_YEARS_URL}'")
    html = response.text
    with open(TITLES_AND_YEARS_HTML_FNAME, 'w') as titles_and_years_html_file:
        titles_and_years_html_file.write(html)


def parse_titles_and_years_html():
    with open(TITLES_AND_YEARS_HTML_FNAME, 'r') as titles_and_years_html_file:
        titles_and_years_html = titles_and_years_html_file.read()

    soup = BeautifulSoup(titles_and_years_html, 'html.parser')
    div = soup.find(id='mainBodyWrapper')
    all_movie_details_raw = div.find_all('li')
    all_movie_details = [one_movie_details_raw.get_text() for one_movie_details_raw in all_movie_details_raw]
    all_movie_details = replace_substring_in_all_movie_details(all_movie_details, '\n', ' ')
    all_movie_details = replace_substring_in_all_movie_details(all_movie_details, '[ ]+', ' ')
    all_movie_details = replace_substring_in_all_movie_details(all_movie_details, '^ ', '')
    all_movie_details = replace_substring_in_all_movie_details(all_movie_details, ',', '')

    titles_and_years = []
    for single_movie_details in all_movie_details:
        details_regex = re.compile(r'^(.+?) \((\d+)')  # group #1 is title, group #2 is year
        match = details_regex.match(single_movie_details)
        title = match.group(1)
        year_as_str = match.group(2)
        year = int(year_as_str)
        titles_and_years.append((title, year))
    return titles_and_years


def replace_substring_in_all_movie_details(all_movie_details, old_regex, new_char):
    return [replace_substring(one_movie_details, old_regex, new_char) for one_movie_details in all_movie_details]


def replace_substring(text, old_regex, new_char):
    return re.sub(old_regex, new_char, text)


def replace_char(text, old_regex, new_char):
    return re.sub(old_regex, new_char, text)


def get_characters_in_movie(title, year):
    download_characters_from_movie(title, year)
    return parse_characters_file(title)


def download_characters_from_movie(title, year):
    if not dir_exists(PICKLED_CHARS_DIR):
        os.mkdir(os.path.join(os.getcwd(), PICKLED_CHARS_DIR))

    pickled_chars_fname = f'{title}.pickle'
    pickled_chars_fpath = os.path.join(os.getcwd(), PICKLED_CHARS_DIR, pickled_chars_fname)

    if not file_exists(pickled_chars_fpath):
        url = f'https://api.themoviedb.org/3/search/movie?query={title}&year={year}&api_key={THE_MOVIE_DB_API_KEY}'
        response = requests.get(url)
        movie_id = response.json()['results'][0]['id']

        # use the movie's ID to get the movie's cast
        url = f'https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={THE_MOVIE_DB_API_KEY}'
        response = requests.get(url)
        cast = response.json()['cast']

        # pickle the movie's entire cast so we don't have to spam the API during development
        with open(pickled_chars_fpath, 'wb') as pickled_chars_file:
            print(f'pickling cast of {title}')
            pickle.dump(cast, pickled_chars_file)


def parse_characters_file(title):
    pickled_chars_fname = f'{title}.pickle'
    pickled_chars_fpath = os.path.join(os.getcwd(), PICKLED_CHARS_DIR, pickled_chars_fname)
    with open(pickled_chars_fpath, 'rb') as pickled_chars_file:
        all_character_data = pickle.load(pickled_chars_file)
        main_characters = []
        for one_character_data in all_character_data[:MAX_CHARS_PER_MOVIE]:
            one_character_full_name = one_character_data['character']
            one_character_first_name = extract_first_name(one_character_full_name)
            if (one_character_first_name not in main_characters) and (one_character_first_name != ''):
                main_characters.append(one_character_first_name)
        return main_characters


def extract_first_name(full_name):
    full_name = replace_char(full_name, '/', ' ')  # break up characters that are listed like "sam/bill"
    split_name = [name_part.lower() for name_part in full_name.split()]
    for name_part in split_name:
        name_part = replace_char(name_part, '\.', '')
        name_part = replace_char(name_part, '-', '')
        name_part = replace_char(name_part, 'é', 'e')
        name_part = replace_char(name_part, 'è', 'e')
        name_part = replace_char(name_part, "'", '')
        if name_part not in NAME_BLACKLIST:
            return name_part
    return ''


# --- UTILS ---

def dir_exists(path):
    return os.path.exists(path) and os.path.isdir(path)


def file_exists(path):
    return os.path.exists(path) and os.path.isfile(path)


# --- MAIN ---

name_data = get_name_data()
character_data = get_character_data()
# for name_year in range(START_YEAR, END_YEAR + 1):
#     print(f'{name_year}: {get_popularity(name_data, "Michael", name_year, 2)}%')
# for entry in character_data:
#     print(entry)

for one_movie_data in character_data:
    title = one_movie_data['title']
    release_year = one_movie_data['year'] + 1
    characters = one_movie_data['characters']

    for character in characters:
        pre_release_popularity = get_popularity(name_data, character, release_year - 1)
        post_release_popularity = get_popularity(name_data, character, release_year + 1, POPULARITY_WINDOW)
        print(character, pre_release_popularity, post_release_popularity)
