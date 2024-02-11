from .models import LogList, Log


class BaseDatabase:
    def __init__(self) -> None:
        self.logs = LogList(logs=[Log(term=0, command={"block": "create"})])
        self.current_term = 0
        self.voted_for = None
        self.connect()

    def connect(self) -> None:
        raise NotImplementedError

    def configure(self, config) -> None:
        raise NotImplementedError    

    @property
    def logs(self) -> LogList:
        raise NotImplementedError

    @logs.setter
    def logs(self, value: LogList):
        raise NotImplementedError

    @property
    def current_term(self) -> int:
        raise NotImplementedError

    @current_term.setter
    def current_term(self, value: int) -> None:
        raise NotImplementedError

    @property
    def voted_for(self) -> str | bool:
        raise NotImplementedError

    @voted_for.setter
    def voted_for(self, value: str | bool) -> None:
        raise NotImplementedError