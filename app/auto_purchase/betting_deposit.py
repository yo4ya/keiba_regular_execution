import sys
sys.path.append('../')
from .modules import purchase
from notify import send_slack_notify
from retry.retry_decorator import retry
import os

# プロジェクトのルートディレクトリをパスに追加
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_dir)
from logging_setup import get_logger
logger = get_logger("Keiba")

@retry
def deposit():
    send_slack_notify("入金を開始します。")
    logger.info("入金を開始します。")
    tickets_purchaser = purchase.TicketsPurchaser()
    tickets_purchaser.deposit()
    send_slack_notify("入金が完了しました。")
    logger.info("入金が完了しました。")