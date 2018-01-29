from logging.handlers import TimedRotatingFileHandler
import logging

def init():
    # ルートロガーを取得
    logger = logging.getLogger()

    # フォーマッターを作成
    formatter = logging.Formatter('%(asctime)s %(name)s %(funcName)s [%(levelname)s]: %(message)s')

    # ハンドラーを作成しフォーマッターを設定
    handler = TimedRotatingFileHandler(
        filename="/var/log/rakumoLog.log",
        when="D",
        interval=1,
        backupCount=31,
    )
    handler.setFormatter(formatter)

    # ロガーにハンドラーを設定、イベント捕捉のためのレベルを設定
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    return logger