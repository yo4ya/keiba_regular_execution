from notify import send_slack_notify

def test_send_slack_notify():
    # 通常のWebhook URLへの送信をテスト
    print("通常メッセージ送信テスト")
    response1 = send_slack_notify("これは通常のテストメッセージです", purchase_flag=False)
    print(f"レスポンス: {response1.status_code}, {response1.text}\n")
    
    # 購入用Webhook URLへの送信をテスト
    print("購入メッセージ送信テスト")
    response2 = send_slack_notify("これは購入用のテストメッセージです", purchase_flag=True)
    print(f"レスポンス: {response2.status_code}, {response2.text}")

if __name__ == "__main__":
    test_send_slack_notify()