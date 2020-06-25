import pandas as pd
from demand_wrangler import DemandWrangler


class ProductsCatalogueWrangler:
    def __init__(self, path_to_products, path_to_demand):
        self.path_to_products = path_to_products
        self.path_to_demand = path_to_demand
        # self.products = pd.read_csv(self.path_to_products)
        demand_wrangler = DemandWrangler(self.path_to_demand)
        self.sap_catalogue = demand_wrangler.get_sap_catalogue()

if __name__ == '__main__':
    print('fuck')
    products_wrangler = ProductsCatalogueWrangler('..', '../../data/full_demand.xlsx')
    sap_catalogue = products_wrangler.sap_catalogue