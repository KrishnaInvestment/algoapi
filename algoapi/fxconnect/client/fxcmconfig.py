from forexconnect import ForexConnect

from algoapi.read_config import config


class FXCMClient:
    def __init__(self, **kwargs):
        self.user_id = kwargs.get("USER_ID") or config.get("USER_ID")
        self.password = kwargs.get("USER_PASSWORD") or config.get("USER_PASSWORD")
        self.str_url = kwargs.get("URL") or config.get("URL")
        self.connection = kwargs.get("CONNECTION") or config.get("CONNECTION")
        self.str_account = kwargs.get("ACCOUNT") or config.get("ACCOUNT")
        self.session_id = kwargs.get("SESSON_ID") or config.get("SESSON_ID")
        self.pin = kwargs.get("PIN") or config.get("PIN")

    def login(self):
        user_id = self.user_id
        password = self.password
        url = self.str_url
        connection = self.connection
        fx = ForexConnect()
        try:
            fx.login(user_id, password, url, connection)
            return fx
        except Exception as e:
            raise e
