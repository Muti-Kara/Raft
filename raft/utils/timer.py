import threading
import random


class FunctionTimer:
    def __init__(self, min_interval, max_interval, func, start: bool = True) -> None:
        """
        Initializes a FunctionTimer instance.

        Args:
            min_interval (float): Minimum interval for timer execution.
            max_interval (float): Maximum interval for timer execution.
            func (callable): The function to be called when the timer expires.
            start (bool, optional): Indicates whether to start the timer immediately upon initialization. 
                                     Defaults to True.
        """
        self._min_interval = min_interval
        self._max_interval = max_interval
        self._func = func

        if start:
            self.start()

    def start(self):
        """
        Starts the timer.
        """
        random_interval = random.uniform(self._min_interval, self._max_interval)
        self._timer = threading.Timer(random_interval, self._func)
        self._timer.start()

    def stop(self):
        """
        Stops the timer.
        """
        self._timer.cancel()

    def reset(self):
        """
        Stops the timer and starts it again.
        """
        self.stop()
        self.start()