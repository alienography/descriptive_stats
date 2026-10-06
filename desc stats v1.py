# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 16:22:31 2026

@author: simme
"""
# import necessary packages
import pandas as pd
import geopandas as gpd

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
print("Successfully made geometries of the trap locations")

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


#total_data.to_excel('./testcel.xlsx')
print(total_data.head(5))
print(total_data.columns)

# =================== DESCRIPTIVE STATISTICS ==============================
# ------------------- first, do overall -----------------------------------
# generate descriptive statistics of the dataset
numbers = total_data.iloc[:, 3:90]
numbers = numbers.reset_index()
numbers = numbers.drop([('Area', ''), ('N. of Trap', '')], axis=1)
print(numbers.columns)

numbers.columns = pd.MultiIndex.from_arrays([
    pd.to_datetime(numbers.columns.get_level_values(0)),
    numbers.columns.get_level_values(1)
    ], names=numbers.columns.names)

print(numbers.columns.get_level_values(0).year)
yearly = numbers.groupby(
    [numbers.columns.get_level_values(0).year,
     numbers.columns.get_level_values(1)],
    axis=1
    )

yearly_mean = yearly.sum() / yearly.count()

yearly_mean.to_excel('./testprinthbjhdd.xlsx')
# descriptive statistics function
#numbers_desc = numbers.describe()

#numbers_desc.to_excel('./desctest.xlsx')

