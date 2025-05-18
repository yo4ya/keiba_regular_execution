import schedule
import time
import pandas as pd
import traceback
from notify import send_slack_notify
from scraping import scraping
from predicting import predicting
from preprocess import fukusho_preprocess
from fukusho_odds_scraping import fetch_odds
from judging import determine_whether_purchase_ticket
from auto_purchase.betting import betting
from retry.retry_decorator import retry
from logging_setup import get_logger

logger = get_logger("Keiba")


def job(running_time, Race_ID):
    try:
        logger.info(f"Job started for Race_ID: {Race_ID} at running_time: {running_time}")
        race_df = scraping(Race_ID)
        logger.info(f"race_df fetched: {race_df}")
        
        if race_df is None: 
            logger.info(f"Race_ID: {Race_ID} is not a target race. Skipping.")
            send_slack_notify("予測対象外のレースのためスキップします。")
            return schedule.CancelJob  # ジョブの実行後にこのスケジュールをキャンセル
        
        df_pred, pred_summary = predicting(Race_ID, race_df, running_time)
        logger.info(f"Prediction completed for Race_ID: {Race_ID}")

        odds_list=fetch_odds(Race_ID)
        logger.info(f"Odds fetched: {odds_list}")
        odds_list=fukusho_preprocess(odds_list)
        logger.info(f"Odds fetched and preprocessed for Race_ID: {Race_ID}, and odds_list: {odds_list}")

        purchase_list=determine_whether_purchase_ticket(df_pred, odds_list)
        if purchase_list:
            logger.info(f"Purchase list determined for Race_ID: {Race_ID}: {purchase_list}")
            message = f"購入馬券: {purchase_list}\n出走時間: {running_time}\nレースID: {Race_ID}"
            send_slack_notify(message, purchase_flag=True)
            betting(Race_ID, purchase_list)
        else:
            logger.info(f"No purchase tickets for Race_ID: {Race_ID}")
            print(Race_ID, "では購入馬券はありません。")
            send_slack_notify(str(Race_ID) + "では購入馬券はありません。")

        return schedule.CancelJob  # ジョブの実行後にこのスケジュールをキャンセル
    
    except Exception as e:
        logger.info(f"Error occurred in job for Race_ID: {Race_ID}: {e}")
        send_slack_notify("job中にエラーが発生しました。")
        send_slack_notify(e)
        traceback.print_exc()
        return schedule.CancelJob  # ジョブの実行後にこのスケジュールをキャンセル

def scheduler(Race_ID_list, pred_time_list, running_time_list):
    # 各時刻にジョブをスケジュールする
    for index, pred_time in enumerate(pred_time_list):
        pred_time_str = pred_time.strftime('%H:%M')
        Race_ID = Race_ID_list[index]
        running_time = running_time_list[index]
        logger.info(f"Scheduling job for Race_ID: {Race_ID} at {pred_time_str}")
        schedule.every().day.at(pred_time_str).do(job, running_time=running_time, Race_ID=Race_ID)

    # 無限ループでスケジュールを維持
    while True:
        schedule.run_pending()
        time.sleep(1)
        if not schedule.jobs:  # スケジュールされたジョブがなくなったら終了
            logger.info("No more scheduled jobs. Exiting scheduler.")
            send_slack_notify("スケジュールされたジョブがなくなりました。スケジューラを終了します。")
            break

if __name__ == "__main__":
    # job(None, "202506030502")
    betting("202505020812", [9])