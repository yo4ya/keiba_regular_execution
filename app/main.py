from scheduler import scheduler
from scheduler import job
from scraping import scraping
from predicting import predicting
from fukusho_odds_scraping import fetch_odds
from fetching_race_id_time import fetch_race_info
from notify import send_slack_notify
from auto_purchase.betting_deposit import deposit
from datetime import datetime, timedelta
import traceback
from flask import Flask
from logging_setup import get_logger

logger = get_logger("Keiba")  # ジョブ名やモジュール名を指定するとよい
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hell, World!'

@app.route('/health')
def health_check():
    return 'OK', 200

def set_pred_time_list(race_time_list):
    logger.info("Start set_pred_time_list")
    pred_time_list = []
    for race_time in race_time_list:
        # Convert time object to datetime object
        now = datetime.now()
        time_obj = datetime.combine(now, race_time)
        
        # Subtract timedelta
        new_time_obj = time_obj - timedelta(minutes=10)
        
        # Convert back to time object and append to list
        pred_time_list.append(new_time_obj.time())
    print(pred_time_list)
    logger.info("End set_pred_time_list")
    return pred_time_list

#@app.route('/main')
def main():
    
    logger.info("スクリプトが起動しました。")
    
    logger.info(f"test{[1, 2, 3]}")

    send_slack_notify("スクリプトが起動しました。")
    try:
        race_info_df=fetch_race_info()
        logger.info(f"race_info_df: {race_info_df}")
        
        Race_ID_list=race_info_df['race_id']
        logger.info(f"Race_ID_list: {Race_ID_list}")

        race_time_list=race_info_df['race_time']
        logger.info(f"race_time_list: {race_time_list}")

        pred_time_list=set_pred_time_list(race_time_list)
        logger.info(f"pred_time_list: {pred_time_list}")
        
        deposit()
        scheduler(Race_ID_list, pred_time_list, race_time_list)
        
        # for testing
        #job("15:35:00", "202405040810")
        
    except Exception as e:
        send_slack_notify("main中にエラーが発生しました。")
        send_slack_notify(e)
        logger.info(f"main中にエラーが発生しました。: {e}")
        logger.info(traceback.format_exc())
        traceback.print_exc()
    
    finally:
        send_slack_notify("スクリプトの全ての処理が終了しました。")
        logger.info("スクリプトの全ての処理が終了しました。")
        
if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=8080)
    main()