from logging.config import dictConfig


class Config:
    SECRET_KEY = "4d20dbbc7accf4a6d71a90eaa910f7e4"  # TODO CHANGE
    MONGO_URI = "mongodb://localhost:27017/Toad-Test"  # TODO CHANGE
    MONGO2_DBNAME = 'Gatekeeper-Test'
    UPLOAD_FOLDER = 'uploads'
    TMP = 'tmp'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_USERNAME = 'CordialCyberCowboy@gmail.com'
    MAIL_PASSWORD = 'nejqbfcqqicjuxvm'
    # DROPZONE_MAX_FILE_SIZE = 1024


dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        },
        'simpleformatter': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            # 'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        },
        'custom_handler': {
            'class': 'logging.FileHandler',
            'formatter': 'simpleformatter',
            'filename': 'MasterLogger.log',  # Change or keep the same
            'level': 'INFO'
        }

    },
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi', 'custom_handler']
    }
})
