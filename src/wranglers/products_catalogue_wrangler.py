import sys
import os
import ntpath
# os.chdir(os.getcwd() + '/src/wranglers')
# sys.path.append(os.getcwd())

import pandas as pd
import json
from wranglers.demand_wrangler import DemandWrangler
from utilis.text_distances import *
from tqdm import tqdm
tqdm.pandas()


PATH_TO_ITEM_DESCRIPTIONS_MAPPING = '../data/item_description_mapping.csv'
PATH_TO_BRANDS_MAPPING = '../data/brand_mapping.csv'
PATH_TO_PRODUCT_CATALOGUE_TEMPLATE_MAPPING = '../data/product_catalogue_template_mapping.txt'
PATH_TO_PRODUCT_CATALOGUE_TEMPLATE = '../data/product_catalogue_template.csv'

class ProductsCatalogueWrangler:
    def __init__(self, path_to_products_catalogue, path_to_save_dir, sap_catalogue):
        self.path_to_products_catalogue = path_to_products_catalogue
        self.path_to_save_dir = path_to_save_dir
        self.sap_catalogue = sap_catalogue
        self.products = pd.DataFrame()
        self.is_wrangled = False
        self.is_voc = False

    def map_to_template(self):
        print('Formatting Product Catalogue to template format...')
        with open(PATH_TO_PRODUCT_CATALOGUE_TEMPLATE_MAPPING) as f:
            columns_mapping = json.load(f)
        self.products.rename(columns=columns_mapping, inplace=True)
        template = pd.read_csv(PATH_TO_PRODUCT_CATALOGUE_TEMPLATE)
        columns_not_mapped = [col for col in self.products.columns if not col in template.columns]
        columns_not_filled = [col for col in template.columns if not col in self.products.columns]
        if columns_not_mapped:
            print('The following columns exist in the file but have not been found in the template. Make sure they '
                  'are properly mapped, otherwise they will be deleted:')
            print(columns_not_mapped)
        if columns_not_filled:
            print('The following columns exist in the template but have not been found in the file. Make sure they are '
                  'properly mapped, otherwise they will be filled with missing data:')
            print(columns_not_filled)
        self.products = pd.concat([template, self.products], ignore_index=True, join='outer')

    def map_brands(self, threshold=0.815, path_to_brand_mapping=PATH_TO_BRANDS_MAPPING):
        print('Mapping Brands...')
        brands_mapping = pd.read_csv(path_to_brand_mapping)
        mapped_brands = brands_mapping['Brand'].unique().tolist()
        brands_to_map = self.products[~self.products['Brand'].isin(mapped_brands)]['Brand'].drop_duplicates().to_frame()
        print('{} new brands detected...'.format(len(brands_to_map)))
        if len(brands_to_map) > 0:
            elc_brands = self.sap_catalogue[['Brand_ID', 'ELC_Brand']].drop_duplicates()
            new_brands_mapping = brands_to_map.assign(key=0).merge(elc_brands.assign(key=0),
                                                                   on='key',
                                                                   how='left').drop('key',
                                                                                    axis=1)
            print('hey')
            new_brands_mapping['Brand_Score'] = new_brands_mapping.progress_apply(
                lambda row: brands_custom_distance(row),
                axis=1)

            new_brands_mapping = new_brands_mapping.groupby('Brand').apply(
                lambda x: x.nlargest(1, 'Brand_Score')).reset_index(
                drop=True).sort_values('Brand_Score', ascending=False)

            new_brands_mapping.loc[new_brands_mapping['Brand_Score'] < threshold,
                                   ['Brand_ID', 'ELC_Brand', 'Brand_Score']] = np.nan, np.nan, 0

            brands_mapping = pd.concat([brands_mapping, new_brands_mapping])
            brands_mapping = brands_mapping.sort_values(by='ELC_Brand').reset_index(drop=True)
            brands_mapping.to_csv(path_to_brand_mapping, index=False)

        self.products = self.products.merge(brands_mapping, how='left')

    def map_item_descriptions(self, threshold=0.637,
                              path_to_item_description_mapping=PATH_TO_ITEM_DESCRIPTIONS_MAPPING):
        print('Mapping Item Descriptions...')
        item_descriptions_mapping = pd.read_csv(path_to_item_description_mapping, low_memory=True)
        mapped_item_descriptions = item_descriptions_mapping[['Brand_ID', 'Product']].drop_duplicates()
        item_descriptions_to_map = self.products.dropna(subset=['Brand_ID'])
        item_descriptions_to_map = item_descriptions_to_map[
            ~((item_descriptions_to_map['Brand_ID'] + item_descriptions_to_map['Product']).isin(
                (mapped_item_descriptions['Brand_ID'] + mapped_item_descriptions['Product']).unique()
            ))][['Brand_ID', 'Product']]
        item_descriptions_to_map = item_descriptions_to_map[['Brand_ID', 'Product']].drop_duplicates()
        print('{} new Item Descriptions detected...'.format(len(item_descriptions_to_map)))
        if len(item_descriptions_to_map) > 0:
            elc_item_descriptions = self.sap_catalogue[['Brand_ID', 'Item_Description']]
            new_item_descriptions_mapping = item_descriptions_to_map.assign(key=0).merge(
                elc_item_descriptions.assign(key=0),
                on=['Brand_ID', 'key'],
                how='left').drop('key', axis=1)
            new_item_descriptions_mapping['Product_Score'] = new_item_descriptions_mapping.progress_apply(
                lambda row: item_description_custom_distance(row), axis=1)
            new_item_descriptions_mapping = new_item_descriptions_mapping.groupby('Product').apply(
                lambda x: x.nlargest(1, 'Product_Score')).reset_index(drop=True)

            item_descriptions_mapping = pd.concat([item_descriptions_mapping, new_item_descriptions_mapping])
            item_descriptions_mapping = item_descriptions_mapping.sort_values(by='Product_Score', ascending=False)
            item_descriptions_mapping.to_csv(path_to_item_description_mapping, index=False)

        self.products = self.products.merge(item_descriptions_mapping, on=['Brand_ID', 'Product'], how='left')
        self.products.loc[self.products['Product_Score'] < threshold, ['Item_Description', 'Product_Score']] = np.nan, 0

    def map_sap_hierarchy(self):
        print('Mapping subcategories and adding SAP hierarchy...')
        self.products = self.products.merge(self.sap_catalogue, on=['Brand_ID', 'ELC_Brand', 'Item_Description'],
                                            how='left')
        self.products['Sub_Category_Score'] = self.products.progress_apply(
            lambda row: subcategory_custom_distance(row), axis=1)
        self.products = self.products.groupby(['Channel', 'Product_Score', 'Brand_ID', 'Product']).progress_apply(
            lambda x: x.nlargest(1, 'Sub_Category_Score')).reset_index(drop=True)

    def wrangle(self, save=True):
        print('Reading Product Catalogue data...')
        self.products = pd.read_csv(self.path_to_products_catalogue)
        print('Wrangling data...')
        self.map_to_template()
        self.map_brands()
        self.map_item_descriptions()
        self.map_sap_hierarchy()
        self.products.drop(columns=['Brand_Score', 'Product_Score', 'Sub_Category_Score'], inplace=True)
        if save:
            print('Saving file with SAP hierarchy...')
            self.products.to_csv(
                os.path.join(self.path_to_save_dir,
                             ntpath.basename(self.path_to_products_catalogue).replace('.csv', '_w_SAP.csv')),
                index=False)
        self.is_wrangled = True
        self.is_voc = False

    def export_voc_files(self):
        if not self.is_wrangled:
            self.wrangle()
        self.products.loc[~self.products['Brand_ID'].isna(), 'Brand'] = self.products.loc[
            ~self.products['Brand_ID'].isna(), 'ELC_Brand']
        self.products.loc[~self.products['Sub_Category'].isna(), 'ELC_Solution_Type'] = self.products.loc[
            ~self.products['Sub_Category'].isna(), 'Sub_Category']
        self.products.loc[~self.products['Item_Description'].isna(), 'Product'] = self.products.loc[
            ~self.products['Item_Description'].isna(), 'Item_Description']
        template = pd.read_csv(PATH_TO_PRODUCT_CATALOGUE_TEMPLATE)
        self.products = self.products[template.columns]
        self.is_wrangled = False
        self.is_voc = True
        self.split_and_save()

    def split_and_save(self, max_rows=199999):
        print('Splitting and saving VoC files...')
        if len(self.products) <= max_rows:
            self.products.to_csv(
                os.path.join(self.path_to_save_dir,
                             ntpath.basename(self.path_to_products_catalogue).replace('.csv', '_to_upload.csv')),
                index=False)
        else:
            for k in range(1, len(self.products) // max_rows + 2):
                self.products.iloc[(k - 1) * max_rows:k * max_rows, :].to_csv(
                    os.path.join(self.path_to_save_dir,
                                 ntpath.basename(self.path_to_products_catalogue).replace(
                                     '.csv',
                                     '_to_upload_{}.csv'.format(k))),
                    index=False)


class MultiProductsCatalogueWrangler:
    def __init__(self, paths_to_products_catalogues, path_to_demand, path_to_save_dir):
        self.paths_to_products_catalogues = paths_to_products_catalogues
        self.path_to_save_dir = path_to_save_dir
        demand_wrangler = DemandWrangler(path_to_demand)
        self.sap_catalogue = demand_wrangler.get_sap_catalogue()
        del demand_wrangler

    def export_voc_files(self):
        for path in self.paths_to_products_catalogues:
            print('\nProcessing file ', ntpath.basename(path), '...')
            products_wrangler = ProductsCatalogueWrangler(path, self.path_to_save_dir, self.sap_catalogue)
            products_wrangler.export_voc_files()


if __name__ == '__main__':
    demand_wrangler = DemandWrangler('../data/full_demand.xlsx')
    sap_catalogue = demand_wrangler.get_sap_catalogue()
    products_wrangler = ProductsCatalogueWrangler('../data/Cosmetics_Product_20200116.csv',
                                                  sap_catalogue)
    products_wrangler.get_voc_files()
    products = products_wrangler.products

# columns_mapping = {
#     'Product_ID': 'Product_Id',
#     'Source Product Identifier': 'Source_Product_Identifier',
#     'Product': 'Product',
#     'Description': 'Description',
#     'Channel': 'Channel',
#     'Brand': 'Brand',
#     'Feature': 'Feature',
#     'Benefit': 'Benefit',
#     'Ingredient': 'Ingredient',
#     'Additional Ingredients (no rulebase)': 'Additional_Ingredients',
#     'Product Form': 'Product_Form',
#     'ELC Solution Type': 'ELC_Solution_Type',
#     'Rating': 'Rating',
#     'Number of Reviews': 'Number_of_Reviews',
#     'Geography': 'Geography',
#     'Collection Date': 'Collection_Date',
#     'Normalized Product Title': 'Normalized_Product_Title',
#     'ProductCluster_ID': 'ProductCluster_Id',
#     'Finish': 'Finish',
#     'Looks': 'Looks',
#     'Other': 'Other',
#     'Trends': 'Trends'}
# with open(PATH_TO_PRODUCT_CATALOGUE_TEMPLATE_MAPPING, 'w') as f:
#     f.write(json.dumps(columns_mapping, indent=1))
