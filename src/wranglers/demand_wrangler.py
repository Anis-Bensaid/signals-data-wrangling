import datetime
import numpy as np
import pandas as pd


#
# import os
# os.chdir(os.getcwd()+'/src/wranglers')
# df = pd.read_excel('../../data/full_demand.xlsx', header=1)

class DemandWrangler:
    def __init__(self, path_to_file):
        self.path_to_file = path_to_file
        print('Reading demand data...')
        # self.demand = pd.read_excel(path_to_file, header=1)
        self.demand = df
        self.sap_catalogue = pd.DataFrame()
        self.is_wrangled = False

    def wrangle(self):
        if self.is_wrangled:
            return
        print('Wrangling demand data...')
        # Drop the total columns
        self.demand.drop(columns=[str(col) for col in self.demand.columns if str(col).find('Total') != -1], axis=1,
                         inplace=True)

        # In the .xlsx files 0 is marked as '-' which causes the demand columns to be read as of type object (str).
        # We need to replace the '-' by '0', and the ',' by '' in the demand columns and transform the type to int so
        # that we can aggregate using sum().
        dates_columns = [col for col in self.demand.columns if isinstance(col, datetime.datetime)]
        self.demand.loc[:, dates_columns] = self.demand.loc[:, dates_columns].replace(to_replace='-', value='0')
        self.demand.loc[:, dates_columns] = self.demand.loc[:, dates_columns].replace(to_replace=',', value='')
        self.demand.loc[:, dates_columns] = self.demand.loc[:, dates_columns].astype(int)

        # For the non-demand columns we replace '-' by np.nan
        self.demand.replace(to_replace='-', value=np.nan, inplace=True)
        self.demand.replace(to_replace=' ', value=np.nan, inplace=True)

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

        self.is_wrangled = True

    def get_sap_catalogue(self):
        self.wrangle()
        print('Getting SAP Catalogue...')
        # We agregate using brand, item_description and sub_category, then we keep the hierarchy rows that have the
        # most recent sales and sum the demand.
        self.sap_catalogue = self.demand[self.demand['demand'] > 0].sort_values(
            ascending=False,
            by=['item_description', 'date', 'demand']).drop(
            columns=['date', 'demand']).dropna().drop_duplicates(
            subset=['brand', 'item_description', 'sub_category_id'], keep='first')

        # The category and subcategories are truncated in the demand data so we remap them using mapping files
        # We also map the brand IDs to the brand names using a mapping file.
        sap_sub_categories = pd.read_csv('../../data/elc_sub_categories.csv', encoding="ISO-8859-1")
        sap_sub_categories['sub_category_id'] = sap_sub_categories['sub_category_id'].astype(str)
        self.sap_catalogue = self.sap_catalogue.drop(columns=['sub_category']).merge(sap_sub_categories,
                                                                                     on='sub_category_id',
                                                                                     how='left')
        if not self.sap_catalogue[self.sap_catalogue['sub_category'].isna()].empty:
            print('The following Subcategory IDs are not mapped, please add them to the mapping file:')
            print(self.sap_catalogue[self.sap_catalogue['sub_category'].isna()]['sub_category_id'].unique().tolist())

        sap_categories = pd.read_csv('../../data/elc_categories.csv', encoding="ISO-8859-1")
        sap_categories['category_id'] = sap_categories['category_id'].astype(str)
        self.sap_catalogue = self.sap_catalogue.drop(columns=['category']).merge(sap_categories,
                                                                                 on='category_id',
                                                                                 how='left')
        if not self.sap_catalogue[self.sap_catalogue['category'].isna()].empty:
            print('The following Category IDs are not mapped, please add them to the mapping file:')
            print(self.sap_catalogue[self.sap_catalogue['category'].isna()]['category_id'].unique().tolist())

        sap_brands = pd.read_csv('../../data/elc_brands.csv', encoding="ISO-8859-1")
        sap_brands['brand_id'] = sap_brands['brand_id'].astype(str)
        self.sap_catalogue.rename(columns={'brand': 'brand_id'}, inplace=True)
        self.sap_catalogue = self.sap_catalogue.merge(sap_brands,
                                                      on='brand_id',
                                                      how='left')
        if not self.sap_catalogue[self.sap_catalogue['elc_brand'].isna()].empty:
            print('The following Brand IDs are not mapped, please add them to the mapping file:')
            print(self.sap_catalogue[self.sap_catalogue['elc_brand'].isna()]['brand_id'].unique().tolist())

        # Drop missing columns
        self.sap_catalogue.dropna(inplace=True)

        # Ordering columns and rows
        ordered_columns = [
            'brand_id',
            'elc_brand',
            'itemid_4',
            'item_description',
            'major_category_id',
            'major_category',
            'application_id',
            'application',
            'category_id',
            'category',
            'sub_category_id',
            'sub_category']
        self.sap_catalogue = self.sap_catalogue.set_index(ordered_columns).reset_index()
        return self.sap_catalogue


if __name__ == '__main__':
    demand_wrangler = DemandWrangler('../../data/full_demand.xlsx')
    sap_catalogue = demand_wrangler.get_sap_catalogue()
    demand = demand_wrangler.demand
    # sap_catalogue[sap_catalogue['elc_brand'].isna()]['brand_id'].unique()
