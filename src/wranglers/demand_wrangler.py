import pandas as pd
import os
import numpy as np
import datetime


# os.chdir(os.getcwd()+'/src/wranglers')
# df = pd.read_excel('../../data/full_demand.xlsx', header=1)

class DemandWrangler:
    def __init__(self, path_to_file):
        self.path_to_file = path_to_file
        self.demand = pd.read_excel(path_to_file, header=1)
        self.sap_catalogue = pd.DataFrame()

    def wrangle(self):
        # Drop the total columns
        self.demand.drop(columns=[str(col) for col in self.demand.columns if str(col).find('Total') != -1], axis=1,
                         inplace=True)
        # Pandas friendly column names
        # In the .xlsx files 0 is marked as '-' which causes the demand columns to be read as of type object (str).
        # We need to replace the '-' by 0 in the demand columns and transform the type to int so that we can aggregate using sum().
        dates_columns = [col for col in self.demand.columns if isinstance(col, datetime.datetime)]
        self.demand.loc[:, dates_columns] = self.demand.loc[:, dates_columns].replace(to_replace='-', value='0')
        self.demand.loc[:, dates_columns] = self.demand.loc[:, dates_columns].replace(to_replace=',', value='')
        self.demand.loc[:, dates_columns] = self.demand.loc[:, dates_columns].astype(int)
        # For the non-demand columns we replace '-' by np.nan
        self.demand.replace(to_replace='-', value=np.nan, inplace=True)

        # Columns that do not contain dates
        groupbycols = ['Brand',
                       'ItemID 4',
                       'Item Description',
                       'Major Category ID',
                       'Major Category',
                       'Application ID',
                       'Application',
                       'Category ID',
                       'Category',
                       'Sub Category ID',
                       'Sub Category']

        # Converting the ids to str to make sure they are not duplicated.
        self.demand['ItemID 4'] = self.demand['ItemID 4'].astype(str)
        self.demand['Major Category ID'] = self.demand['Major Category ID'].astype(str)
        self.demand['Application ID'] = self.demand['Application ID'].astype(str)
        self.demand['Category ID'] = self.demand['Category ID'].astype(str)
        self.demand['Sub Category ID'] = self.demand['Sub Category ID'].astype(str)

        self.demand = self.demand[groupbycols + dates_columns].dropna()
        # We aggregate the data
        self.demand = self.demand.groupby(groupbycols).sum()
        # Finally we use stack to create a columns date, and have a row for each seperate month
        self.demand.columns.name = 'Date'
        self.demand = self.demand.stack().to_frame('Demand').reset_index()
        self.demand['Date'] = pd.to_datetime(self.demand['Date'], errors='coerce').dt.to_period('m')

        # Code friendly column names
        self.demand.columns = [col.lower().strip().replace(' ', '_') for col in self.demand.columns]

    def get_sap_catalogue(self):
        self.wrangle()
        # We agregate using brand, item_description and sub_category, then we keep the hierarchy rows that have the most recent sales and sum the demand.
        self.sap_catalogue = self.demand[self.demand['demand'] > 0].sort_values(
            ascending=False,
            by=['item_description', 'date', 'demand']).drop(
            columns=['date', 'demand']).dropna().drop_duplicates(
            subset=['brand', 'item_description', 'sub_category'], keep='first')
        self.sap_catalogue.reset_index(drop=True, inplace=True)
        return self.sap_catalogue

if __name__ == '__main__':
    demand_wrangler = DemandWrangler('../../data/full_demand.xlsx')
    print(demand_wrangler.get_sap_catalogue())


