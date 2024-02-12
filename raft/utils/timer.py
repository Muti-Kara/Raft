import threading
import random

class FunctionTimer:
    """
    Timer for periodically executing a function with random intervals.
    """

    def __init__(self, min_interval, max_interval, func, start: bool = True) -> None:
        """
        Initialize the FunctionTimer.

        Args:
            min_interval (float): Minimum interval for function execution (in seconds).
            max_interval (float): Maximum interval for function execution (in seconds).
            func (callable): The function to be executed.
            start (bool, optional): Whether to start the timer immediately upon initialization. Defaults to True.
        """
        self._min_interval = min_interval
        self._max_interval = max_interval
        self._func = func

        if start:
            self.start()

    def start(self):
        """
        Start the timer with a random interval.
        """
        random_interval = random.uniform(self._min_interval, self._max_interval)
        self._timer = threading.Timer(random_interval, self._func)
        self._timer.start()

    def stop(self):
        """
        Stop the timer.
        """
        self._timer.cancel()

    def reset(self):
        """
        Reset the timer by stopping it and starting it again.
        """
        self.stop()
        self.start()