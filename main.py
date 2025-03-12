import streamlit as st
from function import *
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ================================== #
# ====== Start Streamlit Code ====== #
# ================================== #
st.set_page_config(
    page_title="Sistem Pemeringkatan Aplikasi",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.title("Sistem Pemeringkatan Aplikasi 🏆")
st.divider()
option = st.selectbox(
    "Pilih metode input data:",
    ("Scraping Data Baru", "Upload File CSV"),
)

if option == "Upload File CSV":
    # Upload file CSV
    uploaded_file = st.file_uploader("Upload file CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            # Baca file CSV
            df = pd.read_csv(uploaded_file, sep=None, engine="python")
            st.subheader("Data yang Diunggah")
            st.dataframe(df)

            # Validasi kolom
            required_columns = ['Alternatif', 'Positif', 'Non Positif', 'Jumlah Download', 'Total Ulasan', 'Rating']
            if all(col in df.columns for col in required_columns):
                # Pemeringkatan SAW
                st.subheader("Pemeringkatan dengan Metode SAW")
                ranked_result_saw = saw_ranking(df, criteria_type)
                st.dataframe(ranked_result_saw)

                # Pemeringkatan ARAS
                st.subheader("Pemeringkatan dengan Metode ARAS")
                ranked_result_aras = aras_ranking(df, criteria_type)
                st.dataframe(ranked_result_aras)

                # Perbandingan hasil SAW dan ARAS
                st.subheader("Perbandingan Hasil Pemeringkatan SAW dan ARAS")
                saw_comparison = ranked_result_saw[['Alternatif', 'Peringkat']].rename(columns={'Peringkat': 'SAW'})
                aras_comparison = ranked_result_aras[['Alternatif', 'Peringkat']].rename(columns={'Peringkat': 'ARAS'})
                comparison_df = pd.merge(saw_comparison, aras_comparison, on='Alternatif', how='inner')
                st.dataframe(comparison_df)
                st.bar_chart(comparison_df.set_index('Alternatif'), x_label='Alternatif', y_label='Peringkat', stack=False)
            else:
                st.error(f"File CSV harus memiliki kolom: {', '.join(required_columns)}")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membaca file CSV: {e}")
else:   
    # Form input di halaman utama
    st.header("Masukkan Data Aplikasi")
    num_apps = st.number_input("Jumlah Aplikasi", min_value=1, max_value=50, value=5)
    app_data = {}

    for i in range(num_apps):
        col1, col2 = st.columns(2)
        with col1:
            app_name = st.text_input(f"Nama Aplikasi {i+1}", key=f"app_name_{i}")
        with col2:
            app_id = st.text_input(f"ID Aplikasi {i+1}", key=f"app_id_{i}")
        if app_name and app_id:
            app_data[app_name] = app_id

    # Input tanggal dan jumlah ulasan
    st.header("Masukkan Rentang Tanggal dan Jumlah Ulasan")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Tanggal Mulai", value=datetime(2023, 1, 1))
    with col2:
        end_date = st.date_input("Tanggal Akhir", value=datetime(2024, 12, 31))
    desired_count = st.number_input("Jumlah Ulasan per Aplikasi", min_value=1, max_value=10000, value=10)
    st.divider()
    # Tombol untuk mulai scraping
    if st.button("Mulai"):
        with st.spinner('Sedang memproses...'):
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)

            # Scrape data
            if app_data:
                logging.info("Memulai scraping data ulasan")
                try:
                    df = scrape_all_reviews(app_data, start_date, end_date, desired_count)
                    logging.info("Scraping data ulasan selesai")
                    st.subheader("Hasil Scraping Ulasan")
                    st.dataframe(df)
                    st.subheader("Jumlah ulasan yang berhasil diambil per aplikasi")
                    st.write(df[['appName']].value_counts())

                    # Preprocessing
                    logging.info("Memulai Preprocessing data ulasan")
                    df['clean'] = df['content'].apply(clean_text)  # Cleaning teks
                    df['case_folding'] = df['clean'].apply(lambda x: x.lower())  # Case folding
                    df['norm'] = df['case_folding'].apply(text_normal)  # Normalization
                    df['tokenization'] = df['norm'].apply(tokenize_text)  # Tokenization
                    df['stopword_removal'] = df['tokenization'].apply(remove_stopwords)  # Stopwords removal
                    df['stemming'] = df['stopword_removal'].apply(lambda x: ' '.join(stem_text(x)))  # Stemming
                    logging.info("Preprocessing data ulasan selesai")

                    logging.info("Memulai translate")
                    # Translate
                    df['translate'] = parallel_translate(df)
                    logging.info("Translate selesai")
                    
                    # Analisis Sentimen
                    logging.info("Memulai analisis sentimen")
                    df['score'], df['sentimen'] = zip(*df['translate'].apply(analyze_sentiment))
                    logging.info("Analisis sentimen selesai")

                    # Tampilkan hasil preprocessing dan analisis sentimen
                    st.subheader("Hasil Preprocessing dan Analisis Sentimen")
                    st.dataframe(df[['appName', 'at', 'content', 'clean', 'case_folding', 'norm', 'tokenization', 'stopword_removal', 'stemming', 'translate', 'score', 'sentimen']])

                    # Menampilkan jumlah sentimen per aplikasi
                    st.subheader("Jumlah Sentimen per Aplikasi")

                    grouped = df.groupby('appName')['sentimen'].value_counts().unstack().fillna(0).astype(int)
                    result_df = grouped[['Positif', 'Non Positif']].reset_index()
                    result_df.columns = ['Alternatif', 'Positif', 'Non Positif']
                    result_df.loc['Total'] = grouped.sum()
                    st.dataframe(result_df)
                    st.bar_chart(result_df.drop('Total').set_index('Alternatif'), x_label='Alternatif', y_label='Jumlah Sentimen', stack=False)

                    # Scrape data aplikasi (jumlah unduhan, total ulasan, rating)
                    logging.info("Memulai scraping data aplikasi")
                    app_data_df = scrape_app_data(app_data)
                    logging.info("Scraping data aplikasi selesai")
                    st.subheader("Data Aplikasi (Jumlah Unduhan, Total Ulasan, Rating)")
                    st.dataframe(app_data_df)

                    # Menggabungkan hasil analisis sentimen dengan data aplikasi
                    final_df = pd.merge(result_df, app_data_df, on="Alternatif", how="right")
                    st.subheader("Hasil Gabungan Analisis Sentimen dan Data Aplikasi")
                    st.dataframe(final_df)

                    # Pemeringkatan SAW
                    logging.info("Memulai pemeringkatan SAW")
                    st.subheader("Pemeringkatan dengan Metode SAW")
                    ranked_result_saw = saw_ranking(final_df, criteria_type)
                    st.dataframe(ranked_result_saw)
                    logging.info("Pemeringkatan SAW selesai")

                    # Pemeringkatan ARAS
                    logging.info("Memulai pemeringkatan ARAS")
                    st.subheader("Pemeringkatan dengan Metode ARAS")
                    ranked_result_aras = aras_ranking(final_df, criteria_type)
                    st.dataframe(ranked_result_aras)
                    logging.info("Pemeringkatan ARAS selesai")

                    # Perbandingan hasil SAW dan ARAS
                    logging.info("Memulai perbandingan hasil SAW dan ARAS")
                    st.subheader("Perbandingan Hasil Pemeringkatan SAW dan ARAS")

                    # Ambil kolom Alternatif dan Peringkat dari hasil SAW dan ARAS
                    saw_comparison = ranked_result_saw[['Alternatif', 'Peringkat']].rename(columns={'Peringkat': 'SAW'})
                    aras_comparison = ranked_result_aras[['Alternatif', 'Peringkat']].rename(columns={'Peringkat': 'ARAS'})
                    # Gabungkan hasil SAW dan ARAS berdasarkan kolom Alternatif
                    comparison_df = pd.merge(saw_comparison, aras_comparison, on='Alternatif', how='inner')
                    st.dataframe(comparison_df)
                    st.bar_chart(comparison_df.set_index('Alternatif'), x_label='Alternatif', y_label='Peringkat', stack=False)
                    logging.info("Proses perbandingan selesai")

                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")
            else:
                st.warning("Mohon masukkan data aplikasi terlebih dahulu.")

st.divider()
st.markdown(
    """
    <style>
    @keyframes beat {
        0% { transform: scale(1); }
        50% { transform: scale(1.2); }
        100% { transform: scale(1); }
    }
    .heart {
        display: inline-block;
        animation: beat 1s infinite;
    }
    </style>
    <div style='text-align: center;'>Dibuat dengan <span class='heart'>❤️</span> oleh <a style='text-decoration: none;' href="https://www.linkedin.com/in/wibiemahardhika/" target="_blank">Wibie Mahardhika Adi</a> | © 2025</div>
    """,
    unsafe_allow_html=True
)