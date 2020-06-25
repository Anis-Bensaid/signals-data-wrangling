import pandas as pd
import json

class RatingsReviewsWrangler():
    def __init__(self, path_to_file):
        self.path_to_file = path_to_file
        self.reviews = pd.read_csv(path_to_file, low_memory=False)
        self.is_wrangled = False

    def wrangle(self):
        with open('../../data/reviews_template_mapping.txt') as f:
            columns_mapping = json.load(f)
        self.reviews.rename(columns=columns_mapping, inplace=True)
        template = pd.read_csv('../../data/reviews_template.csv')
        columns_not_mapped = [col for col in self.reviews.columns if not col in template.columns]
        columns_not_filled = [col for col in template.columns if not col in self.reviews.columns]
        if columns_not_mapped:
            print('The following columns exist in the file but have not been found in the template. Make sure they '
                  'are properly mapped, otherwise they will be deleted:')
            print(columns_not_mapped)
        if columns_not_filled:
            print('The following columns exist in the template but have not been found in the file. Kake sure they are '
                  'properly mapped, otherwise they will be filled with missing data:')
            print(columns_not_filled)
        self.reviews = pd.concat([template, self.reviews], ignore_index=True, join='inner')
        self.is_wrangled = True

    def split_and_save(self, max_rows=199999):
        if not self.is_wrangled:
            self.wrangle()
        if len(self.reviews) <= max_rows:
            self.reviews.to_csv(self.path_to_file.replace('.csv', '_to_upload.csv'), index=False)
        else:
            for k in range(1, len(self.reviews)//max_rows+2):
                self.reviews.iloc[(k-1)*max_rows:k*max_rows, :].to_csv(
                    self.path_to_file.replace('.csv', '_to_upload_'+str(k)+'.csv'), index=False)

if __name__ == '__main__':
    reviews_wrangler = RatingsReviewsWrangler('../../data/cosmetics_reviews_20200331.csv')
    reviews_wrangler.wrangle()
    reviews = reviews_wrangler.reviews
    reviews_wrangler.split_and_save(max_rows=100000)

