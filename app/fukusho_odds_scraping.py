from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from sklearn.model_selection import train_test_split
from sklearn.model_selection import KFold
from numpy.core.numeric import NaN
import pandas as pd
import codecs
from sklearn.preprocessing import LabelEncoder
import re
import numpy as np
import lightgbm as lgb
# import optuna.integration.lightgbm as lgb
import matplotlib.pyplot as plt
import time
import os
from retry.retry_decorator import fukusho_retry
from notify import send_slack_notify





@fukusho_retry
def fetch_odds(race_id):
    send_slack_notify("オッズ取得を開始します。")


    # ブラウザのオプションを設定
    options = Options()
    options.add_argument('--headless')   
    options.add_argument('log-level=3')
    options.page_load_strategy = 'none'  # 'normal', 'eager', 'none'
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--remote-debugging-port=9222')

    # WebDriverを起動
    driver = webdriver.Chrome(options=options)

    try:
        # Webページにアクセス
        driver.get(f'https://race.netkeiba.com/odds/index.html?type=b1&race_id={race_id}&rf=shutuba_submenu')

        # 要素が表示されるまで最大10秒間待機
        # RaceOdds_HorseList_Tableクラスを持つテーブルタグの2番目のテーブルを選択
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".RaceOdds_HorseList_Table"))
        )[1]  # 2番目のテーブルを指定

        # 2番目のテーブル内のクラスOddsのspanタグをすべて取得
        elements = table.find_elements(By.CSS_SELECTOR, "td.Odds")
        
        # 要素のテキストを取得
        odds_list=[element.text for element in elements]
        return odds_list
    finally:
        # ブラウザを閉じる
        driver.quit()
        send_slack_notify("オッズ取得が完了しました。")
    


    

        

    
