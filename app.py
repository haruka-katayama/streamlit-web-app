import streamlit as st
import pandas as pd
import subprocess
import os
import glob
import zipfile
from io import BytesIO
import base64

# 現在の除外単語リストをダウンロードするための関数
def download_csv(csv_file, download_filename):
    if os.path.exists(csv_file):
        with open(csv_file, "rb") as file:
            st.markdown(
                f'<a href="data:file/csv;base64,{base64.b64encode(file.read()).decode()}" download="{download_filename}"><button type="button">現在の除外単語リストをダウンロードする</button></a>',
                unsafe_allow_html=True
            )

# 除外する単語.csvを表示するための関数
def update_excluded_words():
    st.subheader('除外単語リスト')

    # ユーザーが新しいCSVをアップロード
    uploaded_file = st.file_uploader("新しい除外する単語のCSVをアップロードしてください", type=["csv"])

    if uploaded_file is not None:
        # アップロードされたCSVを読み込む
        new_data = pd.read_csv(uploaded_file)
        st.write("アップロードされたリスト:", new_data)

        if st.button("リストを更新"):
            # 新しいデータをCSVファイルに保存
            new_data.to_csv('除外する単語.csv', index=False)
            st.success("リストが更新されました。")

    # 既存のリストとそのダウンロードボタンを表示
    csv_file = '除外する単語.csv'
    download_csv(csv_file, "excluded_words.csv")

    if os.path.exists(csv_file):
        existing_data = pd.read_csv(csv_file)
        st.write("現在のリスト:", existing_data)
    else:
        st.write("現在のリストは空です。")

# CSVファイルの内容を処理する関数
def process_uploaded_file(uploaded_file):
    df = pd.read_csv(uploaded_file)
    if '企業名' in df.columns and 'URL' in df.columns:
        st.session_state.competitor_entries = df[['企業名', 'URL']].to_dict(orient='records')
        st.write(pd.DataFrame(st.session_state.competitor_entries))

# メインページのUI
def main_page():
    st.title("競合分析アプリ")

    format_directory = "フォーマット"
    format_files = glob.glob(os.path.join(format_directory, '*.csv'))

    if format_files:
        format_file_path = format_files[0]
        with open(format_file_path, "rb") as file:
            b64 = base64.b64encode(file.read()).decode()
            st.markdown(f'<a href="data:file/csv;base64,{b64}" download="format.csv"><button type="button">CSVフォーマットをダウンロードする</button></a>', unsafe_allow_html=True)
    else:
        st.warning("CSVフォーマットが見つかりません。")

    uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])
    if uploaded_file is not None:
        process_uploaded_file(uploaded_file)

    if st.button("実行"):
        if 'competitor_entries' in st.session_state:
            input_folder_path = 'URL to text'
            os.makedirs(input_folder_path, exist_ok=True)
            input_csv_path = os.path.join(input_folder_path, 'input.csv')
            df = pd.DataFrame(st.session_state['competitor_entries'])
            df.to_csv(input_csv_path, index=False, encoding='utf-8')

            st.info("処理を実行中です。しばらくお待ちください...")
            subprocess.run(["python", "company_research.py"])
            st.success("スクリプトの実行が完了しました。")

            image_directory = '出力画像'
            image_paths = glob.glob(os.path.join(image_directory, '*.png'))

            if image_paths:
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for image_path in image_paths:
                        zip_file.write(image_path, os.path.basename(image_path))

                zip_buffer.seek(0)
                st.download_button(
                    label="すべての画像をダウンロード",
                    data=zip_buffer,
                    file_name="images.zip",
                    mime="application/zip"
                )
            else:
                st.error("画像ファイルが見つかりません。")
        else:
            st.warning("CSVファイルをアップロードしてください。")

    if st.button("データ削除"):
        st.info("データ削除スクリプトを実行中です。しばらくお待ちください...")
        subprocess.run(["python", "File_Delete.py"])
        st.success("データ削除が完了しました。")

# メインのUI構築部分
def main():
    st.sidebar.title("ナビゲーション")
    page = st.sidebar.radio('ページを選択', ['ホーム', '除外単語リスト'])

    if page == 'ホーム':
        main_page()
    elif page == '除外単語リスト':
        update_excluded_words()

if __name__ == "__main__":
    main()
