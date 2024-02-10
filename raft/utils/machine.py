class BaseMachine:
    def init(self, config: dict):
        raise NotImplementedError

    def post_request(self, command):
        raise NotImplementedError

    def get_request(self, command) -> any:
        raise NotImplementedError
