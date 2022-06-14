import os
import sys
import requests
import geopandas as gpd
import pandas as pd
import numpy as np

import os
import sys
import requests

class prepare_data:

    def __init__(self, working_dir, plot=False):

        self.plot = plot
        self.working_dir = working_dir

        try:
            raw_shape_ger = gpd.read_file("../"+self.working_dir+"/DEU_adm1.shp")
            raw_shape_ger_eez = gpd.read_file("../"+self.working_dir+"/eez.shp")
        except RuntimeError:
            print(sys.exc_info())
            sys.exit()

        raw_shape_ger = raw_shape_ger[:].to_crs('EPSG:4326')
        raw_shape_ger_eez = raw_shape_ger_eez.to_crs('EPSG:4326')

        # Drop not needed rows, merge both geodataframes, plot a map and save as shape file
        shape_ger = raw_shape_ger[['NAME_1', 'geometry']].rename(columns = {'NAME_1':'geoname'})
        shape_ger_eez = raw_shape_ger_eez[['geoname', 'geometry']]

        self._shape_ger = pd.concat([shape_ger, shape_ger_eez]).reset_index(drop=True)
        self._shape_ger.to_file("../"+self.working_dir+"/shape_ger.shp")

        if self.plot == True:
            ax = self._shape_ger.plot(color="none", edgecolor='gainsboro')

    def fetch_data(self, years = [2019,2020,2021,2022], weather_parameters = 'T2M,T2MDEW,T2MWET,TS,WS50M,WD50M,ALLSKY_SFC_SW_DWN,CLRSKY_SFC_SW_DWN,ALLSKY_SFC_LW_DWN,ALLSKY_SFC_UVA,ALLSKY_SFC_UVB'):

        self.years = years
        self.weather_parameters = weather_parameters

        self._fetch_weather_data()
        self._reformat_weather_data()
        self._prepare_electricity_data()

    def _fetch_weather_data(self):

        # download the weather data
        # this is split into east and west, because the API only allows 10° LAT and LON
        # and into years, because the API only allows 366 days in one download

        for year in self.years:
            if year == 2022:
                mmdd = '0401'
            else:
                mmdd = '1231'

            exists = os.path.isfile('../'+self.working_dir+'/weather_map_raw_ger_west_'+str(year)+'.csv')
            if not exists:
                url = 'https://power.larc.nasa.gov/api/temporal/daily/regional?parameters='+self.weather_parameters+'&start='+str(year)+'0101&end='+str(year)+mmdd+'&community=RE&format=CSV&latitude-min=47.25&latitude-max=56.25&longitude-min=3.25&longitude-max=10.25'
                data = requests.get(url, allow_redirects=True)
                open('../'+self.working_dir+'/weather_map_raw_ger_west_'+str(year)+'.csv', 'wb').write(data.content)

            exists = os.path.isfile('../'+self.working_dir+'/weather_map_raw_ger_east_'+str(year)+'.csv')
            if not exists:
                url = 'https://power.larc.nasa.gov/api/temporal/daily/regional?parameters='+self.weather_parameters+'&start='+str(year)+'0101&end='+str(year)+mmdd+'&community=RE&format=CSV&latitude-min=47.25&latitude-max=56.25&longitude-min=10.75&longitude-max=15.25'
                data = requests.get(url, allow_redirects=True)
                open('../'+self.working_dir+'/weather_map_raw_ger_east_'+str(year)+'.csv', 'wb').write(data.content)


        # merge east and west and all years to one file

        weather_raw_ger = {}

        for year in self.years:
            weather_raw_ger_east = pd.read_csv('../'+self.working_dir+'/weather_map_raw_ger_east_'+str(year)+'.csv',
                                                   header=19)
            weather_raw_ger_west = pd.read_csv('../'+self.working_dir+'/weather_map_raw_ger_west_'+str(year)+'.csv',
                                                   header=19)

            weather_raw_ger[year] = pd.concat([weather_raw_ger_east,
                                               weather_raw_ger_west])

        weather_raw_ger = pd.concat([weather_raw_ger[year] for year in self.years]).reset_index(drop=True)

        # infer the date to a pandas datetime (therefore rename stuff..)
        weather_raw_ger.rename(columns = {'MO':'month', 'DY':'day'}, inplace=True)
        weather_raw_ger['date'] = pd.to_datetime(weather_raw_ger[['YEAR', 'month', 'day']])
        weather_raw_ger.drop(['YEAR', 'month', 'day'], axis=1, inplace=True)

        # convert weather data to a geodataframe (with LON and LAT) so its easy to inspect
        # plot the shape file and the weather data locations (only for one datetime, locations are the same for all datetimes)
        weather_raw_ger_geo = gpd.GeoDataFrame(weather_raw_ger,
                                               geometry = gpd.points_from_xy(weather_raw_ger.LON, weather_raw_ger.LAT),
                                               crs="EPSG:4326")

        if self.plot == True:
            ax = self._shape_ger.plot(color="none", edgecolor='gainsboro')
            weather_raw_ger_geo[weather_raw_ger['date'] == pd.Timestamp('2019-01-01')].plot(color="k", markersize=1, ax=ax)

        self.weather_ger_geo = self._mask_weather_data(weather_raw_ger, weather_raw_ger_geo)

        if self.plot == True:
            ax = self._shape_ger.plot(color="none", edgecolor='gainsboro')
            self.weather_ger_geo[self.weather_ger_geo['date'] == pd.Timestamp('2019-07-04')].plot(color="k", markersize=1, ax=ax)

    def _reformat_weather_data(self):

        # Energy generation data will only be available for whole germany, therefore each row has to contain all LAT LON information.
        # Generate feature map by translating LAT LON from columns to single row:

        weather_ger_df = pd.DataFrame(self.weather_ger_geo.drop(columns='geometry'))#[self.weather_ger_geo.date.dt.year != 2022])

        lat_lon = weather_ger_df[['LAT', 'LON']].drop_duplicates()
        column_names = []
        for i in weather_ger_df.columns[2:-1]:
            for index, row in lat_lon.iterrows():
                column_names.append(i+' '+str(row['LAT'])+' '+str(row['LON']))
        column_names.append('date')

        # A bit hacky, but correct and fast:
        self._weather_ger_reshape = pd.DataFrame(columns = column_names, index=np.arange(len(pd.unique(weather_ger_df.date))))
        for j in range(len(self._weather_ger_reshape)):
            for i in range(len(weather_ger_df.columns)-3):
                self._weather_ger_reshape.loc[j][i*len(lat_lon):(i+1)*len(lat_lon)] = weather_ger_df.loc[j*len(lat_lon):(j+1)*len(lat_lon)-1][weather_ger_df.columns[i+2]]
            self._weather_ger_reshape.loc[j][-1] = weather_ger_df.loc[j*len(lat_lon)].date
        self._weather_ger_reshape.set_index('date', inplace=True)

    def _mask_weather_data(self, weather_raw_ger, weather_raw_ger_geo):

        # Sort the data for a computationally efficent application of the mask
        weather_raw_ger = weather_raw_ger.sort_values(by=['date', 'LAT', 'LON']).reset_index(drop=True)
        weather_raw_ger_geo = weather_raw_ger_geo.sort_values(by=['date', 'LAT', 'LON']).reset_index(drop=True)

        # for one specific datetime generate a mask of weather locations that are within germany and eez
        mask_individual_shape = [weather_raw_ger_geo[weather_raw_ger['date'] == pd.Timestamp('2019-01-01')].within(self._shape_ger.loc[i, 'geometry']) for i in range(len(self._shape_ger))]
        mask_individual_time = pd.Series([any([mask_individual_shape[i].iloc[j] for i in range(len(mask_individual_shape))]) for j in range(len(mask_individual_shape[0]))])

        # expand this mask by concatinating copys of it
        mask = mask_individual_time.copy()
        mask_t = mask_individual_time.copy()
        for i in range(int(len(weather_raw_ger)/len(mask_individual_time)-1)):
            mask_t.index += len(mask_individual_time)
            mask = pd.concat([mask, mask_t])

        # Apply the mask and plot the result for a single datetime
        return weather_raw_ger_geo[mask].reset_index(drop=True)

    def _power_to_energy(self, power_single_day):
        measurements_per_hour = len(power_single_day)/24
        energy = np.sum(power_single_day) / measurements_per_hour
        return energy

    def _prepare_electricity_data(self):

        electricity_raw = {}

        for year in self.years:
            if year <= 2019:
                electricity_raw[year] = pd.read_csv('../'+self.working_dir+'/energy-charts_Electricity_production_in_Germany_in_'+str(year)+'.csv')
            else:
                electricity_raw[year] = pd.read_csv('../'+self.working_dir+'/energy-charts_Electricity_generation_in_Germany_in_'+str(year)+'.csv')

        electricity_raw = pd.concat([electricity_raw[year] for year in self.years]).reset_index(drop=True)
        electricity_raw['Date (UTC)'] = pd.to_datetime(electricity_raw['Date (UTC)'], utc=True)
        electricity_raw.set_index(['Date (UTC)'], inplace = True)
        electricity_raw.index = electricity_raw.index.tz_convert(None)

        electricity_raw_daybinned = electricity_raw.resample('D').apply(self._power_to_energy)

        self._electricity_daybinned = pd.DataFrame(index = electricity_raw_daybinned.index)
        self._electricity_daybinned['Wind'] = electricity_raw_daybinned[electricity_raw_daybinned.columns[0:6]].sum(axis=1)
        self._electricity_daybinned['Solar'] = electricity_raw_daybinned[electricity_raw_daybinned.columns[6:-1]].sum(axis=1)

        self._electricity_daybinned.index.names = ['date']

        self.weather_electricity_data = pd.merge(left = self._weather_ger_reshape, right = self._electricity_daybinned, how='left', on = 'date')
        self.weather_electricity_data

    def save_data(self, file_name = 'weather_electricity_data.csv'):
        # save data as da pandas dataframe
        self.weather_electricity_data.to_csv('../'+self.working_dir+'/'+file_name)
        
