import re
import time
from urllib.request import urlopen

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
#from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
import pandas as pd
from retry.retry_decorator import retry
from notify import send_slack_notify
from logging_setup import get_logger

logger = get_logger("Keiba")


@retry
def scrape_race_id_and_time_list(kaisai_date: str):
    logger.info("Start scrape_race_id_and_time_list")
    options = Options()
    options.add_argument("--headless")
    options.add_argument('log-level=3')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--remote-debugging-port=9222')
    
    race_id_list = []
    race_time_list = []
    

    driver = webdriver.Chrome(options=options)
    
    url = f"https://race.netkeiba.com/top/race_list.html?kaisai_date={kaisai_date}"
    try:
        driver.get(url)
        time.sleep(1)
        li_list = driver.find_elements(By.CLASS_NAME, "RaceList_DataItem")

        for li in li_list:
            href = li.find_element(By.TAG_NAME, "a").get_attribute("href")
            race_id = re.findall(r"race_id=(\d{12})", href)[0]
            
            # Get race time
            time_element = li.find_element(By.CLASS_NAME, "RaceList_Itemtime")
            race_time = time_element.text.strip()
            
            # Append race id and time
            race_id_list.append(race_id)
            race_time_list.append(race_time)
    
            
    except Exception as e:
        print(f"Stopped at {url} due to {e}")
        logger.info(f"Stopped at {url} due to {e}")
        
    finally:
        # ブラウザを閉じる
        driver.quit()
    #print("race_id_list, race_time_list")
    #send_slack_notify(race_id_list, race_time_list)
    logger.info("End scrape_race_id_and_time_list")
    return race_id_list, race_time_list


def fetch_race_info():
    logger.info("Start fetch_race_info")
    now = datetime.now()
    kaisai_date = now.strftime("%Y%m%d")
    #kaisai_date="20241006"

    race_id_list, race_time_list = scrape_race_id_and_time_list(kaisai_date)

    race_info_df = pd.DataFrame({
        "race_id": race_id_list,
        "race_time": race_time_list,
    })

    logger.info(f"race_info_df: {race_info_df}")
    
    
    # 'race_time'列をdatetimeオブジェクトに変換
    race_info_df['race_time'] = pd.to_datetime(race_info_df['race_time'], format='%H:%M').dt.time

    # 'race_time'列を基準にソート
    race_info_df = race_info_df.sort_values('race_time').reset_index(drop=True)
    print(race_info_df)
    logger.info(f"race_info_df: {race_info_df}")
    
    # 現在時刻を取得し、5分を追加
    now = (datetime.now() + timedelta(minutes=5)).time()
    
    # 'race_time'列が現在時刻の5分後より後の行だけを残す
    race_info_df = race_info_df[race_info_df['race_time'] > now].reset_index(drop=True)

    logger.info("End fetch_race_info")

    return race_info_df

