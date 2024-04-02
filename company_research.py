import csv
import requests
from bs4 import BeautifulSoup
import chardet
import pandas as pd
import os
import re
from collections import defaultdict
from janome.tokenizer import Tokenizer
import matplotlib.pyplot as plt
import prince  # Correspondence Analysis
from wordcloud import WordCloud
import mca
from adjustText import adjust_text
import csv
import requests
from bs4 import BeautifulSoup

#上限ワード数設定
word_max = 30

def extract_text_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    # 特定の文字を取り除く（オプショナル）
    text = ''.join(filter(lambda x: x.isalpha(), text))
    return text

# 入力CSVファイルから企業名とURLを読み込む
with open('URL to text/input.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # ヘッダー行をスキップ
    company_urls = [(row[0], row[1]) for row in reader if len(row) > 1]

# 出力データの準備
results = []
for company, url in company_urls:
    if url:
        try:
            response = requests.get(url)
            html = response.text
            text = extract_text_from_html(html)
            results.append([company, url, text])
        except requests.RequestException as e:
            print('Error fetching URL:', url, '; Error:', e)
            results.append([company, url, 'Error'])

# 処理されたデータを出力CSVファイルに書き出す
#with open('元データ/output.csv', 'w', newline='', encoding='utf-8') as csvfile:
#    writer = csv.writer(csvfile)
#    writer.writerow(['企業名', 'URL', 'Extracted Text'])  # ヘッダー
#    writer.writerows(results)

# DataFrameを作成
df = pd.DataFrame(results, columns=['企業名', 'URL', 'Extracted Text'])
# CSVファイルに書き出す
# 出力ディレクトリ
output_directory = '元データ'
# CSVファイルに書き出す
df.to_csv(os.path.join(output_directory, 'output.csv'), index=False, encoding='utf-8')

#ユニーク化

# 日本語の文字にマッチする正規表現パターン（漢字、ひらがな、カタカナ）
japanese_pattern = re.compile(r'([A-Za-z]+|[\u3000-\u303F\u3040-\u309F\u30A0-\u30FF]+)')

# 除外する単語が含まれるCSVファイルのパス
excluded_words_file = '除外する単語.csv'

# 除外する単語のリストを読み込む
with open(excluded_words_file, 'r', encoding='utf-8') as file:
    excluded_words = [row[0] for row in csv.reader(file)]

# csvファイルのディレクトリパス
csv_directory = '元データ'

# csvファイルのリストを取得
csv_files = [file for file in os.listdir(csv_directory) if file.endswith('.csv')]

# データフレームを格納するリスト
dfs = []

# Janomeのインスタンスを生成
tokenizer = Tokenizer()

for csv_file in csv_files:
    # csvファイルのエンコーディングを判定
    csv_file_path = os.path.join(csv_directory, csv_file)
    with open(csv_file_path, 'rb') as file:
        result = chardet.detect(file.read())
        encoding = result['encoding']

    # csvファイルを読み込む
    df = pd.read_csv(csv_file_path, encoding=encoding)

    # 単語の出現企業数を格納する辞書
    word_count = defaultdict(lambda: defaultdict(int))

    for index, row in df.iterrows():
        company_name = str(row['企業名'])
        text = str(row['Extracted Text'])

        # Janomeで形態素解析
        for token in tokenizer.tokenize(text):
            word = token.surface
            part_of_speech = token.part_of_speech.split(',')[0]

            # 除外する単語をフィルタリング
            if part_of_speech == '名詞' and word not in excluded_words:
                word_count[word][company_name] = 1

    # 辞書をデータフレームに変換
    word_df = pd.DataFrame.from_dict(word_count, orient='index').fillna(0)
    word_df = word_df.reset_index().rename(columns={'index': '単語'})
    dfs.append(word_df)

# データフレームをマージ
merged_df = pd.concat(dfs, ignore_index=True)

# ピボットテーブルの作成
pivot_table = merged_df.groupby('単語').sum()
pivot_table.reset_index(inplace=True)

# 合計列を追加
pivot_table['合計'] = pivot_table.sum(axis=1)

# 合計列を降順でソート
pivot_table = pivot_table.sort_values(by='合計', ascending=False)

# 合計列を削除
pivot_table = pivot_table.drop('合計', axis=1)

# 上位100件に絞り込む
pivot_table = pivot_table.head(word_max)

# 出力ディレクトリ
output_directory = '出力結果'

# 出力ディレクトリがない場合は作成
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# ピボットテーブルをCSVファイルとして保存
pivot_table.to_csv(os.path.join(output_directory, 'unique_words.csv'), index=False, encoding='utf-8-sig')

#別々

# 日本語の文字にマッチする正規表現パターン（漢字、ひらがな、カタカナ）
japanese_pattern = re.compile(r'^[\u3000-\u303F\u3040-\u309F\u30A0-\u30FF]+$')

# 除外する単語が含まれるCSVファイルのパス
excluded_words_file = '除外する単語.csv'

# 除外する単語のリストを読み込む
with open(excluded_words_file, 'r', encoding='utf-8') as file:
    excluded_words = [row[0] for row in csv.reader(file)]

# csvファイルのディレクトリパス
csv_directory = '元データ'

# csvファイルのリストを取得
csv_files = [file for file in os.listdir(csv_directory) if file.endswith('.csv')]

# Janomeのインスタンスを生成
tokenizer = Tokenizer()

# 出力ディレクトリ
output_directory = '企業別カウントファイル'

# 出力ディレクトリがない場合は作成
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

for csv_file in csv_files:
    # csvファイルのエンコーディングを判定
    csv_file_path = os.path.join(csv_directory, csv_file)
    with open(csv_file_path, 'rb') as file:
        result = chardet.detect(file.read())
        encoding = result['encoding']

    # csvファイルを読み込む
    df = pd.read_csv(csv_file_path, encoding=encoding)

    # URLが日本語のみの行を残す
    #df = df[df['URL'].apply(lambda x: bool(japanese_pattern.match(str(x))))]

    # 単語の出現回数を格納する辞書
    word_count = defaultdict(lambda: defaultdict(int))

    for index, row in df.iterrows():
        company_name = str(row['企業名'])
        text = str(row['Extracted Text'])

        # Janomeで形態素解析
        for token in tokenizer.tokenize(text):
            word = token.surface
            part_of_speech = token.part_of_speech.split(',')[0]

            # 除外する単語をフィルタリング
            if part_of_speech == '名詞' and word not in excluded_words:
                word_count[word][company_name] += 1

    # 辞書をデータフレームに変換し、企業名でグループ化
    word_df = pd.DataFrame.from_dict(word_count, orient='index').fillna(0)
    word_df = word_df.reset_index().rename(columns={'index': '単語'})

    for company in word_df.columns[1:]: # 最初の列（'単語'）を除外
        # 企業ごとのデータフレームを生成
        company_df = word_df[['単語', company]].copy()
        company_df.rename(columns={company: '出現回数'}, inplace=True)
        company_df = company_df[company_df['出現回数'] > 0] # 出現回数が0より大きい行のみを含める

        # 出現回数で降順にソートし、上位指定単語までを抽出
        company_df = company_df.sort_values(by='出現回数', ascending=False).head(word_max)

        # 企業ごとのファイルを出力
        company_output_path = os.path.join(output_directory, f'{company}_export.csv')
        company_df.to_csv(company_output_path, index=False, encoding='utf-8-sig')

#ワードクラウド

# 追加部分 フォントを指定する。
plt.rcParams["font.family"] = "IPAexGothic"

# 取り込み元のディレクトリ名
input_directory = '企業別カウントファイル'

# 画像を保存するディレクトリ名
output_directory = '出力画像'

# 出力ディレクトリがない場合は作成
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# 指定されたディレクトリ内の全CSVファイルを取得
csv_files = [f for f in os.listdir(input_directory) if f.endswith('.csv')]

for csv_file in csv_files:
    # CSVファイルをデータフレームとして読み込む
    df = pd.read_csv(os.path.join(input_directory, csv_file), encoding='UTF-8')

    # 単語とその出現回数を辞書に格納
    word_frequencies = {row['単語']: int(row['出現回数']) for index, row in df.iterrows()}

    # ワードクラウドの生成
    wordcloud = WordCloud(width=800, height=400, background_color='white', 
                          font_path="/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc").generate_from_frequencies(word_frequencies)

    # プロットの表示
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.title('Word Cloud for ' + csv_file.replace('_export.csv', ''))
    plt.axis('off')  # 軸を非表示に

    # 画像をファイルとして保存
    image_path = os.path.join(output_directory, csv_file.replace('.csv', '.png'))
    plt.savefig(image_path)
    plt.close()
    
    
#コレスポンデンス分析

# コレスポンデンス分析を行うCSVファイルのパス
csv_file_path = '出力結果/unique_words.csv'

# CSVファイルの読み込み
df = pd.read_csv(csv_file_path, index_col=0)

# コレスポンデンス分析
mca_counts = mca.MCA(df, benzecri=False)
rows = mca_counts.fs_r(N=2)
cols = mca_counts.fs_c(N=2)

# 表のサイズの調整
plt.figure(figsize=(15, 8))

# 行側のプロット
plt.scatter(rows[:, 0], rows[:, 1], marker="o", color="b")

# 列側のプロット
plt.scatter(cols[:, 0], cols[:, 1], marker="x", color="r")

# アノテーションのリストを作成
texts = []
for label, x, y in zip(df.index, rows[:, 0], rows[:, 1]):
    texts.append(plt.text(x, y, label, color="b"))
for label, x, y in zip(df.columns, cols[:, 0], cols[:, 1]):
    texts.append(plt.text(x, y, label, color="r"))

# テキストの重なりを調整
adjust_text(texts)

# xy軸の表示
plt.axhline(0, color='gray')
plt.axvline(0, color='gray')

# グラフのタイトルと軸ラベル
plt.title('コレスポンデンス分析')
plt.xlabel('次元1')
plt.ylabel('次元2')

# 画像をファイルとして保存
image_path = os.path.join(output_directory, 'コレスポンデンス分析.png')
plt.savefig(image_path)