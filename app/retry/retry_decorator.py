import time
import traceback
import os
import sys

# プロジェクトのルートディレクトリをパスに追加
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_dir)
from logging_setup import get_logger
logger = get_logger("Keiba")


def retry(func, max_attempts=3):
    """
    指定された関数をリトライするデコレータ。最大リトライ回数に達するまで、または成功するまで関数を呼び出します。
    
    Args:
        func: リトライする関数
        max_attempts: 最大リトライ回数 (デフォルトは3)
        
    Returns:
        関数の実行結果、または全てのリトライが失敗した場合はNone
    """
    def wrapper(*args, **kwargs):
        attempts = 0
        while attempts < max_attempts:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"エラーが発生しました: {e}. リトライ中... ({attempts+1}/{max_attempts})")
                print(traceback.format_exc())  # スタックトレースを出力
                logger.info(f"エラーが発生しました: {traceback.format_exc()}. リトライ中... ({attempts+1}/{max_attempts})")
                #send_slack_notify(f"エラーが発生しました: {e}. リトライ中... ({attempts+1}/{max_attempts})")
                attempts += 1
                time.sleep(1)  # エラー間の待機時間（必要に応じて調整）
        print(f"{func.__name__}の最大リトライ回数に達しました。スキップします。")
        return None
    return wrapper

def fukusho_retry(func, max_attempts=5):
    """
    指定された関数をリトライするデコレータ。最大リトライ回数に達するまで、または成功するまで関数を呼び出します。
    
    Args:
        func: リトライする関数
        max_attempts: 最大リトライ回数
        
    Returns:
        関数の実行結果、ただし10回リトライしても解決しない場合、'---.-'はNoneに置き換えられる
    """
    def wrapper(*args, **kwargs):
        attempts = 0
        least_invalids = float('inf')  # To track the list with the fewest '---.-'
        best_result = None
        while attempts < max_attempts:
            try:
                result = func(*args, **kwargs)
                if '---.-' in result:
                    # Count '---.-' in the current result
                    current_invalids = result.count('---.-')
                    if current_invalids < least_invalids:
                        least_invalids = current_invalids
                        best_result = result
                    raise ValueError("Invalid value '---.-' found, triggering retry.")
                return result
            except Exception as e:
                print(f"Error occurred: {e}. Retrying... ({attempts+1}/{max_attempts})\n")
                logger.info(f"Error occurred: {e}. Retrying... ({attempts+1}/{max_attempts})\n")
                print(result)
                logger.info(f"result: {result}")
                attempts += 1
                time.sleep(1)
        
        # After max attempts, return the best result we've recorded
        print(f"Max attempts reached for {func.__name__}. Returning best result with least '---.-'")
        best_result=[None if x == '---.-' else x for x in best_result]
        print(best_result)
        return best_result
    return wrapper