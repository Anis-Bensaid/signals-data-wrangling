from fuzzywuzzy import fuzz
import textdistance
import numpy as np


def brands_custom_distance(row):
    """
    Calculates a distance score between two sentences. In this case elc_brand and brand. The score is between 0 and 1, 1 being a good match.
    """
    # jaccard = textdistance.jaccard(str(row['brand']).lower().replace('.','').replace('&','and'), str(row['elc_brand']).lower().replace('.','').replace('é','e'))
    jaro = textdistance.jaro_winkler(str(row['Brand']).lower().replace('.', '').replace('&', 'and'),
                                     str(row['ELC_Brand']).lower().replace('.', '').replace('é', 'e'))
    try:
        fuzzi = fuzz.partial_ratio(str(row['Brand']).lower().replace('.', '').replace('&', 'and'),
                                   str(row['ELC_Brand']).lower().replace('.', '').replace('é', 'e')) / 100
    except ValueError:
        return jaro
    return np.average([fuzzi, jaro], weights=[0.4, 0.6])


def item_description_custom_distance(row):
    """
    Calculates a distance score between two sentences. In this case elc_brand and brand. The score is between 0 and 1, 1 being a good match.
    """
    # jaccard = textdistance.jaccard(str(row['brand']).lower().replace('.','').replace('&','and'), str(row['elc_brand']).lower().replace('.','').replace('é','e'))
    jaro = textdistance.jaro_winkler(str(row['Product']).lower(), str(row['Item_Description']).lower())
    try:
        fuzzi = fuzz.partial_ratio(str(row['Product']).lower(), str(row['Item_Description']).lower()) / 100
    except ValueError:
        return jaro
    return np.average([fuzzi, jaro], weights=[0.45, 0.55])


def subcategory_custom_distance(row):
    """
    Calculates a distance score between two sentences. In this case elc_brand and brand. The score is between 0 and 1, 1 being a good match.
    """
    jaro = textdistance.jaro_winkler(str(row['Sub_Category']).lower(),
                                     str(row['Item_Description']).lower().replace('.', '').replace('&', 'and'))
    try:
        fuzzi = fuzz.partial_ratio(str(row['Item_Description']).lower().replace('.', '').replace('&', 'and'),
                                   str(row['Sub_Category'])) / 100
    except ValueError:
        return jaro
    return np.average([fuzzi, jaro], weights=[0.5, 0.5])
