import threading
import random
import os

import raft.config as config


class FunctionTimer:
    def __init__(self, interval, func, start: bool = True) -> None:
        self.interval = interval
        self.func = func

        if start:
            self.start()

    def start(self):
        self.timer = threading.Timer(random.randint(self.interval, 2 * self.interval) / 1000, self.func)
        self.timer.start()

    def stop(self):
        self.timer.cancel()

    def reset(self):
        self.stop()
        self.start()


class Log:
    def __init__(self, term, command) -> None:
        self.term: int = term
        self.command: str = command

    def __call__(self):
        print(f"Executing: {self.command}", flush=True)


class LogList:
    def __init__(self) -> None:
        self._logs: list[Log] = []

    def __getitem__(self, index):
        return self._logs[index]
    
    def __setitem__(self, index, value: Log):
        self._logs = self._logs[:index]
        self._logs.append(value)

    def __iter__(self):
        return iter(self._logs)

    def __len__(self):
        return len(self._logs)


class FileDatabase:
    def __init__(self) -> None:
        self.dir = f"/app/data/node{config.NODE_ID}/"
        self.current_term_file = f"{self.dir}/current_term.txt"
        self.voted_for_file = f"{self.dir}/voted_for.txt"
        self.logs_file = f"{self.dir}/logs.txt"
        self._logs = LogList()
        self.reset()
        self.timer = FunctionTimer(config.DATABASE_WRITE, self._auto_save)
        self.timer.start()

    def __del__(self) -> None:
        self.save()

    def _auto_save(self):
        self.save()
        self.timer.start()

    def reset(self):
        self.current_term = 0
        self.voted_for = -1
        self.logs[0] = Log(term=0, command="CREATE")
        os.makedirs(os.path.dirname(self.dir), exist_ok=True)
        self.save()

    def save(self):
        with open(self.current_term_file, "w") as f:
            f.write(str(self.current_term))
        with open(f"{self.dir}/voted_for.txt", "w") as f:
            f.write(str(self.voted_for))
        with open(f"{self.dir}/logs.txt", "w") as f:
            f.write('\n'.join([f"{log.term} {log.command}" for log in self.logs]))

    def load(self):
        with open(self.current_term_file, "r") as f:
            self._current_term = int(f.read())
        with open(f"{self.dir}/voted_for.txt", "r") as f:
            self._voted_for = int(f.read())
        self._logs = LogList()
        with open(f"{self.dir}/logs.txt", "r") as f:
            for index, line in enumerate(f.read().splitlines()):
                self._logs[index] = Log(
                    term=int(line.split()[0]),
                    command=line.split()[1]
                )

    @property
    def current_term(self):
        return self._current_term

    @current_term.setter
    def current_term(self, value):
        self._current_term = value

    @property
    def voted_for(self):
        return self._voted_for

    @voted_for.setter
    def voted_for(self, value):
        self._voted_for = value

    @property
    def logs(self) -> LogList: # array of Log(term, command)
        return self._logs