from notify import send_slack_notify

def determine_whether_purchase_ticket(df_pred, odds_list):
    odds_dict = {i + 1: odds_list[i] for i in range(len(odds_list))}  # Create a dictionary with horse_num as key
    df_pred['odds'] = df_pred['horse_num'].map(odds_dict)  # Map the odds to the correct horse_num

    # Now drop rows where 'odds' is None, as these correspond to missing horse numbers in odds_list
    df_summary = df_pred.dropna(subset=['odds'])
    print(df_summary)
    # DataFrameを文字列に変換
    df_str = df_summary.to_string()
    send_slack_notify(f"予測結果:\n```\n{df_str}\n```")

    condition_1 = (df_summary['pred'] >= 0.7) & (df_summary['odds'] >= 2) & (df_summary['odds'] < 3)
    condition_2 = (df_summary['pred'] >= 0.6) & (df_summary['odds'] >= 3) & (df_summary['odds'] < 5)
    condition_3 = (df_summary['pred'] >= 0.5) & (df_summary['odds'] >= 5) & (df_summary['odds'] < 9)
    condition_4 = (df_summary['pred'] >= 0.4) & (df_summary['odds'] >= 9)
    
    purchase_list = df_summary[(condition_1 | condition_2 | condition_3 | condition_4)]['horse_num'].tolist()
    
    print(purchase_list)
    return purchase_list