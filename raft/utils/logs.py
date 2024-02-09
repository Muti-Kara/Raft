from pydantic import BaseModel


class Log(BaseModel):
    term: int
    command: dict


class LogList(BaseModel):
    logs: list[Log] = list()

    def add_log(self, value: Log):
        self.logs.append(value)

    def add_logs(self, index, value: 'LogList'):
        self.logs[index:] = value.logs