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
texts_in_a = re.compile(r'\>(.*)\</a\>')

def extract_calories(fmt_str):
    cal = texts_in_p.findall(fmt_str)[0].strip('Kcal').replace(',', '')
    try:
        cal = int(cal)
    except ValueError:
        # print(fmt_str)
        pass
    return cal

def extract_img_name(entry):
    name, src = "", ""
    img = entry.select('img')
    if len(img) == 1:
        if 'alt' in img[0].attrs:
            name = img[0]['alt']

        if 'src' in img[0].attrs:
            src = img[0]['src']
    else:
        raise ValueError(f'img object(s) {img}')
    return name, src


def extract_cal_ingrd(soup_content):
    cal, ingrd = 0, ''
    try:
        assert len(soup_content) > 2, soup_content
    except:
        # raise ValueError(f'Empty contents: {soup_content}')
        print(f'Empty contents: {soup_content}')
        return cal, ingrd
    
    check_cal = extract_calories(str(soup_content[0]))
    if type(check_cal) is int:
        cal = check_cal
        ingrd = texts_in_p.findall(str(soup_content[1]))[0]
    else:
        cal = extract_calories(str(soup_content[1]))
        ingrd = texts_in_p.findall(str(soup_content[2]))[0]

    return cal, ingrd


# start reading stuff
base_url = 'https://meetfresh.us'
menu_url = base_url + '/menu/'

# Pretend to be a web browser by changing the user-agent header in your request.
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

response = requests.get(menu_url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')


# let's try constructing a new table
prod_df = pd.DataFrame(columns=['Name', 'Link', 'Image', 'Calories', 'Ingredients'])

problematic_df_rows = []

row_index = 0

for i, entry in enumerate(soup.select('div.hover-wrap-inner')):
    # Add an empty row
    prod_df.loc[row_index] = [np.nan] * 5
    # for the next row
    add_row = True

    # find image
    img = entry.select('img')
    try:
        name, src = extract_img_name(entry)
    except ValueError:
        print(i, 'weird img, len(img)=', len(img))
        add_row = False
        continue
    prod_df.loc[row_index, 'Name'] = name
    prod_df.loc[row_index, 'Image'] = src  

    # find href
    a = entry.select('a')
    if len(a) == 1:
        if 'href' in a[0].attrs:
            link = a[0]['href']
            # check if it's combo:
            if 'combos' in link:
                # # sanity check
                # a_text = texts_in_a.findall(str(a[0]))[0]
                # assert 'Series' in a_text, a_text

                # read further, and overwrite current row
                combo_response = requests.get(link, headers=headers)
                combo_soup = BeautifulSoup(combo_response.content, 'html.parser')
                for j, combo in  enumerate(combo_soup.select('div.hover-wrap-inner')): 
                    if prod_df.shape[0] == row_index:
                        # Add an empty row
                        prod_df.loc[row_index] = [np.nan] * 5
                    # within this loop
                    add_row_here = True            
                    # find image
                    img = combo.select('img')
                    try:
                        name, src = extract_img_name(combo)
                    except ValueError:
                        print(i, 'weird img, len(img)=', len(img))
                        add_row_here = False
                        continue
                    prod_df.loc[row_index, 'Name'] = name
                    prod_df.loc[row_index, 'Image'] = src

                    # find href
                    a_here = combo.select('a')
                    if len(a_here) == 1:
                        a_here = a_here[0]
                    else:
                        print(f'weird a object, len(a)={len(a)}')
                        continue
                    if 'href' in a_here.attrs:
                        combo_link = a_here['href']
                        prod_df.loc[row_index, 'Link'] = combo_link
                        this_combo_soup = BeautifulSoup(requests.get(combo_link, 
                                                                     headers=headers).content, 
                                                        'html.parser')
                        sub_contents = this_combo_soup.select('div.wpb_wrapper > p')  
                        try:                     
                            cal, ingrd = extract_cal_ingrd(sub_contents)
                        except Exception as e:
                            print(e)
                            problematic_df_rows.append(row_index)
                            cal, ingrd = 0, ''
                        prod_df.loc[row_index, 'Calories'] = cal
                        prod_df.loc[row_index, 'Ingredients'] = ingrd          
                    if add_row_here:
                        # increment
                        row_index += 1
                # end for-loop for products in series
            else:
                prod_df.loc[row_index, 'Link'] = link
                # grep more
                prod_response = requests.get(link, headers=headers)
                prod_soup = BeautifulSoup(prod_response.content, 'html.parser')
                # retrieve info
                contents = prod_soup.select('div.wpb_wrapper > p')
                try:
                    cal, ingrd = extract_cal_ingrd(contents)
                except Exception as e:
                    print(e)
                    problematic_df_rows.append(row_index)
                    cal, ingrd = 0, ''
                prod_df.loc[row_index, 'Calories'] = cal
                prod_df.loc[row_index, 'Ingredients'] = ingrd               
        else:
            print(i, row_index, a[0].attrs)
            add_row = False
    else:
        print(i, row_index, 'no <a> entry', a)
        add_row = False
        continue
    
    if add_row:
        # increment
        row_index += 1

# now let's see...
print(prod_df.shape)        
# print(prod_df.head(2))    
# print(type(prod_df))    

# fill in the blanks
def grep_name_from_link(name_link):
    assert name_link is not np.nan, name_link
    name = [w for w in name_link.split("/") if w != '']
    name = [w.capitalize() for w in name[-1].split("-")]
    name = ' '.join(name)
    # double check on other values
    name_response = requests.get(name_link, headers=headers)
    name_soup = BeautifulSoup(name_response.content, 'html.parser')
    # retrieve info
    name_contents = name_soup.select('div.wpb_wrapper > p')
    cal, ingrd = extract_cal_ingrd(name_contents)
    return name, cal, ingrd

print(problematic_df_rows)
print(prod_df.loc[problematic_df_rows, 'Name'].unique())

rows_to_remove = []
for i, row in prod_df.iterrows():
    if row.isnull().all():
        rows_to_remove.append(i)
    elif prod_df.loc[i, 'Name'] in ['Meet Fresh Arcadia Order Online', 'Meet Fresh App']:
        rows_to_remove.append(i)
    elif 'store' in prod_df.loc[i, 'Link'] or 'fresh-app' in prod_df.loc[i, 'Link']:
        rows_to_remove.append(i)
    elif prod_df.loc[i, 'Name'] == 'Crystal Mochi Milk Shaved Ice':
        # manual edit
        fix_link = 'https://meetfresh.us/crystal-mochi-milk-shaved-ice/'
        prod_df.loc[i, 'Link'] = fix_link
        meh, cal, ingrd = grep_name_from_link(fix_link)
        prod_df.loc[i, 'Calories'] = cal
        prod_df.loc[i, 'Ingredients'] = ingrd
    elif prod_df.loc[i, 'Link'].endswith("preview=true"):
        # manual edit
        fix_link = "https://meetfresh.us/icy-taro-ball-combo-a/"
        prod_df.loc[i, 'Link'] = fix_link
        meh, cal, ingrd = grep_name_from_link(fix_link)
        prod_df.loc[i, 'Calories'] = cal
        prod_df.loc[i, 'Ingredients'] = ingrd
    elif prod_df.loc[i, 'Name'] == '': # or prod_df.loc[i, 'Ingredients'] == ''
        # print(i, print(prod_df.iloc[i, -3:]))
        name_link = prod_df.loc[i, 'Link']
        if 'store' in name_link or 'app' in name_link:
            rows_to_remove.append(i)
        name, cal, ingrd = grep_name_from_link(name_link)
        prod_df.loc[i, 'Name'] = name
        prod_df.loc[i, 'Calories'] = cal
        prod_df.loc[i, 'Ingredients'] = ingrd


print(rows_to_remove, prod_df.loc[rows_to_remove])

print(prod_df.shape)
prod_df = prod_df.drop(rows_to_remove)
print(prod_df.shape)
# make sure calories are int
prod_df['Calories'] = prod_df['Calories'].astype(int)

# save
prod_df.to_csv('menu_items_v2.csv', index=False)