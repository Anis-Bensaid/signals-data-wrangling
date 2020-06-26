import pandas as pd
import json
import ntpath
import os

PATH_TO_REVIEWS_TEMPLATE = '../data/reviews_template.csv'
PATH_TO_REVIEWS_TEMPLATE_MAPPING = '../data/reviews_template_mapping.txt'


class RatingsReviewsWrangler:
    def __init__(self, path_to_file, path_to_save_dir):
        self.path_to_file = path_to_file
        self.path_to_save_dir = path_to_save_dir
        print('Reading file...')
        self.reviews = pd.read_csv(path_to_file, low_memory=False)
        self.is_wrangled = False

    def wrangle(self, save=True):
        print('Wrangling Ratings and Reviews data...')
        with open(PATH_TO_REVIEWS_TEMPLATE_MAPPING) as f:
            columns_mapping = json.load(f)
        self.reviews.rename(columns=columns_mapping, inplace=True)
        template = pd.read_csv(PATH_TO_REVIEWS_TEMPLATE)
        columns_not_mapped = [col for col in self.reviews.columns if not col in template.columns]
        columns_not_filled = [col for col in template.columns if not col in self.reviews.columns]
        if columns_not_mapped:
            print('The following columns exist in the file but have not been found in the template. Make sure they '
                  'are properly mapped, otherwise they will be deleted:')
            print(columns_not_mapped)
        if columns_not_filled:
            print('The following columns exist in the template but have not been found in the file. Make sure they are '
                  'properly mapped, otherwise they will be filled with missing data:')
            print(columns_not_filled)
        self.reviews = pd.concat([template, self.reviews], ignore_index=True, join='outer').drop(
            columns=columns_not_mapped)
        self.is_wrangled = True
        if save:
            print('Saving file...')
            self.reviews.to_csv(
                os.path.join(self.path_to_save_dir,
                             ntpath.basename(self.path_to_file).replace('.csv', '_processed.csv')),
                index=False)

    def export_voc_files(self, max_rows=199999):
        print('Splitting and saving VoC files...')
        if not self.is_wrangled:
            self.wrangle()
        if len(self.reviews) <= max_rows:
            self.reviews.to_csv(
                os.path.join(self.path_to_save_dir,
                             ntpath.basename(self.path_to_file).replace('.csv', '_to_upload.csv')),
                             index=False)
        else:
            for k in range(1, len(self.reviews) // max_rows + 2):
                self.reviews.iloc[(k - 1) * max_rows:k * max_rows, :].to_csv(
                    os.path.join(self.path_to_save_dir,
                                 ntpath.basename(self.path_to_file).replace(
                                     '.csv',
                                     '_to_upload_{}.csv'.format(k))),
                                 index=False)


class MultiRatingsReviewsWrangler:
    def __init__(self, paths_to_ratings_and_reviews, path_to_save_dir):
        self.path_to_save_dir = path_to_save_dir
        self.paths_to_ratings_and_reviews = paths_to_ratings_and_reviews

    def export_voc_files(self):
        for path in self.paths_to_ratings_and_reviews:
            print('\nProcessing file ', ntpath.basename(path), '...')
            products_wrangler = RatingsReviewsWrangler(path, self.path_to_save_dir)
            products_wrangler.export_voc_files()

if __name__ == '__main__':
    reviews_wrangler = RatingsReviewsWrangler('../data/cosmetics_reviews_20200331.csv')
    reviews_wrangler.map_to_template()
    reviews = reviews_wrangler.reviews
    reviews_wrangler.split_and_save(max_rows=100000)
