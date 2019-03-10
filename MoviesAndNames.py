import os
import pandas as pd

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
    title_and_year_data = download_top_titles_and_years()
    character_data = download_characters(title_and_year_data)
    return character_data


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

character_data = read_character_data()
print('hi')
