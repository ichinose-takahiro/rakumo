from logging.handlers import TimedRotatingFileHandler
import logging
import os
loggers = {}

def init(name=None):
    global loggers

    if name is None:
        name = __name__

    if loggers.get(name):
        return loggers.get(name)

    os.environ['TZ'] = 'Asia/Tokyo'
    logger = None
    # ルートロガーを取得
    logger = logging.getLogger(name)

    # フォーマッターを作成
    formatter = logging.Formatter('%(asctime)s %(name)s %(funcName)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

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

def setId(creId,user,ii,name):
    global loggers
  
    if loggers.get(name):
        return loggers.get(name) 
    # ルートロガーを取得
    
    #logger = loggers.get(name)
    os.environ['TZ'] = 'Asia/Tokyo'
    logger = None
    # ルートロガーを取得
    logger = logging.getLogger(name)

    formatter = logging.Formatter('%(asctime)s %(name)s userID:['+creId+'] name:['+ user +'] %(funcName)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

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
    loggers[name] = None
    loggers[name] = logger
    return logger
