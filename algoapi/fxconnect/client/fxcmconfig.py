from forexconnect import ForexConnect

from algoapi.read_config import config

class FXCMClient:
    def __init__(self):
        self.user_id = config.get('USER_ID')
        self.password = config.get('USER_PASSWORD')
        self.str_url = config.get('URL')
        self.connection = config.get('CONNECTION')
        self.str_account = config.get('ACCOUNT')
        self.session_id = config.get('SESSON_ID')
        self.pin = config.get('PIN')
        self.fx = None

    def get_data(self):
        return 'c'

    def login(self):
        user_id = config.get('USER_ID')
        password = config.get('USER_PASSWORD')
        url = config.get('URL')
        connection = config.get('CONNECTION')
        fx = ForexConnect()
        try:
            fx.login(user_id, password, url,
                        connection)
            return fx
        except Exception as e:
            raise e
