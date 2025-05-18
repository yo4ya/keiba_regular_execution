import pickle
import IPython
from sklearn.model_selection import train_test_split
from numpy.core.numeric import NaN
import pandas as pd
import codecs
from sklearn.preprocessing import LabelEncoder
import re
import numpy as np
import lightgbm as lgb
import matplotlib.pyplot as plt
import warnings
from sklearn.preprocessing import LabelEncoder
warnings.filterwarnings('ignore')

df = pd.DataFrame

# 各種関数

# データフレームを綺麗に出力する関数


def display(*dfs, head=True):
    for df in dfs:
        IPython.display.display(df.head() if head else df)

# 特徴量重要度を棒グラフでプロットする関数


def plot_feature_importance(df):
    n_features = len(df)                              # 特徴量数(説明変数の個数)
    # df_importanceをプロット用に特徴量重要度を昇順ソート
    df_plot = df.sort_values('importance')
    f_importance_plot = df_plot['importance'].values  # 特徴量重要度の取得
    plt.barh(range(n_features), f_importance_plot, align='center')
    cols_plot = df_plot['feature'].values             # 特徴量の取得
    plt.yticks(np.arange(n_features), cols_plot)      # x軸,y軸の値の設定
    plt.xlabel('Feature importance')                  # x軸のタイトル
    plt.ylabel('Feature')                             # y軸のタイトル
    plt.show()


def extract_days(x):  # 前走からの日数差から日数だけを抽出する関数
    if isinstance(x, str):
        return int(re.findall(r'(\d+)', x)[0])
    elif isinstance(x, pd.Timedelta):
        return int(x.days)
    else:
        return np.nan


def rank_str_change(x):  # 中止されたレースのRankを欠損値にする関数
    if x == '中':
        return np.nan


def prize_str_chage(x):  # なぜかこれを挟まないと整数型に変換できなかった
    if x == NaN:
        return pd.NA


def feature_importance(x_train, model):
    # 特徴量重要度の算出 (データフレームで取得)
    cols = list(x_train.columns)         # 特徴量名のリスト(目的変数CRIM以外)
    f_importance = np.array(model.feature_importance())  # 特徴量重要度の算出
    f_importance = f_importance / np.sum(f_importance)  # 正規化(必要ない場合はコメントアウト)
    df_importance = pd.DataFrame({'feature': cols, 'importance': f_importance})
    df_importance = df_importance.sort_values(
        'importance', ascending=False)  # 降順ソート
    display(df_importance)

    # 特徴量重要度の可視化
    plot_feature_importance(df_importance)


#def fukusho_preprocess(df):
#    df[['Fukusho_Min_Odds', 'Fukusho_Max_Odds']] = df['Fukusho_Odds'].str.split(' - ', expand=True).astype(float)    
#    df['Fukusho_Mean_Odds'] = df[['Fukusho_Min_Odds', 'Fukusho_Max_Odds']].mean(axis=1)
#    return df

# Function to calculate the internal division point
def calculate_internal_division(odds_str, ratio_lower=0.71, ratio_upper=0.29):
    if odds_str:
        lower, upper = map(float, odds_str.split(' - '))
        return lower * ratio_lower + upper * ratio_upper
    return None

def fukusho_preprocess(odds_list):
    odds_list = [calculate_internal_division(odds) for odds in odds_list]
    return odds_list

def label_encoding(df, save_label_encoder=False):
    """
    カテゴリカルな特徴量をラベルエンコーディングする
    空文字列や未知のラベルにも対応
    """
    # ラベルエンコード対象のカラムグループ
    cat_cols = ['Sex', 'Weather', 'Training', 'Horse_House']
    condition_cols = ['Condition', 'Condition1', 'Condition2', 'Condition3']
    place_cols = ['Place1', 'Place2', 'Place3']
    course_cols = ['Course', 'Course1', 'Course2', 'Course3']
    
    # 共通の前処理: 空文字列と欠損値を'missing'に置き換え
    for cols in [cat_cols, condition_cols, place_cols, course_cols]:
        for col in cols:
            if col in df.columns:
                df[col] = df[col].replace('', 'missing').fillna('missing')

    # エンコーダを新規作成して保存するモード
    if save_label_encoder:
        # 各列に対してラベルエンコーダを作成し、保存
        for col in cat_cols:
            if col in df.columns:
                le = LabelEncoder()
                le.fit(df[col])
                
                # ディレクトリが存在しない場合は作成
                import os
                os.makedirs('./label_encoder', exist_ok=True)
                
                # ラベルエンコーダを保存
                with open(f'./label_encoder/label_encoder_{col}.pkl', 'wb') as file:
                    pickle.dump(le, file)

        # Condition系の列に対して一つのラベルエンコーダを作成し、保存
        all_condition_values = []
        for col in condition_cols:
            if col in df.columns:
                all_condition_values.extend(df[col].values)
                
        if all_condition_values:  # リストが空でない場合のみ処理
            le_condition = LabelEncoder()
            le_condition.fit(all_condition_values)
            
            with open(f'./label_encoder/label_encoder_Condition.pkl', 'wb') as file:
                pickle.dump(le_condition, file)

        # Place系の列に対して一つのラベルエンコーダを作成し、保存
        all_place_values = []
        for col in place_cols:
            if col in df.columns:
                all_place_values.extend(df[col].values)
                
        if all_place_values:  # リストが空でない場合のみ処理
            le_place = LabelEncoder()
            le_place.fit(all_place_values)
            
            with open(f'./label_encoder/label_encoder_Place.pkl', 'wb') as file:
                pickle.dump(le_place, file)

        # Course系の列に対して一つのラベルエンコーダを作成し、保存
        all_course_values = []
        for col in course_cols:
            if col in df.columns:
                all_course_values.extend(df[col].values)
                
        if all_course_values:  # リストが空でない場合のみ処理
            le_course = LabelEncoder()
            le_course.fit(all_course_values)
            
            with open(f'./label_encoder/label_encoder_Course.pkl', 'wb') as file:
                pickle.dump(le_course, file)

    # 既存のエンコーダを使って変換するモード
    # 各列に対してラベルエンコーダを適用
    for col in cat_cols:
        if col in df.columns:
            try:
                with open(f'./label_encoder/label_encoder_{col}.pkl', 'rb') as file:
                    le = pickle.load(file)
                    
                # 未知のクラスがあるか確認
                unknown_classes = set(df[col].unique()) - set(le.classes_)
                if unknown_classes:
                    # 新しいクラスを追加
                    le.classes_ = np.append(le.classes_, list(unknown_classes))
                    
                # 変換を実行
                df[col] = le.transform(df[col])
            except FileNotFoundError:
                print(f"警告: {col}のエンコーダファイルが見つかりません。スキップします。")

    # Condition系の列に対してラベルエンコーダを適用
    try:
        with open(f'./label_encoder/label_encoder_Condition.pkl', 'rb') as file:
            le_condition = pickle.load(file)
            
        for col in condition_cols:
            if col in df.columns:
                # 未知のクラスがあるか確認
                unknown_classes = set(df[col].unique()) - set(le_condition.classes_)
                if unknown_classes:
                    # 新しいクラスを追加
                    le_condition.classes_ = np.append(le_condition.classes_, list(unknown_classes))
                
                # 変換を実行
                df[col] = le_condition.transform(df[col])
    except FileNotFoundError:
        print("警告: Conditionエンコーダファイルが見つかりません。スキップします。")

    # Place系の列に対してラベルエンコーダを適用
    try:
        with open(f'./label_encoder/label_encoder_Place.pkl', 'rb') as file:
            le_place = pickle.load(file)
            
        for col in place_cols:
            if col in df.columns:
                # 未知のクラスがあるか確認
                unknown_classes = set(df[col].unique()) - set(le_place.classes_)
                if unknown_classes:
                    # 新しいクラスを追加
                    le_place.classes_ = np.append(le_place.classes_, list(unknown_classes))
                
                # 変換を実行
                df[col] = le_place.transform(df[col])
    except FileNotFoundError:
        print("警告: Placeエンコーダファイルが見つかりません。スキップします。")

    # Course系の列に対してラベルエンコーダを適用
    try:
        with open(f'./label_encoder/label_encoder_Course.pkl', 'rb') as file:
            le_course = pickle.load(file)
            
        for col in course_cols:
            if col in df.columns:
                # 未知のクラスがあるか確認
                unknown_classes = set(df[col].unique()) - set(le_course.classes_)
                if unknown_classes:
                    # 新しいクラスを追加
                    le_course.classes_ = np.append(le_course.classes_, list(unknown_classes))
                
                # 変換を実行
                df[col] = le_course.transform(df[col])
    except FileNotFoundError:
        print("警告: Courseエンコーダファイルが見つかりません。スキップします。")
    
    return df

def preprocess(df, save_label_encoder=False):
    #global df

    print('Start preprocess.')

    # データの読み込み
    # with codecs.open('my_data.csv', 'r', 'Shift-JIS', 'ignore') as file:
    #    df = pd.read_table(file, delimiter=',', index_col=0)

    # 複勝払い戻し列の作成
    if df['Fukusho'].dtype == 'object':  # Pandasでは文字列型は通常 'object' として扱われます
        df_temp = df['Fukusho'].str.split('円', expand=True)
        df["Fukusho1"] = df_temp[0].str.replace(",","").replace("", 0).astype(int)
        df["Fukusho2"] = df_temp[1].str.replace(",","").replace("", 0).astype(int)
        df["Fukusho3"] = df_temp[2].str.replace(",","").replace("", 0).astype(int)

    # 使うデータの選別
    df = df.drop(columns=['Waku', 'Jockey',
                         'Ninki', 'Right_Left', 'Day1', 'Day2', 'Day3', 'Tansho', 
                         'Fukusho', 'Umaren', 'Wide', 'Umatan', 'Fuku3', 'Tan3', 'MothersFather_Time_Index', 'Horse_Name'])
    df = df[df['Course'] != '障']
    # "Fukusho"列の値を分割して新しい列に割り当てる
    # 型の成型
    df['Elapsed_Day'] = df['Elapsed_Day'].apply(extract_days)

    # label encoding
    #label_encoder = LabelEncoder()
    #df["Horse_Name"]=label_encoder.fit_transform(df['Horse_Name'])

    df['Rank1'] = pd.to_numeric(df['Rank1'], errors='coerce')
    df['Rank2'] = pd.to_numeric(df['Rank2'], errors='coerce')
    df['Rank3'] = pd.to_numeric(df['Rank3'], errors='coerce')
    
    df['Condition_Index1'] = pd.to_numeric(df['Condition_Index1'], errors='coerce')
    df['Condition_Index2'] = pd.to_numeric(df['Condition_Index2'], errors='coerce')
    df['Condition_Index3'] = pd.to_numeric(df['Condition_Index3'], errors='coerce')

    
    df['Time_Index1'] = pd.to_numeric(df['Time_Index1'], errors='coerce')
    df['Time_Index2'] = pd.to_numeric(df['Time_Index2'], errors='coerce')
    df['Time_Index3'] = pd.to_numeric(df['Time_Index3'], errors='coerce')
    df['Father_Time_Index'] = pd.to_numeric(df['Father_Time_Index'], errors='coerce')
    df['Mother_Time_Index'] = pd.to_numeric(df['Mother_Time_Index'], errors='coerce')
    #df['MothersFather_Time_Index'] = pd.to_numeric(df['MothersFather_Time_Index'], errors='coerce')

    df['Jockey_Weight'] = pd.to_numeric(df['Jockey_Weight'], errors='coerce')
    df['Jockey_Prize'] = pd.to_numeric(df['Jockey_Prize'], errors='coerce')

    df.fillna({'Prize1': 0, 'Prize2': 0, 'Prize3': 0}, inplace=True)
    df['Prize1'] = df['Prize1'].apply(lambda x: str(x).replace(',', '')).apply(lambda x: pd.to_numeric(x, errors='coerce'))
    df['Prize2'] = df['Prize2'].apply(lambda x: str(x).replace(',', '')).apply(lambda x: pd.to_numeric(x, errors='coerce'))
    df['Prize3'] = df['Prize3'].apply(lambda x: str(x).replace(',', '')).apply(lambda x: pd.to_numeric(x, errors='coerce'))


        
    df=label_encoding(df, save_label_encoder)
    

    # le = LabelEncoder()
    # for cat in cat_cols:
    #     df[cat].fillna('missing', inplace=True)
    #     #encoded_data = le.fit_transform(df[cat])
    #     encoded_data = loaded_label_encoder.transform(df[cat])
    #     df[cat] = encoded_data


    # 数値に変換する必要がある列を選択して変換
    numerical_columns = ['Race_ID', 'Year', 'Month', 'Date', 'Race_Count', 'Day', 'Race_Num', 'Prize', 'Horse_Num', 'Age', 'Distanse', 'Elapsed_Day', 'Race_Num1', 'Race_Num2', 'Race_Num3', 'Horse_Num1', 'Horse_Num2', 'Horse_Num3', 'Distanse1', 'Distanse2', 'Distanse3', 'Last3F1', 'Last3F2', 'Last3F3']
    for col in numerical_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 目的変数の作成
    df.loc[(0 < df['Rank']) & (df['Rank'] < 4), 'Rank_group'] = 0
    df.loc[(3 < df['Rank']) & (df['Rank'] < 9), 'Rank_group'] = 1
    df.loc[8 < df['Rank'], 'Rank_group'] = 2

    # print(df)
    # print(df['Condition_Index1'].dtype)

    print('End preprocess')
    # print(df.head())
    # df.to_csv('preprocessed_data.csv')
    return df


def no_training_preprocess(df):
    #global df

    print('Start preprocess.')

    # データの読み込み
    # with codecs.open('my_data.csv', 'r', 'Shift-JIS', 'ignore') as file:
    #    df = pd.read_table(file, delimiter=',', index_col=0)

    # 使うデータの選別
    df = df.drop(columns=['Waku', 'Horse_Name', 'Jockey',
                          'Ninki', 'Right_Left', 'Day1', 'Day2', 'Day3',])
    df = df[df['Course'] != '障']

    # 型の成型
    df['Elapsed_Day'] = df['Elapsed_Day'].apply(extract_days)

    Rank_RM_Dict = {'中': np.nan, '取': np.nan,  '失': np.nan, '除': np.nan,
                    '1(降)': np.nan, '2(降)': np.nan, '3(降)': np.nan, '4(降)': np.nan,
                    '5(降)': np.nan, '6(降)': np.nan, '7(降)': np.nan, '8(降)': np.nan,
                    '9(降)': np.nan, '10(降)': np.nan, '11(降)': np.nan, '12(降)': np.nan,
                    '13(降)': np.nan, '14(降)': np.nan, '15(降)': np.nan, '16(降)': np.nan,
                    '17(降)': np.nan, '18(降)': np.nan,
                    }
    Jockey_Weight_Dict = {'未定': np.nan}
    Index_Dict = {',': '', '**': np.nan}

    df['Rank1'] = df['Rank1'].replace(Rank_RM_Dict)
    df['Rank1'] = df['Rank1'].astype(float)
    df['Rank2'] = df['Rank2'].replace(Rank_RM_Dict)
    df['Rank2'] = df['Rank2'].astype(float)
    df['Rank3'] = df['Rank3'].replace(Rank_RM_Dict)
    df['Rank3'] = df['Rank3'].astype(float)

    df['Condition_Index1'] = df['Condition_Index1'].replace(Index_Dict)
    df['Condition_Index1'] = df['Condition_Index1'].astype(float)
    df['Condition_Index2'] = df['Condition_Index2'].replace(Index_Dict)
    df['Condition_Index2'] = df['Condition_Index2'].astype(float)
    df['Condition_Index3'] = df['Condition_Index3'].replace(Index_Dict)
    df['Condition_Index3'] = df['Condition_Index3'].astype(float)

    df['Time_Index3'] = df['Time_Index3'].replace(Index_Dict)
    df['Time_Index3'] = df['Time_Index3'].astype(float)
    df['Time_Index2'] = df['Time_Index2'].replace(Index_Dict)
    df['Time_Index2'] = df['Time_Index2'].astype(float)
    df['Time_Index1'] = df['Time_Index1'].replace(Index_Dict)
    df['Time_Index1'] = df['Time_Index1'].astype(float)
    df['Jockey_Weight'] = df['Jockey_Weight'].replace(Jockey_Weight_Dict)
    df['Jockey_Weight'] = df['Jockey_Weight'].astype(float)

    #df['Prize1'] = df['Prize1'].apply(prize_str_chage)
    #df['Prize2'] = df['Prize2'].apply(prize_str_chage)
    #df['Prize3'] = df['Prize3'].apply(prize_str_chage)
    df.fillna({'Prize1': 0, 'Prize2': 0, 'Prize3': 0}, inplace=True)
    df['Prize1'] = df['Prize1'].apply(
        lambda x: str(x).replace(',', '')).astype(np.float)
    df['Prize2'] = df['Prize2'].apply(
        lambda x: str(x).replace(',', '')).astype(np.float)
    df['Prize3'] = df['Prize3'].apply(
        lambda x: str(x).replace(',', '')).astype(np.float)
    # df['Condition_Index1'] = df['Condition_Index1'].apply(
    #    lambda x: str(x).replace(Index_Dict)).astype(np.float)

    # ラベルエンコード
    cat_cols = ['Sex', 'Course', 'Weather', 'Condition', 'Place1',
                'Place2', 'Place3', 'Course1', 'Course2', 'Course3', 'Condition1', 'Condition2', 'Condition3', ]
    le = LabelEncoder()

    for cat in cat_cols:
        df[cat].fillna('missing', inplace=True)
        encoded_data = le.fit_transform(df[cat])
        df[cat] = encoded_data

    # 目的変数の作成
    df.loc[(0 < df['Rank']) & (df['Rank'] < 4), 'Rank_group'] = 0
    df.loc[(3 < df['Rank']) & (df['Rank'] < 9), 'Rank_group'] = 1
    df.loc[8 < df['Rank'], 'Rank_group'] = 2

    # print(df)
    # print(df['Condition_Index1'].dtype)

    print('End preprocess')
    # print(df.head())
    # df.to_csv('preprocessed_data.csv')
    return df


def not_run_preprocess(df):
    #global df

    print('Start preprocess.')

    # データの読み込み
    # with codecs.open('my_data.csv', 'r', 'Shift-JIS', 'ignore') as file:
    #    df = pd.read_table(file, delimiter=',', index_col=0)

    # 使うデータの選別
    df = df.drop(columns=['Waku', 'Jockey',
                          'Ninki', 'Right_Left', 'Day1', 'Day2', 'Day3', 'MothersFather_Time_Index'])
    df = df[df['Course'] != '障']

    # 型の成型
    df['Elapsed_Day'] = df['Elapsed_Day'].apply(extract_days)

    Rank_RM_Dict = {'中': np.nan, '取': np.nan,  '失': np.nan, '除': np.nan,
                    '1(降)': np.nan, '2(降)': np.nan, '3(降)': np.nan, '4(降)': np.nan,
                    '5(降)': np.nan, '6(降)': np.nan, '7(降)': np.nan, '8(降)': np.nan,
                    '9(降)': np.nan, '10(降)': np.nan, '11(降)': np.nan, '12(降)': np.nan,
                    '13(降)': np.nan, '14(降)': np.nan, '15(降)': np.nan, '16(降)': np.nan,
                    '17(降)': np.nan, '18(降)': np.nan,
                    }
    Jockey_Weight_Dict = {'未定': np.nan}
    Index_Dict = {',': '', '**': np.nan}

    df['Rank1'] = pd.to_numeric(df['Rank1'], errors='coerce')
    df['Rank2'] = pd.to_numeric(df['Rank2'], errors='coerce')
    df['Rank3'] = pd.to_numeric(df['Rank3'], errors='coerce')

    df['Condition_Index1'] = pd.to_numeric(df['Condition_Index1'], errors='coerce')
    df['Condition_Index2'] = pd.to_numeric(df['Condition_Index2'], errors='coerce')
    df['Condition_Index3'] = pd.to_numeric(df['Condition_Index3'], errors='coerce')

    df['Time_Index1'] = pd.to_numeric(df['Time_Index1'], errors='coerce')
    df['Time_Index2'] = pd.to_numeric(df['Time_Index2'], errors='coerce')
    df['Time_Index3'] = pd.to_numeric(df['Time_Index3'], errors='coerce')
    df['Father_Time_Index'] = pd.to_numeric(df['Father_Time_Index'], errors='coerce')
    df['Mother_Time_Index'] = pd.to_numeric(df['Mother_Time_Index'], errors='coerce')
    
    df['Jockey_Weight'] = pd.to_numeric(df['Jockey_Weight'], errors='coerce')
    df['Jockey_Prize'] = pd.to_numeric(df['Jockey_Prize'], errors='coerce')

    df.fillna({'Prize1': 0, 'Prize2': 0, 'Prize3': 0}, inplace=True)
    df['Prize1'] = df['Prize1'].apply(lambda x: str(x).replace(',', '')).apply(lambda x: pd.to_numeric(x, errors='coerce'))
    df['Prize2'] = df['Prize2'].apply(lambda x: str(x).replace(',', '')).apply(lambda x: pd.to_numeric(x, errors='coerce'))
    df['Prize3'] = df['Prize3'].apply(lambda x: str(x).replace(',', '')).apply(lambda x: pd.to_numeric(x, errors='coerce'))


    # ラベルエンコード
    cat_cols = ['Sex', 'Course', 'Weather', 'Condition', 'Place1',
                'Place2', 'Place3', 'Course1', 'Course2', 'Course3', 
                'Condition1', 'Condition2', 'Condition3', 'Training',
                'Horse_House', 'Horse_Name']
    le = LabelEncoder()

    for cat in cat_cols:
        df[cat].fillna('missing', inplace=True)
        encoded_data = le.fit_transform(df[cat])
        df[cat] = encoded_data

    # 目的変数の作成
    df.loc[(0 < df['Rank']) & (df['Rank'] < 4), 'Rank_group'] = 0
    df.loc[(3 < df['Rank']) & (df['Rank'] < 9), 'Rank_group'] = 1
    df.loc[8 < df['Rank'], 'Rank_group'] = 2

    # print(df)
    # print(df['Condition_Index1'].dtype)

    print('End preprocess')
    # print(df.head())
    # df.to_csv('preprocessed_data.csv')
    return df


def not_run_no_training_preprocess(df):
    #global df

    print('Start preprocess.')

    # データの読み込み
    # with codecs.open('my_data.csv', 'r', 'Shift-JIS', 'ignore') as file:
    #    df = pd.read_table(file, delimiter=',', index_col=0)

    # 使うデータの選別
    df = df.drop(columns=['Waku', 'Horse_Name', 'Jockey',
                          'Ninki', 'Right_Left', 'Day1', 'Day2', 'Day3', 'Training', ])
    df = df[df['Course'] != '障']

    # 型の成型
    df['Elapsed_Day'] = df['Elapsed_Day'].apply(extract_days)

    Rank_RM_Dict = {'中': np.nan, '取': np.nan,  '失': np.nan, '除': np.nan,
                    '1(降)': np.nan, '2(降)': np.nan, '3(降)': np.nan, '4(降)': np.nan,
                    '5(降)': np.nan, '6(降)': np.nan, '7(降)': np.nan, '8(降)': np.nan,
                    '9(降)': np.nan, '10(降)': np.nan, '11(降)': np.nan, '12(降)': np.nan,
                    '13(降)': np.nan, '14(降)': np.nan, '15(降)': np.nan, '16(降)': np.nan,
                    '17(降)': np.nan, '18(降)': np.nan,
                    }
    Jockey_Weight_Dict = {'未定': np.nan}
    Index_Dict = {',': '', '**': np.nan}

    #df['Rank1'] = df['Rank1'].replace(Rank_RM_Dict)
    df['Rank1'] = df['Rank1'].astype(float)
    #df['Rank2'] = df['Rank2'].replace(Rank_RM_Dict)
    df['Rank2'] = df['Rank2'].astype(float)
    #df['Rank3'] = df['Rank3'].replace(Rank_RM_Dict)
    df['Rank3'] = df['Rank3'].astype(float)

    #df['Condition_Index1'] = df['Condition_Index1'].replace(Index_Dict)
    df['Condition_Index1'] = df['Condition_Index1'].astype(float)
    #df['Condition_Index2'] = df['Condition_Index2'].replace(Index_Dict)
    df['Condition_Index2'] = df['Condition_Index2'].astype(float)
    #df['Condition_Index3'] = df['Condition_Index3'].replace(Index_Dict)
    df['Condition_Index3'] = df['Condition_Index3'].astype(float)

    #df['Time_Index3'] = df['Time_Index3'].replace(Index_Dict)
    df['Time_Index3'] = df['Time_Index3'].astype(float)
    #df['Time_Index2'] = df['Time_Index2'].replace(Index_Dict)
    df['Time_Index2'] = df['Time_Index2'].astype(float)
    #df['Time_Index1'] = df['Time_Index1'].replace(Index_Dict)
    df['Time_Index1'] = df['Time_Index1'].astype(float)
    #df['Jockey_Weight'] = df['Jockey_Weight'].replace(Jockey_Weight_Dict)
    df['Jockey_Weight'] = df['Jockey_Weight'].astype(float)

    #df['Prize1'] = df['Prize1'].apply(prize_str_chage)
    #df['Prize2'] = df['Prize2'].apply(prize_str_chage)
    #df['Prize3'] = df['Prize3'].apply(prize_str_chage)
    df.fillna({'Prize1': 0, 'Prize2': 0, 'Prize3': 0}, inplace=True)
    df['Prize1'] = df['Prize1'].apply(
        lambda x: str(x).replace(',', '')).astype(np.float)
    df['Prize2'] = df['Prize2'].apply(
        lambda x: str(x).replace(',', '')).astype(np.float)
    df['Prize3'] = df['Prize3'].apply(
        lambda x: str(x).replace(',', '')).astype(np.float)
    # df['Condition_Index1'] = df['Condition_Index1'].apply(
    #    lambda x: str(x).replace(Index_Dict)).astype(np.float)

    # ラベルエンコード
    cat_cols = ['Sex', 'Course', 'Weather', 'Condition', 'Place1',
                'Place2', 'Place3', 'Course1', 'Course2', 'Course3', 'Condition1', 'Condition2', 'Condition3', ]
    le = LabelEncoder()

    for cat in cat_cols:
        df[cat].fillna('missing', inplace=True)
        encoded_data = le.fit_transform(df[cat])
        df[cat] = encoded_data

    # 目的変数の作成
    df.loc[(0 < df['Rank']) & (df['Rank'] < 4), 'Rank_group'] = 0
    df.loc[(3 < df['Rank']) & (df['Rank'] < 9), 'Rank_group'] = 1
    df.loc[8 < df['Rank'], 'Rank_group'] = 2

    # print(df)
    # print(df['Condition_Index1'].dtype)

    print('End preprocess')
    # print(df.head())
    # df.to_csv('preprocessed_data.csv')
    return df
