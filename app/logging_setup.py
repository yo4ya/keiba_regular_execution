# from google.cloud import logging

# # クライアントを作成し、ロガーを設定
# client = logging.Client()
# logger = client.logger("shared-log")  # すべてのファイルで共有するログの名前

# def get_logger():
#     """ロガーを取得する関数"""
#     return logger

import json
import logging
import sys
from datetime import datetime

def get_logger(name=None):
    """構造化ログを出力するロガーを取得する関数"""
    logger_name = name or "shared-log"
    logger = logging.getLogger(logger_name)
    
    # ハンドラが既に設定されている場合は既存のロガーを返す
    if logger.handlers:
        return logger
        
    # 新しいロガーを設定
    handler = logging.StreamHandler(sys.stdout)
    formatter = StructuredLogFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

class StructuredLogFormatter(logging.Formatter):
    """Cloud Logging用の構造化ログフォーマッタ"""
    
    def format(self, record):
        # 基本的なログ情報
        log_entry = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "time": datetime.utcnow().isoformat() + "Z",
        }
        
        # 例外情報がある場合は追加
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        # カスタム属性がある場合は追加
        if hasattr(record, "extras") and record.extras:
            for key, value in record.extras.items():
                log_entry[key] = value
                
        return json.dumps(log_entry, ensure_ascii=False)
