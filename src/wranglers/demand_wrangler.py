import datetime
import numpy as np
import pandas as pd


PATH_TO_CATEGORIES_MAPPING = '../data/elc_categories.csv'
PATH_TO_SUBCATEGORIES_MAPPING = '../data/elc_sub_categories.csv'
PATH_TO_BRANDS_MAPPING = '../data/elc_brands.csv'
#
# import os
# os.chdir(os.getcwd()+'/src/wranglers')
# df = pd.read_excel('../../data/full_demand.xlsx', header=1)


class DemandWrangler:
    def __init__(self, path_to_file):
        self.path_to_file = path_to_file
        print('Reading Demand data...')
        self.demand = pd.read_excel(path_to_file, header=1)
        # self.demand = df
        self.sap_catalogue = pd.DataFrame()
        self.is_wrangled = False

    def wrangle(self):
        if self.is_wrangled:
            return
        print('Wrangling Demand data...')
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
        self.demand.columns = [col.strip().replace(' ', '_') for col in self.demand.columns]

        self.is_wrangled = True

    def get_sap_catalogue(self):
        self.wrangle()
        print('Getting SAP Catalogue...')
        # We agregate using brand, item_description and sub_category, then we keep the hierarchy rows that have the
        # most recent sales and sum the demand.
        self.sap_catalogue = self.demand[self.demand['Demand'] > 0].sort_values(
            ascending=False,
            by=['Item_Description', 'Date', 'Demand']).drop(
            columns=['Date', 'Demand']).dropna().drop_duplicates(
            subset=['Brand', 'Item_Description', 'Sub_Category_ID'], keep='first')

        # The category and subcategories are truncated in the demand data so we remap them using mapping files
        # We also map the brand IDs to the brand names using a mapping file.
        sap_sub_categories = pd.read_csv(PATH_TO_SUBCATEGORIES_MAPPING, encoding="ISO-8859-1")
        sap_sub_categories['Sub_Category_ID'] = sap_sub_categories['Sub_Category_ID'].astype(str)
        self.sap_catalogue = self.sap_catalogue.drop(columns=['Sub_Category']).merge(sap_sub_categories,
                                                                                     on='Sub_Category_ID',
                                                                                     how='left')
        if not self.sap_catalogue[self.sap_catalogue['Sub_Category'].isna()].empty:
            print('The following Subcategory IDs are not mapped, please add them to the mapping file:')
            print(self.sap_catalogue[self.sap_catalogue['Sub_Category'].isna()]['Sub_Category_ID'].unique().tolist())

        sap_categories = pd.read_csv(PATH_TO_CATEGORIES_MAPPING, encoding="ISO-8859-1")
        sap_categories['Category_ID'] = sap_categories['Category_ID'].astype(str)
        self.sap_catalogue = self.sap_catalogue.drop(columns=['Category']).merge(sap_categories,
                                                                                 on='Category_ID',
                                                                                 how='left')
        if not self.sap_catalogue[self.sap_catalogue['Category'].isna()].empty:
            print('The following Category IDs are not mapped, please add them to the mapping file:')
            print(self.sap_catalogue[self.sap_catalogue['Category'].isna()]['Category_ID'].unique().tolist())

        sap_brands = pd.read_csv(PATH_TO_BRANDS_MAPPING, encoding="ISO-8859-1")
        sap_brands['Brand_ID'] = sap_brands['Brand_ID'].astype(str)
        self.sap_catalogue.rename(columns={'Brand': 'Brand_ID'}, inplace=True)
        self.sap_catalogue = self.sap_catalogue.merge(sap_brands,
                                                      on='Brand_ID',
                                                      how='left')
        if not self.sap_catalogue[self.sap_catalogue['ELC_Brand'].isna()].empty:
            print('The following Brand IDs are not mapped, please add them to the mapping file:')
            print(self.sap_catalogue[self.sap_catalogue['ELC_Brand'].isna()]['Brand_ID'].unique().tolist())

        # Drop missing columns
        self.sap_catalogue.dropna(inplace=True)

        # Ordering columns and rows
        ordered_columns = [
            'Brand_ID',
            'ELC_Brand',
            'ItemID_4',
            'Item_Description',
            'Major_Category_ID',
            'Major_Category',
            'Application_ID',
            'Application',
            'Category_ID',
            'Category',
            'Sub_Category_ID',
            'Sub_Category']
        self.sap_catalogue = self.sap_catalogue.set_index(ordered_columns).reset_index()
        return self.sap_catalogue


if __name__ == '__main__':
    demand_wrangler = DemandWrangler('../../data/full_demand.xlsx')
    sap_catalogue = demand_wrangler.get_sap_catalogue()
    demand = demand_wrangler.demand
    # sap_catalogue[sap_catalogue['ELC_Brand'].isna()]['Brand_ID'].unique()
