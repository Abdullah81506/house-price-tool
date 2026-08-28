import pandas as pd
import re
from location_parser import extract_area, extract_block

def parse_price(price_text):
    if not price_text:
        return None
    price_text = price_text.replace(',', '')
    match = re.search(r"\d+\.?\d*", price_text)
    if not match:
        return None
    number = float(match.group())
    if 'lakh' in price_text.lower():
        number *= 100_000
    elif 'crore' in price_text.lower():
        number *= 10_000_000
    elif 'arab' in price_text.lower():
        number *= 1_000_000_000
    return number

def parse_size(size_text):  # to convert size in one unit only
    if not size_text:
        return None
    size_text = size_text.replace(',', '')
    match = re.search(r"\d+\.?\d*", size_text)
    if not match:
        return None
    number = float(match.group())
    if 'kanal' in size_text.lower():
        number *= 20
    elif 'sqft' in size_text.lower():
        number /= 272.25
    return number

# def extract_area(location_text):  # to extract the broader area from location
#     if not location_text:
#         return 'Other'
#     text = location_text.split(',')[0]
#     text = text.split(' - ')[0]
#     return ' '.join(text.split())

def extract_title_features(title):
    if not title:
        return pd.Series([0, 0, 0, 0, 0, 0])
    t = title.lower()
    is_new = int('new' in t or 'brand' in t)
    is_furnished = int('furnished' in t)
    is_luxury = int('luxury' in t or 'ultra' in t)
    has_basement = int('basement' in t)
    is_corner = int('corner' in t)
    is_commercial = int(bool(re.search(r'semi.?commercial|commercial house|commercial property|commercial use|commercial plot', t)))
    return pd.Series([is_new, is_furnished, is_luxury, has_basement, is_corner, is_commercial])

FLOOR_WORDS = {
    'ground': 0, 'first': 1, 'second': 2, 'third': 3, 'fourth': 4,
    'fifth': 5, 'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10,
}

def extract_floor(title):
    if not title:
        return None
    t = title.lower()
    match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*floor', t)
    if match:
        return float(match.group(1))
    for word, num in FLOOR_WORDS.items():
        if f'{word} floor' in t:
            return float(num)
    return None

if __name__ == '__main__':

    df_houses = pd.read_csv('listings_houses.csv')
    df_flats = pd.read_csv('listings_flats.csv')
    df = pd.concat([df_houses, df_flats], ignore_index=True)
    details = pd.read_csv('detail_features.csv')
    if '_error' in details.columns:
        details = details[details['_error'].isna()].drop(columns=['_error'])
    df = df.merge(details, on='url', how='left')
    print("after detail merge:", df.shape)
    print("detail_location fill:", df['detail_location'].notna().mean())
    print("Combined shape:", df.shape)
    print(df['property_type'].value_counts())

    from collections import Counter
    import re as re_temp
    all_words = []
    for title in df['title'].dropna():
        words = re_temp.findall(r'[a-z]+', title.lower())
        all_words.extend(words)
    word_counts = Counter(all_words)
    print(word_counts.most_common(50))

    print(df['price'].str.extract(r'([A-Za-z]+)$')[0].value_counts())
    print(df['size'].str.extract(r'([A-Za-z]+)$')[0].value_counts())

    df['price_numeric'] = df['price'].apply(parse_price)
    df['size_marla'] = df['size'].apply(parse_size)
    df['best_location'] = df['detail_location'].fillna(df['location'])
    df['area'] = df['best_location'].apply(extract_area)
    df['block'] = df['best_location'].apply(extract_block)
    df[['is_new', 'is_furnished', 'is_luxury', 'has_basement', 'is_corner', 'is_commercial']] = \
    df['title'].apply(extract_title_features)
    df['floor'] = df['title'].apply(extract_floor)
    print(df.nlargest(10, 'size_marla')[['title', 'size', 'size_marla', 'property_type']])
    area_counts = df['area'].value_counts()
    print(area_counts.describe())
    rare_areas = area_counts[area_counts < 5].index
    df['area'] = df['area'].apply(lambda x: 'Other' if x in rare_areas else x)

    print(df.shape)
    print(df.columns)

    # Find the known Central Park style bug by content, not a hardcoded index
    suspect = df[
        df['title'].str.contains('Corner House', case=False, na=False) &
        df['location'].str.contains('Central Park', case=False, na=False)
        ]
    print(suspect[['title', 'location', 'size', 'size_marla']])
    suspect2 = df[df['title'].str.contains('NNEW DOUBLE STORY', case=False, na=False)]
    print(suspect2[['title', 'size', 'size_marla']])
    df = df.drop(index=suspect2.index)
    suspect_flat = df[
        df['title'].str.contains('Premium 1-Bed Apartment In Indigo Heights', case=False, na=False)
    ]
    print(suspect_flat[['title', 'size', 'size_marla']])
    df = df.drop(index=suspect_flat.index)
    suspect2_flat = df[
        df['title'].str.contains('Luxury 2 bed Room Apartment', case=False, na=False) &
        df['location'].str.contains('Gulberg 3', case=False, na=False)
        ]
    print(suspect2_flat[['title', 'location', 'size', 'size_marla']])
    df = df.drop(index=suspect2_flat.index)
    print(df.duplicated().sum())
    pd.set_option('display.max_columns', None)
    # If suspect has rows and you confirm it's the same kind of bug, drop by its real index, e.g
    # df = df.drop(index=suspect.index)
    df = df.drop_duplicates()
    before = len(df)
    df = df.drop_duplicates(subset=['url'], keep='first')
    print(f"dropped {before - len(df)} rows with repeated urls")
    df.to_csv('listings_cleaned.csv', index=False)
    print("Saved listings_cleaned.csv")
    print(df[df['property_type'] == 'Flat']['floor'].isnull().sum())
    print(df[df['property_type'] == 'House']['floor'].isnull().sum())

    # ============================================================
    # print(df.loc[df.isna().any(axis='columns')])
    # print(df.isnull().sum())
    # print(df.duplicated().sum())
    # print(df[df['title'].isna()]['page'].value_counts())
    # print(df[['price', 'size', 'location', 'beds', 'baths']].sample(10))
    # print(df['beds'].unique())
    # print(df['baths'].unique())
    # print(df['beds'].dtype)
    # sample = df['price'].unique()[:20]
    # for val in sample:
    #     print(val, '->', parse_price(val))
    # sample2 = df['size'].unique()[:20]
    # for val in sample2:
    #     print(val, '->', parse_size(val))
    # sample3 = df['location'].unique()[:20]
    # for val in sample3:
    #     print(val, '->', extract_area(val))
    # print(df['location'].nunique())
    # print(df['area'].value_counts())
    # print(df['area'].nunique())
    # print(df[['price_numeric', 'size_marla', 'beds', 'baths', 'area']].sample(10))
    # print(sum('corner' in t.lower() for t in df['title'].dropna()))
    # print(sum('commercial' in t.lower() for t in df['title'].dropna()))
    # print(df[['title', 'is_new', 'is_furnished', 'is_luxury', 'has_basement', 'is_corner', 'is_commercial']].sample(10))
    # print(df.loc[5459, 'title'])
    # print(df[df['is_commercial'] == 1]['title'].tolist())
    # print(df['is_commercial'].sum())
