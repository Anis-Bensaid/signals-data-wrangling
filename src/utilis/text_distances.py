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
    item_description = str(row['item_description']).lower().replace('clinique', '').replace('origins', '').replace(
        'tom ford', '').replace('la mer', '').replace('estee lauder', '').replace('mac', '').replace('bb', '').replace(
        'bobbi', '').replace('brown', '')
    product = str(row['product']).lower()
    jaro = textdistance.jaro_winkler(item_description, product)
    try:
        fuzzi = fuzz.partial_ratio(item_description, product) / 100
    except ValueError:
        return jaro
    return np.average([fuzzi, jaro], weights=[0.95, 0.05])


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
