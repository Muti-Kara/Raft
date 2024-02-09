class BaseMachine:
    def post_request(self, command):
        raise NotImplementedError

    def get_request(self, command):
        raise NotImplementedError


class KeyStoreMachine:
    def __init__(self) -> None:
        self.store = {}

    def post_request(self, command):
        self.store[command["key"]] = command["value"]
        return (command["key"], command["value"]), True


    def get_request(self, command):
        if self.store.get(command["key"], None):
            return self.store[command["key"]], True
        return None, False