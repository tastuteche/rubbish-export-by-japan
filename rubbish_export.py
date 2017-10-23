import re
import sqlite3
import pandas.io.sql as psql
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# waste_hscode_list = []
# with open('waste_hscode.txt', 'r') as f:
#     text = f.read()
#     lines = text.split('\n')
#     for l in lines:
#         lst = re.findall('^(\d{6})\s+', l)
#         if len(lst) > 0:
#             print(lst[0])
#             waste_hscode_list.append(lst[0])


b_dir = './japan-trade-statistics/'
b0_dir = './custom-2016/'
b2_dir = "./japantradestatistics2/"
b3_dir = "./counties-geographic-coordinates/"

country = pd.read_csv(b_dir + 'country_eng.csv',
                      dtype={'Country': 'str', 'Country_name': 'str'})
country.index = country['Country']
custom = pd.read_csv(b_dir + 'custom.csv',
                     dtype={'Custom': 'str', 'd_name': 'str'})
last_year = 2016

hs9 = pd.read_csv(b_dir + "hs9_eng.csv",
                  dtype={'hs9': 'str'})
hs9.index = hs9['hs9']
waste_hscode_list = hs9[hs9['hs9_name'].str.contains('waste')]['hs9'].unique()
where_waste_hscode_list = 'hs9 in (' + ','.join(
    ['"%s"' % hscode for hscode in waste_hscode_list]) + ')'

# with sqlite3.connect(b_dir + 'ym_custom_' + str(last_year) + '.db') as conn:
# with sqlite3.connect(b0_dir + 'database.sqlite') as conn:
# last_df = pd.merge(last_df, country, on='Country')

# with sqlite3.connect(b_dir + 'year_1988_2015.db') as conn:
with sqlite3.connect(b2_dir + 'database.sqlite') as conn:
    sql = 'select exp_imp,Year,Country,Value from year_1988_2016 where ' + \
        where_waste_hscode_list
    year_df = pd.read_sql(sql, conn)

# with sqlite3.connect(b_dir + 'ym_custom_latest.db') as conn:


def group_by(year_df, by):
    year_df_by = pd.pivot_table(year_df,
                                index=by, columns='exp_imp', values='Value', aggfunc=np.sum)
    dict_col = {2: 'import', 1: 'export'}
    year_df_by.columns = [dict_col.get(col, col) for col in year_df_by.columns]
    year_df_by['import'].fillna(0, inplace=True)
    year_df_by['export'].fillna(0, inplace=True)
    year_df_by['net_export'] = year_df_by['export'] - year_df_by['import']
    return year_df_by


year_group = group_by(year_df, 'Year')
year_group.plot.bar(y=['export', 'import'], alpha=0.6, figsize=(12, 5))
plt.title('Rubbish Export Import By Japan')
# plt.show()
plt.savefig('rubbish_export_import_by_janpan.png', dpi=200)
plt.clf()
plt.cla()
plt.close()

with sqlite3.connect(b2_dir + 'database.sqlite') as conn:
    sql = 'select exp_imp,Year,Country,Value from year_1988_2016 where ' + \
        where_waste_hscode_list + ' and Year = 2016'
    year_2016_df = pd.read_sql(sql, conn)

country_group = group_by(year_2016_df, 'Country')
#country_group.plot.bar(y=['export', 'import'], alpha=0.6, figsize=(12, 5))


countries_df = pd.read_csv(
    b3_dir + "countries.csv", index_col="country")
countries_df = countries_df[countries_df.index != "UM"]

from mpl_toolkits.basemap import Basemap

import math


def draw_country_line(worldmap, c1, c2, val, min_delta, brush_factor, neg_color='r', pos_color='b'):
    if c2 not in countries_df.index:
        return
    delta = val
    if abs(delta) < min_delta:
        return
    x = (countries_df["longitude"][c1], countries_df["longitude"][c2])
    y = (countries_df["latitude"][c1], countries_df["latitude"][c2])
    color = pos_color if delta > 0 else neg_color
    w = math.sqrt(abs(delta)) * brush_factor
    #w = 1
    #worldmap.plot(x, y, latlon=True, linewidth=w, color=color)
    #, color=color
    worldmap.plot(*worldmap(x, y), linewidth=w)


from tabulate import tabulate


dict_c2_code = {"Macao": "Macau", "Viet_Nam": "Vietnam",
                "United_States_of_America": "United States"
                }


def plot_country_export_map(category, top_20, val_col, c1, min_delta, brush_factor):
    plt.figure(figsize=(20, 10))
    worldmap = Basemap()
    worldmap.drawcoastlines()
    worldmap.drawcountries()
    worldmap.fillcontinents()
    for c2, val in zip(top_20.Country_name, top_20[val_col].fillna(0)):
        c2 = dict_c2_code.get(c2, c2)
        c2_code = countries_df[countries_df['name'].str.contains(
            c2.replace('_', ' '))]
        if len(c2_code) > 0:
            c2 = c2_code.index[0]
            print(c2)
            draw_country_line(worldmap, c1, c2, val,
                              min_delta, brush_factor)
        else:
            print('%s not found in countries_df' % c2)
    plt.title(countries_df["name"][c1] + " %s Map" % category)
    # plt.show()
    plt.savefig('rubbish_%s_by_%s.png' %
                (val_col, countries_df["name"][c1]), dpi=200)
    plt.clf()
    plt.cla()
    plt.close()
    print(tabulate(top_20.set_index("Country_name").loc[:, [
          val_col]], tablefmt="pipe", headers="keys"))


top_net_export_20 = country_group.join(country).sort_values(
    'net_export', ascending=False).head(20)
plot_country_export_map(
    'Rubbish Net Export', top_net_export_20, 'net_export', 'JP', 0, 0.002)

top_import_20 = country_group.join(country).sort_values(
    'import', ascending=False).head(20)
plot_country_export_map(
    'Rubbish Import', top_import_20, 'import', 'JP', 0, 0.002)

top_export_20 = country_group.join(country).sort_values(
    'export', ascending=False).head(20)
plot_country_export_map(
    'Rubbish Export', top_export_20, 'export', 'JP', 0, 0.002)
