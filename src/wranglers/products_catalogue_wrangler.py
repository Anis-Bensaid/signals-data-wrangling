import sys
import os
os.chdir(os.getcwd()+'/src/wranglers')
sys.path.append(os.getcwd())

import pandas as pd
import json
from demand_wrangler import DemandWrangler
from utilis.text_distances import *
from tqdm import tqdm
tqdm.pandas()


PATH_TO_ITEM_DESCRIPTIONS_MAPPING = '../../data/'
PATH_TO_BRANDS_MAPPING = '../../data/brand_mapping.csv'
PATH_TO_PRODUCT_CATALOGUE_TEMPLATE_MAPPING = '../../data/product_catalogue_template_mapping.txt'
PATH_TO_PRODUCT_CATALOGUE_TEMPLATE = '../../data/product_catalogue_template.csv'
# df = pd.read_csv('../../data/cosmetics_products_20200331.csv')


class ProductsCatalogueWrangler:
    def __init__(self, path_to_products, path_to_demand):
        self.path_to_products = path_to_products
        self.path_to_demand = path_to_demand
        demand_wrangler = DemandWrangler(self.path_to_demand)
        self.sap_catalogue = demand_wrangler.get_sap_catalogue()
        del demand_wrangler
        self.products = pd.read_csv(self.path_to_products)

        self.is_mapped_to_template = False

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
            print('The following columns exist in the template but have not been found in the file. Kake sure they are '
                  'properly mapped, otherwise they will be filled with missing data:')
            print(columns_not_filled)
        self.products = pd.concat([template, self.products], ignore_index=True, join='inner')
        self.is_mapped_to_template = True

    def map_brands(self, threshold=0.815, path_to_brand_mappings=PATH_TO_BRANDS_MAPPING):
        print('Mapping Brands...')
        brands_mapping = pd.read_csv(path_to_brand_mappings)
        mapped_brands = brands_mapping.loc[0:6000, 'Brand'].unique().tolist()
        elc_brands = self.sap_catalogue[['Brand_ID', 'ELC_Brand']].drop_duplicates()
        brands_to_map = self.products[~self.products['Brand'].isin(mapped_brands)]['Brand'].drop_duplicates().to_frame()
        print('{} new brands detected...'.format(len(brands_to_map)))

        new_brands_mapping = brands_to_map.assign(key=0).merge(elc_brands.assign(key=0),
                                                               on='key',
                                                               how='left').drop('key',
                                                                                axis=1)

        new_brands_mapping['Brand_Score'] = new_brands_mapping.progress_apply(lambda row: brands_custom_distance(row),
                                                                              axis=1)

        new_brands_mapping = new_brands_mapping.groupby('Brand').apply(
            lambda x: x.nlargest(1, 'Brand_Score')).reset_index(
            drop=True).sort_values('Brand_Score', ascending=False)

        new_brands_mapping.loc[new_brands_mapping['Brand_Score'] < threshold,
                               ['Brand_ID', 'ELC_Brand', 'Brand_Score']] = np.nan, np.nan, 0

        brands_mapping = pd.concat([brands_mapping, new_brands_mapping])
        brands_mapping = brands_mapping.sort_values(by='ELC_Brand').reset_index(drop=True)
        brands_mapping.to_csv(path_to_brand_mappings, index=False)

        self.products = self.products.merge(brands_mapping, on=['Brand'], how='left')


    def map_item_descriptions(self, path_to_item_description_mappings):
        return

    def map_subcategories(self):
        return

    def wrangle(self):
        return
if __name__ == '__main__':
    products_wrangler = ProductsCatalogueWrangler('../../data/cosmetics_products_20200331.csv', '../../data/full_demand.xlsx')
    products = products_wrangler.products
    products['Brand'].unique()
    sap_catalogue = products_wrangler.sap_catalogue

#
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