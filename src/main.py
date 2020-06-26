from wranglers.ratings_and_reviews_wrangler import *
from wranglers.products_catalogue_wrangler import *
from utilis.user_interface import *

if __name__ == '__main__':
    while True:
        print('\nPlease select the type of data to process (use the dialogue box)')
        reply = easygui.buttonbox(msg='What type of file do you want to process ?', title='Signals data processor',
                                  choices=['Ratings and Reviews', 'Products Catalogue', 'Exit'])
        if reply == 'Exit':
            break
        if reply == 'Ratings and Reviews':
            print('Please select the Ratings and Reviews file (use the dialogue box)')
            paths_to_ratings_and_reviews = get_path(msg='Select Ratings and Reviews files',
                                                    title='Signals data processor',
                                                    filetypes='*.csv',
                                                    multiple=True,
                                                    to_list=True)
            path_to_save_dir = get_dir(msg='Select directory to save the files to',
                                       title='Signals data processor')
            wrangler = MultiRatingsReviewsWrangler(paths_to_ratings_and_reviews, path_to_save_dir)
            wrangler.export_voc_files()
        if reply == 'Products Catalogue':
            print('Please select the Demand file (use the dialogue box)')
            paths_to_demand = get_path(msg='Select the Demand file',
                                       title='Signals data processor',
                                       filetypes='*.xlsx',
                                       multiple=False,
                                       to_list=False)
            print('Please select the Product Catalogue files (use the dialogue box)')
            paths_to_products_catalogues = get_path(msg='Select Product Catalogue files',
                                                    title='Signals data processor',
                                                    filetypes='*.csv',
                                                    multiple=True,
                                                    to_list=True)
            path_to_save_dir = get_dir(msg='Select directory to save the files to',
                                       title='Signals data processor')
            wrangler = MultiProductsCatalogueWrangler(paths_to_products_catalogues, paths_to_demand, path_to_save_dir)
            wrangler.export_voc_files()
        print('Done.')
