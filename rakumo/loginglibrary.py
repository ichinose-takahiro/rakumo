from logging.handlers import TimedRotatingFileHandler
import logging

loggers = {}

def init(name=None):
    global loggers
    if name is None:
        name = __name__

    if loggers.get(name):
        return loggers.get(name)

    logger = None
    # ルートロガーを取得
    logger = logging.getLogger(name)

    # フォーマッターを作成
    formatter = logging.Formatter('%(asctime)s %(name)s %(funcName)s [%(levelname)s]: %(message)s')

    # ハンドラーを作成しフォーマッターを設定
    handler = TimedRotatingFileHandler(
        filename="/var/log/rakumo/rakumoLog.log",
        when="D",
        interval=1,
        backupCount=31,
    )
    handler.setFormatter(formatter)

    # ロガーにハンドラーを設定、イベント捕捉のためのレベルを設定
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    loggers[name] = logger
    return logger
