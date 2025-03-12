from google_play_scraper import Sort, reviews, app
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
import requests

# Fungsi untuk mengambil ulasan
def fetch_reviews_batch(app_info, start_date, end_date, batch_size, desired_count):
    appName, app_id = app_info
    all_reviews, continuation_token = [], None

    while len(all_reviews) < desired_count:
        result, continuation_token = reviews(
            app_id,
            lang='id',
            country='id',
            sort=Sort.NEWEST,
            count=batch_size,
            continuation_token=continuation_token
        )

        for review in result:
            review_date = pd.to_datetime(review['at'])
            if start_date <= review_date <= end_date:
                review['appName'] = appName
                all_reviews.append(review)
            if len(all_reviews) >= desired_count:
                break

        if not result or continuation_token is None:
            break

    return all_reviews

# Fungsi untuk mengelola scraping semua ulasan
def scrape_all_reviews(app_list, start_date, end_date, desired_count, batch_size=1000):
    all_reviews = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(fetch_reviews_batch, (appName, app_id), start_date, end_date, batch_size, desired_count)
            for appName, app_id in app_list.items()
        ]
        for future in futures:
            all_reviews.extend(future.result())

    return pd.DataFrame(all_reviews)

# Fungsi untuk scraping data aplikasi
def scrape_app_data(app_list):
    scraped_data = []

    for app_name, app_id in app_list.items():
        try:
            result = app(
                app_id,
                lang='id',
                country='id'
            )
            scraped_data.append({
                "Alternatif": app_name,
                "Jumlah Download": result["minInstalls"],
                "Total Ulasan": result["ratings"],
                "Rating": round(result["score"], 1)
            })
        except Exception as e:
            print(f"Error scraping {app_name}: {e}")

    return pd.DataFrame(scraped_data)

# Fungsi Cleaning
def clean_text(text):
    # Menghapus URL
    text = re.sub(r'https?://\S+|www\.\S+', '', text)

    # Menghapus tag HTML
    text = re.sub(r'<.*?>', '', text)

    # Menghapus emoji
    emoji_pattern = re.compile("[" 
                               u"\U0001F600-\U0001F64F" 
                               u"\U0001F300-\U0001F5FF" 
                               u"\U0001F680-\U0001F6FF" 
                               u"\U0001F1E0-\U0001F1FF" 
                               "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)

    # Menghapus angka dan karakter khusus
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)

    # Menghapus spasi yang berlebih
    text = re.sub(r'\s+', ' ', text).strip()

    return text

# Fungsi Normalization
def text_normal(text):
    key_norm = pd.read_csv('https://raw.githubusercontent.com/Mhrd22/keynorm/master/key_norm.csv')
    key_norm_dict = dict(zip(key_norm['singkat'], key_norm['hasil']))

    return ' '.join([key_norm_dict.get(word, word) for word in text.split()])

# Fungsi Tokenization
def tokenize_text(text):
    nltk.download('punkt_tab', quiet=True) 
    nltk.download('punkt', quiet=True)
    return word_tokenize(text)

# Fungsi Stopwords Removal
def remove_stopwords(text):
    nltk.download('stopwords', quiet=True)
    stop_words = stopwords.words('indonesian')
    return [word for word in text if word not in stop_words]

# Fungsi Stemming
def stem_text(text):
    factory = StemmerFactory()
    stemmer = factory.create_stemmer()

    return [stemmer.stem(word) for word in text]

# Fungsi Translate
def translate_text(text, src_lang='id', dest_lang='en'):
    url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl={}&tl={}&dt=t&q={}'.format(src_lang, dest_lang, text)
    response = requests.get(url)
    if response.status_code == 200:
        translated_text = response.json()[0][0][0]
        return translated_text
    else:
        return text  # Return original text in case of failure

# Fungsi untuk menerjemahkan dengan paralelisme
def parallel_translate(df, max_workers=10):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(translate_text, df['stemming']))
    return results

# Fungsi Sentiment Analysis
def analyze_sentiment(text):
    nltk.download('vader_lexicon', quiet=True)
    sid = SentimentIntensityAnalyzer()
    analysis = sid.polarity_scores(text)
    polarity_score = analysis['compound']
    sentiment = 'Positif' if polarity_score > 0.05 else 'Non Positif'
    return polarity_score, sentiment

# Kriteria dan tipe kriteria untuk SAW dan ARAS
criteria_type = {
    'Positif': 'benefit',
    'Non Positif': 'cost',
    'Jumlah Download': 'benefit',
    'Total Ulasan': 'benefit',
    'Rating': 'benefit'
}

# Fungsi Pemeringkatan SAW
def saw_ranking(df, criteria_type, weight=0.2):
    df_saw = df.copy()

    # 1. Normalisasi Matriks
    for col, c_type in criteria_type.items():
        if c_type == 'benefit':
            df_saw[f'Norm_{col}'] = (df_saw[col] / df_saw[col].max()).round(3)
        else:  # cost
            df_saw[f'Norm_{col}'] = (df_saw[col].min() / df_saw[col]).round(3)
    df_saw = df_saw.fillna(0)

    # 2. Pembobotan Matriks
    for col in criteria_type.keys():
        df_saw[f'Bobot_{col}'] = (df_saw[f'Norm_{col}'] * weight).round(3)

    # 3. Menghitung Nilai Akhir
    bobot_cols = [f'Bobot_{col}' for col in criteria_type.keys()]
    df_saw['Nilai_Akhir'] = df_saw[bobot_cols].sum(axis=1).round(3)

    # 4. Menghitung Peringkat
    # ranked_df_saw = df_saw.sort_values(by='Nilai_Akhir', ascending=False, ignore_index=True)
    ranked_df_saw = df_saw
    ranked_df_saw['Peringkat'] = ranked_df_saw['Nilai_Akhir'].rank(method='first', ascending=False).astype(int)

    return ranked_df_saw

# Fungsi Pemeringkatan ARAS
def aras_ranking(df, criteria_type, weight=0.2):
    df_aras = df.copy()

    # 1. Membuat matriks keputusan dengan menambahkan alternatif optimal
    optimal_values = {col: df_aras[col].max() if ctype == "benefit" else df_aras[col].min() for col, ctype in criteria_type.items()}
    optimal_row = pd.DataFrame([["A0"] + list(optimal_values.values())], columns=df_aras.columns)
    df_aras = pd.concat([optimal_row, df_aras], ignore_index=True)

    # 2. Normalisasi matriks
    for col, ctype in criteria_type.items():
        if ctype == 'benefit':
            df_aras[f'Norm_{col}'] = (df_aras[col] / df_aras[col].sum()).round(3)
        else:  # cost
            df_aras[f'Norm_{col}'] = (1 / df_aras[col])
            df_aras[f'Norm_{col}'] /= df_aras[f'Norm_{col}'].sum()
            df_aras[f'Norm_{col}'] = df_aras[f'Norm_{col}'].round(3)
    df_aras = df_aras.fillna(0)
    
    # 3. Perhitungan bobot matriks
    for col in criteria_type.keys():
        df_aras[f'Bobot_{col}'] = (df_aras[f'Norm_{col}'] * weight).round(3)

    # 4. Menghitung nilai optimum
    bobot_cols = [f'Bobot_{col}' for col in criteria_type.keys()]
    df_aras['Nilai_Optimum'] = df_aras[bobot_cols].sum(axis=1).round(3)

    # 5. Menghitung peringkat
    S0 = df_aras.at[0, 'Nilai_Optimum']
    df_aras['Nilai_Akhir'] = (df_aras['Nilai_Optimum'] / S0).round(3)

    # Simpan A0 sebelum pengurutan
    A0_row = df_aras.iloc[0:1]  # Ambil baris pertama (A0)

    # Buat dataframe tanpa A0 untuk perangkingan
    # ranked_df_aras = df_aras.iloc[1:].sort_values(by='Nilai_Akhir', ascending=False, ignore_index=True)
    ranked_df_aras = df_aras.iloc[1:]
    ranked_df_aras['Peringkat'] = ranked_df_aras['Nilai_Akhir'].rank(method='first', ascending=False)

    # Gabungkan kembali A0 di akhir
    final_result = pd.concat([A0_row, ranked_df_aras], ignore_index=True)
    final_result['Peringkat'] = final_result['Peringkat'].fillna(0).astype(int)

    return final_result