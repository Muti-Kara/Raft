import threading
import random


class FunctionTimer:
    def __init__(self, min_interval, max_interval, func, start: bool = True) -> None:
        self._min_interval = min_interval
        self._max_interval = max_interval
        self._func = func

        if start:
            self.start()

    def start(self):
        random_interval = random.uniform(self._min_interval, self._max_interval)
        self._timer = threading.Timer(random_interval, self._func)
        self._timer.start()

    def stop(self):
        self._timer.cancel()

    def reset(self):
        self.stop()
        self.start()