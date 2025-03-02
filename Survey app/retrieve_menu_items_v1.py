'''This script extracts menu items from meet fresh website'''
# basic packages
import numpy as np
import pandas as pd
import re

# Disable all warnings
import warnings
warnings.filterwarnings('ignore')
# warnings.filterwarnings('ignore', category='SettingWithCopyWarning')
# warnings.filterwarnings('ignore', category=DeprecationWarning)

# web crawler
import requests
from bs4 import BeautifulSoup
import csv

# helper functions
texts_in_p = re.compile(r'\>(.*)\</p\>')

def extract_calories(fmt_str):
    cal = texts_in_p.findall(fmt_str)[0].strip('Kcal').replace(',', '')
    try:
        cal = int(cal)
    except ValueError:
        # print(fmt_str)
        pass
    return cal


# start reading stuff
base_url = 'https://meetfresh.us'
menu_url = base_url + '/menu/'

# Pretend to be a web browser by changing the user-agent header in your request.
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

response = requests.get(menu_url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

# retrieve images with links first
product_links = soup.select('div.hover-wrap-inner > a')
product_images = soup.select('div.hover-wrap-inner > a > img')
assert len(product_links) == len(product_images)

# now assemble the 31 products that have both href and images and names
products = [[product_images[i]['alt'], 
             product_links[i]['href'], 
             product_images[i]['src']] for i in range(len(product_images))]
products = pd.DataFrame(products)
products.columns= ['Name', 'Link', 'Image']
# print(products.head(3))

# go into each link & read cal & ingrd
## make placeholders for calories and ingredients:
products['Calories'] = np.zeros(len(products), dtype=int)
products['Ingredients'] = pd.Series([np.nan] * len(products), dtype='object')

def extract_prod_info(soup_content, products_i):
    try:
        assert len(soup_content) > 2, soup_content
    except:
        print(products_i['Name'], 'skip')
        raise ValueError(f'Empty contents: {soup_content}')
    
    check_cal = extract_calories(str(soup_content[0]))
    if type(check_cal) is int:
        products_i['Calories'] = check_cal
        products_i['Ingredients'] = texts_in_p.findall(str(soup_content[1]))[0]
    else:
        products_i['Calories'] = extract_calories(str(soup_content[1]))
        products_i['Ingredients'] = texts_in_p.findall(str(soup_content[2]))[0]
    return products_i

problematic_rows = []

for i, link in enumerate(products['Link']):
    prod_response = requests.get(link, headers=headers)
    prod_soup = BeautifulSoup(prod_response.content, 'html.parser')
    # retrieve info
    contents = prod_soup.select('div.wpb_wrapper > p')
    try:
        products.iloc[i] = extract_prod_info(contents, products.iloc[i])
    except ValueError:
        # print(contents[1:3])
        problematic_rows.append(i)

print('problematic rows:', problematic_rows)

# remove 28, 29
products = products.drop([28, 29])

print('Before:', products.iloc[20])
# manually edit this one
link = 'https://meetfresh.us/crystal-mochi-milk-shaved-ice/'
products.loc[20, 'Link'] = link
prod_response = requests.get(link, headers=headers)
prod_soup = BeautifulSoup(prod_response.content, 'html.parser')
# retrieve info
contents = prod_soup.select('div.wpb_wrapper > p')
products.iloc[20] = extract_prod_info(contents, products.iloc[20])
## double check
products.loc[20, 'Ingredients'] = texts_in_p.findall(str(contents[2]))[0]
print('After:', products.iloc[20])
# write things out
products.to_csv('menu_items_v1.csv')