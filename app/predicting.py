import sys
#sys.path.append(r'G:\マイドライブ\keiba')
from preprocess import preprocess
from notify import send_slack_notify
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
from retry.retry_decorator import retry
from logging_setup import get_logger

logger = get_logger("Keiba")

warnings.filterwarnings('ignore')




@retry
def predicting(Race_ID, race_df, running_time):
    send_slack_notify("予測を開始します。")
    logger.info("予測を開始します。")
    
    df=race_df

    df['Place']=int(Race_ID[4:6])
    model = pickle.load(open(r'./model/model_through_2023.pkl', 'rb'))
    logger.info("モデルを読み込みました。")


    df_origin = df
    test_set = preprocess(df)
    test_set['Horse_name_origin']=df_origin['Horse_Name']

    test_set=test_set.reset_index(drop=True)
    x_test = test_set.drop(columns=['Rank_group', 'Rank', 'Odds', 'Horse_name_origin'])

    if x_test['Rank1'].isnull().sum() > len(x_test['Rank1'])/2:
        return None, None
    x_test.to_csv("x_test.csv")
    y_pred_prob = model.predict(x_test)
    df_pred=pd.DataFrame({
        'horse_num': test_set['Horse_Num'].values,
        'pred': y_pred_prob[:, 0],
        'horse_name': test_set['Horse_name_origin'].values
    })
    #df_pred['horse_num']=df_pred.index+1
    
    df_pred_sorted = df_pred.sort_values(by='pred', ascending=False)
    df_pred_sorted['pred'] = df_pred_sorted['pred'].round(3)
    
    pred_summary = str(Race_ID)+"\n"
    pred_summary += "出走時刻: "+str(running_time)+"\n"+"\n"
    pred_summary+=df_pred_sorted.to_string(index=False, columns=['horse_num', 'pred', 'horse_name'])
    send_slack_notify(pred_summary)
    logger.info(f"予測が完了しました。{pred_summary}")
    

        
    return df_pred, pred_summary

# if __name__ == '__main__':
#     predicting()
    