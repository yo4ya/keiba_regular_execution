import requests
import pandas as pd
import json
import traceback

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

def main():
    send_slack_notify('kuya')

def send_slack_notify(notification_message):
    """
    LINEに通知する
    """
    #line_notify_token = 'cOXPn2XWNh4Ni68N1gNOYMlHeuDPA32a4MBdVLZG39S' #グループ用
    line_notify_token = 'YPqrppoqg91I0FI53khUzvOtzxAKRCc5SvRVx8tKT8W' #個人用
    line_notify_api = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {line_notify_token}'}
    data = {'message': f'message: \n\n{notification_message}'}
    requests.post(line_notify_api, headers = headers, data = data)
    
def send_slack_notify(notification_message, webhook_url=None, purchase_flag=False):
    """
    Slackに通知する
    
    Args:
        notification_message (any): 送信するメッセージ（文字列、DataFrame、例外オブジェクトなど）
        webhook_url (str, optional): SlackのWebhook URL。指定がない場合はデフォルト値を使用。
        purchase_flag (bool, optional): Trueの場合、購入用のWebhook URLにメッセージを送信する。デフォルトはFalse。
    """
    if webhook_url is None:
        if purchase_flag:
            # 購入用のWebhook URL
            webhook_url = 'https://hooks.slack.com/services/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'
        else:
            # 通常のWebhook URL
            webhook_url = 'https://hooks.slack.com/services/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'
    
    # メッセージの種類に応じた処理
    if isinstance(notification_message, pd.DataFrame):
        # DataFrameの場合はコードブロックで囲んだ文字列に変換
        text_message = f"```\n{notification_message.to_string()}\n```"
    elif isinstance(notification_message, Exception):
        # 例外オブジェクトの場合は文字列に変換
        text_message = f"エラー: {str(notification_message)}"
    else:
        # それ以外は単純に文字列に変換
        text_message = str(notification_message)
    
    payload = {
        'text': text_message
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code != 200:
            print(f'Slack通知の送信に失敗しました: {response.status_code}, {response.text}')
        return response
    except Exception as e:
        print(f'Slack通知の送信中にエラーが発生しました: {e}')
        return None

# if __name__ == "__main__":
#     app.run(host='0.0.0.0', port=8080)
    
#     main()