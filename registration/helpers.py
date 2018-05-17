from datetime import datetime

from constance import config


def is_registration_open():
    open_datetime = datetime.combine(config.REGISTRATION_OPEN, config.REGISTRATION_OPEN_TIME)
    close_datetime = datetime.combine(config.REGISTRATION_CLOSE, config.REGISTRATION_CLOSE_TIME)
    return open_datetime <= datetime.now() <= close_datetime
