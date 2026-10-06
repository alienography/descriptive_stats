# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 16:22:31 2026

@author: simme
"""
# import necessary packages
import pandas as pd
import geopandas as gpd
import numpy as np

# load in data
# read in olive fly number data
fly_numbers = pd.read_excel('../../Samos 2022-2024-20251120T120022Z-1-001/Samos 2022-2024/Traps Samos 2022-2024.xlsx',
                          sheet_name=['2022', '2023', '2024'], dtype={1: 'float64'}, header=[0, 1]
                          )

# reading in trap data
trap_data = pd.read_excel('../../Samos 2022-2024-20251120T120022Z-1-001/Samos 2022-2024/Traps Samos 2022-2024.xlsx',
                          sheet_name='2022', usecols=['Area', 'N. of Trap', 'Longitude', 'Latitude']#, header=[0, 1]
                          )

# read in regions of samos - DONE WITH FINISHED REGIONS
samos_regions = gpd.read_file('../MY_INPUTS/samos regions incl ikaria.gpkg')

# drop unnecessary columns
samos_regions = samos_regions.drop(['EKTASH', 'PERIMETROS'], axis=1)

# reproject samos regions
samos_regions = samos_regions.to_crs('EPSG:2100')


# set area and trap number as a multiindex
for sheet in fly_numbers:
    fly_numbers[sheet] = fly_numbers[sheet].set_index([('Area', 'Unnamed: 0_level_1'), 
                                                       ('N. of Trap', 'Unnamed: 1_level_1')]
                                                       )
 
# combine the different years into one year
merged_flies = pd.concat(fly_numbers.values(), axis=1)

# get rid of duplicate latitude, longitude & altitude columns
merged_flies = merged_flies.loc[:, ~merged_flies.columns.duplicated()]

# make the dataframe into point data with geometries
spray_data_gdb = gpd.GeoDataFrame(trap_data, geometry=gpd.points_from_xy(
                                  trap_data[('Longitude')],
                                  trap_data[('Latitude')]),
                                  crs='EPSG:4326')

# project to greek grid
spray_data_proj = spray_data_gdb.to_crs('EPSG:2100')

# join points with regions
trap_locale = gpd.sjoin(
    spray_data_proj,
    samos_regions,
    predicate='intersects')

# set indices to match
trap_locale = trap_locale.set_index(['Area', 'N. of Trap'])
merged_flies.index = merged_flies.index.set_names(['Area', 'N. of Trap'])

# merge the two datasets to give regions to the main dataset
merged_data = merged_flies.merge(
    trap_locale['layer'],
    left_index=True,
    right_index=True,
    how='left'
    )

# drop all points in Ikaria
samos_data = merged_data[
              merged_data['layer'] != 'Ικαρία']

# make columns into multiindex
samos_data.columns = [
    column if isinstance(column, tuple) else (column, '')
    for column in samos_data.columns
    ]


samos_data.columns = pd.MultiIndex.from_tuples(samos_data.columns)

# label the different levels of the header
samos_data.columns.names = ['Date', 'Type']

# ensuring the data is in datetime format
pd.to_datetime(samos_data.columns.get_level_values('Date'), errors='ignore')

# take out either total numbers or female fly numbers
total_cols = samos_data.columns[
              samos_data.columns.get_level_values('Type') != 'Female']  
female_cols = samos_data.columns[
              samos_data.columns.get_level_values('Type') != 'Total']

# seperating data on female/total flies
Female_data = samos_data[female_cols].copy()
total_data = samos_data[total_cols].copy()

# =================== DESCRIPTIVE STATISTICS ==============================
#%% ------------------- first, do overall -----------------------------------

# extract only the numerical columns
numbers = total_data.iloc[:, 3:90]

# reset the index to not have an issue with indices
#numbers = numbers.reset_index()
#numbers = numbers.drop([('Area', ''), ('N. of Trap', '')], axis=1)

# make sure the columns are datetime & make a multiindex
numbers.columns = pd.MultiIndex.from_arrays([
    pd.to_datetime(numbers.columns.get_level_values(0)),
    numbers.columns.get_level_values(1)
    ], names=numbers.columns.names)

# get the column names of the numerical columns & define a variable to store
numcolumns = numbers.columns.get_level_values(0)
years = numcolumns.year

# basically make all the data into one big long list for each year
year_values = {
    year: numbers.loc[:, years==year].to_numpy().ravel()
    for year in np.unique(years)
    }

# remove blank values
year_values = {
    year: vals[~np.isnan(vals)]
    for year, vals in year_values.items()
    }

# describe a dictionary to store descriptive statistics
desc_overall = {}

# go through the dictionaries generated above, and find descriptive
# statistics of these
for yearish, occurrence in year_values.items():
    
    year_idx = yearish
    df_describe = pd.DataFrame(occurrence)
    desc = df_describe.describe()
    desc['sum'] = occurrence.sum()
    desc_overall[year_idx] = desc
    
# convert to an excel file with a sheet for each year
with pd.ExcelWriter('../MY_OUTPUTS/desc_stats_year.xlsx') as writer:
    for yearyyzy, dataframe in desc_overall.items():
        dataframe.to_excel(writer, sheet_name=str(yearyyzy))


#%% ----------------------- now, per region ---------------------------

# extract only the numerical columns
regions = total_data.iloc[:, 3:91]

# reset the index to not have an issue with indices
#numbers = numbers.reset_index()
#numbers = numbers.drop([('Area', ''), ('N. of Trap', '')], axis=1)

# make sure the columns are datetime & make a multiindex
regions.columns = pd.MultiIndex.from_arrays([
    pd.to_datetime(regions.columns.get_level_values(0), errors='ignore'),
    regions.columns.get_level_values(1)
    ], names=regions.columns.names)

# get the column names of the numerical columns & define a variable to store
regionrows = regions['layer']

# basically make all the data into one big long list for each year
regio_values = {
    region: regions.loc[regionrows==region, :].to_numpy().ravel()
    for region in np.unique(regionrows)
    }

# remove text values
regio_values = {
    region: pd.to_numeric(vals, errors='coerce')[~np.isnan(pd.to_numeric(vals, errors='coerce'))]
    for region, vals in regio_values.items()
    }

# remove blank values - this may be redundant with the notnull above
#regio_values = {
 #   region: vals[~pd.isnull(vals)]
  #  for region, vals in regio_values.items()
   # }

# describe a dictionary to store descriptive statistics
regional_dict = {}

# go through the dictionaries generated above, and find descriptive
# statistics of these
for regun, case in regio_values.items():
    regional_index = regun
    desc_stat = pd.Series(case).describe()
    desc_stat['sum'] = pd.Series(case).sum()
    regional_dict[regional_index] = desc_stat
    
# convert to an excel file with a sheet for each year
with pd.ExcelWriter('../MY_OUTPUTS/desc_stats_region.xlsx') as writer:
    for regyz, dataframee in regional_dict.items():
        dataframee.to_excel(writer, sheet_name=str(regyz))
        
#%% ------------------------------- now, per season -----------------------------

# extract only the numerical columns
seasons = total_data.iloc[:, 3:90]

# reset the index to not have an issue with indices
#numbers = numbers.reset_index()
#numbers = numbers.drop([('Area', ''), ('N. of Trap', '')], axis=1)

# make sure the columns are datetime & make a multiindex
seasons.columns = pd.MultiIndex.from_arrays([
    pd.to_datetime(seasons.columns.get_level_values(0), errors='ignore'),
    seasons.columns.get_level_values(1)
    ], names=seasons.columns.names)

# get the column dates
datesseason = seasons.columns.get_level_values(0)

# 
labels_season = np.full(len(datesseason), 'Other', dtype=object)

# data selectors for season
spring_dates = (
    ((datesseason.month == 6) & (datesseason.day >= 5)) |
     ((datesseason.month == 7) & (datesseason.day < 25))
     )
    
labels_season[spring_dates] = 'Spring'

summer_dates = (
    ((datesseason.month == 7) & (datesseason.day >= 25)) |
     (datesseason.month == 8) |
     ((datesseason.month == 9) & (datesseason.day < 12))
     )

labels_season[summer_dates] = 'Summer'        
        
autumn_dates = (
    ((datesseason.month == 9) & (datesseason.day >= 12)) |
     (datesseason.month == 10)
     )

labels_season[autumn_dates] = 'Autumn'

seasons.columns = pd.MultiIndex.from_arrays(
    [datesseason, labels_season],
    names=['Date', 'Season'])

saisons = seasons.columns.get_level_values(1)

# basically make all the data into one big long list for each year
season_values = {
    season: seasons.loc[:, saisons==season].to_numpy().ravel()
    for season in np.unique(saisons)
    }

# remove blank values
season_values = {
    season: vals[~np.isnan(vals)]
    for season, vals in season_values.items()
    }

# describe a dictionary to store descriptive statistics
season_overall = {}

# go through the dictionaries generated above, and find descriptive
# statistics of these
for sswd, datza in season_values.items():
    
    season_index = sswd
    seas_desc = pd.DataFrame(datza)
    s_desc = seas_desc.describe()
    s_desc['sum'] = datza.sum()
    #s_sum = seas_desc.sum()
    season_overall[season_index] = s_desc
    
# convert to an excel file with a sheet for each year
with pd.ExcelWriter('../MY_OUTPUTS/season_desc_stats.xlsx') as writer:
    for sprsumaut, dita_frame in season_overall.items():
        dita_frame.to_excel(writer, sheet_name=str(sprsumaut))


#%% per 10 days
# extract only the numerical columns
days_10 = total_data.iloc[:, 3:90]

# reset the index to not have an issue with indices
#numbers = numbers.reset_index()
#numbers = numbers.drop([('Area', ''), ('N. of Trap', '')], axis=1)

# make sure the columns are datetime & make a multiindex
days_10.columns = pd.MultiIndex.from_arrays([
    pd.to_datetime(days_10.columns.get_level_values(0)),
    days_10.columns.get_level_values(1)
    ], names=days_10.columns.names)

# get the column names of the numerical columns & define a variable to store
numcolumns = days_10.columns.get_level_values(0)
dates = numcolumns.date

# date labels
date_labels = np.full(len(dates), 'Other', dtype=object)
 
# convert into a dataframe   
dates_dataframe = pd.DataFrame(dates)
dates_dataframe = dates_dataframe.rename({0: 'Start Date'}, axis=1)
dates_dataframe = dates_dataframe.sort_values('Start Date')

# define a loop to only keep the dates that are at least 12 days
# apart from each other
keep_date = []
last = None

for day in dates_dataframe['Start Date']:
    if last is None or day>= last + pd.Timedelta(days=12):
        keep_date.append(True)
        last = day
    else:
        keep_date.append(False)

# keep only these dates to avoid a moving window
resultsish = dates_dataframe[keep_date]

# find the end date of the grouping
resultsish['End Date'] = resultsish['Start Date'] + pd.Timedelta(days=11)

# make sure the list of dates is datetime
dates = pd.to_datetime(dates)

# check that dates are datetime
resultsish['Start Date'] = pd.to_datetime(resultsish['Start Date'])
resultsish['End Date'] = pd.to_datetime(resultsish['End Date'])

# FOR EACH defined 10-day window, assign all dates that fall
# within the window the name of the start date
for _, line in resultsish.iterrows():
    date_filter = (
        (dates >= line['Start Date']) & (dates <= line['End Date']))

    date_labels[date_filter] = line['Start Date']
    
print(date_labels)

# recreate a multiindex based on the original dates and the new
# dates
days_10.columns = pd.MultiIndex.from_arrays(
    [numcolumns, date_labels],
    names=['Original date', '10-day grouping'])

intervals = days_10.columns.get_level_values(1)

# basically make all the data into one big long list for each year
days_10_values = {
    days10: days_10.loc[:, intervals==days10].to_numpy().ravel()
    for days10 in np.unique(intervals)
    }

# remove blank values
days_10_values = {
    days10: vals[~np.isnan(vals)]
    for days10, vals in days_10_values.items()
    }

# describe a dictionary to store descriptive statistics
desc_intervals = {}
countup = 16
# go through the dictionaries generated above, and find descriptive
# statistics of these
for day10int, datagrouped in days_10_values.items():
    
    countup += 1
    interval_idx = countup
    df_describe = pd.DataFrame(datagrouped)
    desc = df_describe.describe()
    desc['sum'] = datagrouped.sum()
    desc['date'] = day10int
    desc_intervals[interval_idx] = desc
    
# convert to an excel file with a sheet for each year
with pd.ExcelWriter('../MY_OUTPUTS/testfor10days.xlsx') as writer:
    for int10, datafraame in desc_intervals.items():
        datafraame.to_excel(writer, sheet_name=str(int10))
