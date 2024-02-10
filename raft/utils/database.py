from .models import LogList, Log


class BaseDatabase:
    def init(self, config) -> None:
        self.logs = LogList(logs=[Log(term=0, command={"block": "create"})])

    @property
    def current_term(self) -> int:
        raise NotImplementedError

    @current_term.setter
    def current_term(self, value: int) -> None:
        raise NotImplementedError

    @property
    def voted_for(self) -> int:
        raise NotImplementedError

    @voted_for.setter
    def voted_for(self, value: int) -> None:
        raise NotImplementedError