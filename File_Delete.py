import os

# 各ディレクトリの相対パス
directories = [
    '元データ',
    '出力結果',
    '企業別カウントファイル',
    '出力画像'
]

# 各ディレクトリ内のファイルを削除
for directory in directories:
    # ディレクトリの絶対パス
    directory_path = directory
    
    # ディレクトリ内のファイルを取得
    files = os.listdir(directory_path)
    
    # ファイルを削除
    for file in files:
        file_path = os.path.join(directory_path, file)
        os.remove(file_path)
        print(f'{file_path} を削除しました。')
