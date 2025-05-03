import sys
sys.path.append('../')
from notify import send_slack_notify
from .modules import purchase
import datetime
from retry.retry_decorator import retry
import os

# プロジェクトのルートディレクトリをパスに追加
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_dir)
from logging_setup import get_logger
logger = get_logger("Keiba")


# 予測

@retry
def betting(Race_ID, purchase_list):
    send_slack_notify("馬券購入を開始します。")
    logger.info("馬券購入を開始します。")
    bet_list=[{'bet_type' : 'fukusho', 'race_id': str(Race_ID), 'horse_number' : purchase_list}]
    print(bet_list)
    tickets_purchaser = purchase.TicketsPurchaser()

    tickets_purchaser.buy_jra_pat(
        bet_list, 
        datetime.date.today()
    )
    send_slack_notify("馬券購入が完了しました。")
    logger.info("馬券購入が完了しました。")
    send_slack_notify("レース中継はこちらから:"+"\n"+"https://jra.jp/keiba/")

