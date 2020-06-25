from fuzzywuzzy import fuzz
import textdistance
import numpy as np


def brands_custom_distance(row):
    """
    Calculates a distance score between two sentences. In this case elc_brand and brand. The score is between 0 and 1, 1 being a good match.
    """
    # jaccard = textdistance.jaccard(str(row['brand']).lower().replace('.','').replace('&','and'), str(row['elc_brand']).lower().replace('.','').replace('é','e'))
    jaro = textdistance.jaro_winkler(str(row['brand']).lower().replace('.', '').replace('&', 'and'),
                                     str(row['elc_brand']).lower().replace('.', '').replace('é', 'e'))
    fuzzi = fuzz.partial_ratio(str(row['brand']).lower().replace('.', '').replace('&', 'and'),
                               str(row['elc_brand']).lower().replace('.', '').replace('é', 'e')) / 100
    return np.average([fuzzi, jaro], weights=[0.4, 0.6])


def names_custom_distance(row):
    """
    Calculates a distance score between two sentences. In this case elc_brand and brand. The score is between 0 and 1, 1 being a good match.
    """
    # jaccard = textdistance.jaccard(str(row['brand']).lower().replace('.','').replace('&','and'), str(row['elc_brand']).lower().replace('.','').replace('é','e'))
    jaro = textdistance.jaro_winkler(str(row['product']).lower(), str(row['item_description']).lower())
    fuzzi = fuzz.partial_ratio(str(row['product']).lower(), str(row['item_description']).lower()) / 100
    return np.average([fuzzi, jaro], weights=[0.45, 0.55])


def subcategory_custom_distance(row):
    """
    Calculates a distance score between two sentences. In this case elc_brand and brand. The score is between 0 and 1, 1 being a good match.
    """
    jaro = textdistance.jaro_winkler(str(row['sub_category']).lower(),
                                     str(row['item_description']).lower().replace('.', '').replace('&', 'and'))
    fuzzi = fuzz.partial_ratio(str(row['item_description']).lower().replace('.', '').replace('&', 'and'),
                               str(row['sub_category'])) / 100
    return np.average([fuzzi, jaro], weights=[0.5, 0.5])
