# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 11:33:26 2026

@author: simme
"""

# produces descriptive statistics

# import necessary packages
import geopandas as gpd
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import itertools
from scipy.stats import ttest_ind, shapiro, mannwhitneyu

# import mapping packages
import matplotlib.pyplot as plt
from matplotlib.pyplot import subplots, savefig, close

#%% =============== READING IN DATA ==================


spray_data = pd.read_excel('../MY_INPUTS/raw_spray_join_left.xlsx')
spray_data = spray_data.rename({'layer_y': 'Region'}, axis=1)

raw_spray = pd.read_excel('../MY_INPUTS/filtered_trap_raw.xlsx')

# filling the index
raw_spray['Area'] = raw_spray['Area'].ffill()
raw_spray = raw_spray.rename({'layer_y': 'Region'}, axis=1)
raw_spray = raw_spray.set_index(['Area', 'N. of Trap', 'Region'])


spray_data['Area'] = spray_data['Area'].ffill()
spray_data['N. of Trap'] = spray_data['N. of Trap'].ffill()

spray_data['Season'] = np.nan

#%% =============== FILTERING BY SEASON ==================

 #so maybe one season from 6th of june to 25th of july
#then 25th of july to 12th of sept
#then 12th of sept to 31st of oct (then each is 49 days exactly)

# NEEEEEEED TO FIX THESE DATA SELECTORS!!!! EARLY JULY SHOWS AS NOTHING, AUTUMN MAYBE ALSO TOO
#spring_dates = (
 #   ((spray_data['d'].dt.month == 6) & (spray_data['d'].dt.day >= 5)) |
  #   ((spray_data['d'].dt.month == 7) & (spray_data['d'].dt.day < 25))
   #  )
    
#spray_data.loc[spring_dates, 'Season'] = 'Spring'

#summer_dates = (
#    ((spray_data['d'].dt.month == 7) & (spray_data['d'].dt.day >= 25)) |
 #    (spray_data['d'].dt.month == 8) |
  #   ((spray_data['d'].dt.month == 9) & (spray_data['d'].dt.day < 12))
   #  )

#spray_data.loc[summer_dates, 'Season'] = 'Summer'        
        
#autumn_dates = (
#    ((spray_data['d'].dt.month == 9) & (spray_data['d'].dt.day >= 12)) |
 #    (spray_data['d'].dt.month == 10)
  #   )

#spray_data.loc[autumn_dates, 'Season'] = 'Autumn'

spray_data = spray_data.set_index(['Area', 'N. of Trap', 'Region'])

# convert to int format
index = spray_data.reset_index()
index.iloc[:, 1] = index.iloc[:, 1].astype(int)

spray_data = index.set_index(spray_data.index.names)

#%%    
sprayed_data = []

#spray_columns = pd.MultiIndex.from_frame(
 #   desire_pivot[['Value', 'Region', 'Date', 'Spraying']]
    
    
   # [['Change (25 days)'],
  #   ['Καλλιθέα', 'Μαραθόκαμπος', 'Καρλόβασι', 'Πύργος',
 #     'Πυθαγόρειο', 'Κοκκάρι', 'Μυτιληνιοί', 'Βαθύ'],
#     ['2024-06-27', '2023-10-15', '2023-09-03', '2023-10-18', '2023-06-29', '2024-10-01',
    # '2024-06-16', '2023-07-29','2023-06-26','2022-09-26','2023-09-21','2024-06-17',
     #'2023-09-20','2024-06-14','2023-07-26','2023-06-21','2024-09-16',
    # '2024-06-15','2023-10-23','2023-09-22','2023-07-27','2022-10-14','2023-10-24',
   #  '2023-06-22','2023-10-22','2023-09-08','2022-10-13','2023-06-25','2024-07-10',
  #   '2024-10-10', '2024-10-07','2024-10-04','2023-10-29','2023-09-09','2024-09-19',
 #    '2023-06-30','2024-07-11','2024-06-18','2023-06-28','2024-09-30','2023-07-28',
     #'2022-09-25','2024-07-12','2022-10-06','2022-10-07','2023-10-16','2022-10-08',
    # '2024-06-19','2024-06-13', '2023-06-27', '2023-09-05','2022-09-23','2022-09-27',
   #  '2023-10-17','2024-07-02','2023-10-13','2023-07-12', '2024-10-06','2024-07-01',
  #   '2023-07-11','2024-06-30','2023-07-10','2024-07-03', '2022-10-09','2024-07-04',
 #    '2023-10-20','2023-10-10',  '2023-09-15','2023-07-30','2023-07-02', '2022-10-10',
   #  '2023-09-11',  '2024-10-09', '2024-09-18', '2023-10-12', '2023-09-12',
    # '2024-07-05',  '2023-07-31', '2023-07-03', '2023-09-23','2024-10-02','2022-10-12',
  #   '2024-07-08', '2024-10-03', '2023-10-21', '2023-06-20', '2024-07-09','2023-09-24','2023-07-01',
  #   '2022-10-11', '2023-09-14','2023-09-10', '2023-07-04','2023-10-11',
 #    '2022-09-24','2024-07-06','2024-10-08','2023-10-19', '2024-07-07', '2023-07-05'],
    # ['Sprayed', 'Unsprayed']
   #  ],
    
  #  names = ['Value', 'Region', 'Date', 'Spraying'])

#data_store = pd.DataFrame(columns=spray_columns)
#print(data_store)

# make a list of all spraying data
spraying_list = spray_data['d'].dropna().unique()


# filter out the columns that are labelled with a date
date_cols = raw_spray.columns[pd.to_datetime(raw_spray.columns, errors='coerce').notna()] 
# define a standard set of labels
expect_labels = ['-5 Days', '0 Days', '5 Days',
                '10 Days', '15 Days', '20 Days']

# create a loop to extract only data near the spray date
for row in spraying_list:
     
    # define the index
    #area, trap, region, season = idx
    # select the spray date of the site

    # define a start date 15 days before spraying
    start = row - pd.Timedelta(days=6)
    
    # define an end date 15 days after spraying
    end = row + pd.Timedelta(days=21)
    # only select columns within this 30 day range
    select_cols = date_cols[(date_cols >= start) & (date_cols <= end)]
    
    # get which areas were sprayed on that date
    arees = spray_data.index[spray_data['d'] == row].get_level_values('Region').unique()
    
    # define the start and end of the window of not overlapping
    # spraying
    row_start = row - pd.Timedelta(days=20)
    row_end = row + pd.Timedelta(days=20)
    
    # set interval day
    delta_w = 'D'
    
    # make a list of all dates in this no overlap window &
    # remove the spraying date
    date_list = pd.date_range(row_start, row_end, freq=delta_w)
    date_list_clean = date_list[date_list != row]

    
    # convert to array
    select_area = arees.to_numpy()
    
    area_list = raw_spray.index.get_level_values(2)
    
    # take the values from within this range
    mask = area_list.isin(select_area)

    # select only the rows that match the region of the set row
    desired_values = raw_spray.loc[mask, select_cols]
    
    areas_2_choose = spray_data.index.get_level_values(2)
     
    mask2 = areas_2_choose.isin(select_area)

    
    spray_mark2 = spray_data.loc[mask2]
    
    # creating an index of rows where the date of buffer intersection
    # is the chosen date (i.e., spraying date)
    # set by default points as unsprayed
    desired_values['Spraying'] = 'Unsprayed'
    
    # group by index
    grouping = spray_mark2.groupby(level=[0, 1, 2])['d']
    
    # if there is any case in the point where it's the spraying
    # date, keep that
    is_spray_date = grouping.apply(lambda spr: (spr == row).any())
    
    # then, if there's any case where it's in the no overlap
    # window, keep that
    in_date_list = grouping.apply(lambda spr: spr.isin(date_list_clean).any())
    
    # find index locs where either above condition is true                              
    exclude_choose = desired_values.index[in_date_list & ~is_spray_date]
    sprayed_choose = desired_values.index[is_spray_date]

    # if points' spraying date matches row, mark them as sprayed
    desired_values.loc[sprayed_choose, 'Spraying'] = 'Sprayed'
    desired_values.loc[exclude_choose, 'Spraying'] = np.nan
 
    # mark the spraying date
    desired_values['Date'] = row

    # mark unsprayed rows as unsprayed
    desired_values = desired_values.dropna(subset='Spraying')

    # update the index
    desired_values = desired_values.set_index(['Spraying', 'Date'], append=True)
    
    # convert this to datetime
    select_cols_datetime = pd.DatetimeIndex(select_cols)
        
    # define an offset from the spraying date
    offset = np.round((select_cols_datetime - row).days / 5) * 5
    offset = offset.astype(int)

    # set the week name to be this offset
    desired_values.columns = [f'{week} Days' for week in offset]
    
    # reindex the columns to standard labels
    desired_values = desired_values.reindex(columns=expect_labels)

    # compare % change for 10 days before & after spraying
    desired_values['Change (25 days)'] = (
        (desired_values['20 Days'] -
        desired_values['-5 Days']).replace(0, np.nan))
    

    # reset the index to make columns
    desire_wipe = desired_values.reset_index()
    
    # pivot the dataset for harmonisation with overall store
    desire_pivot = desire_wipe.pivot(index=None, columns=['Region', 'Spraying'],
                                        values=['Change (25 days)'])
    
    #^ can also do the above with index=['Area', 'N. of Trap', 'Date']
    
    spray_order = pd.CategoricalIndex(
        desire_pivot.columns.get_level_values('Spraying'),
        categories=['Sprayed','Unsprayed'],
        ordered=True)
    
    desire_pivot.columns = desire_pivot.columns.set_levels(
        spray_order.categories, level='Spraying')
    
    desire_pivot = desire_pivot.sort_index(axis=1)
    
    sprayed_data.append(desire_pivot) 

    
 # convert into a dataframe   
data_store = pd.concat(sprayed_data)


#data_store = data_store.reindex(columns=spray_columns)

# ----------- OUTPUT 1 --------------------

# label the different levels of the header
data_store.columns.names = ['Value', 'Region', 'Spraying']

data_store.to_excel('./testforcheck.xlsx')
# =================== statistical test ==============================
#%% student t-test

# create a dictionary
descriptive_results = {}

for region, occurrence in data_store.items():
    
    name = region[1], region[2]
    region_idx = name
    df_describe = pd.DataFrame(occurrence)
    desc = df_describe.describe()
    desc['sum'] = occurrence.sum()
    descriptive_results[region_idx] = desc

# convert to an excel file with a sheet for each year
with pd.ExcelWriter('./desc_stats_per_region_34days.xlsx') as writer:
    for regional, dataframe in descriptive_results.items():
        dataframe.to_excel(writer, sheet_name=str(regional))
