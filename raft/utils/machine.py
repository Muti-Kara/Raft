class BaseMachine:
    def post_request(self, command):
        """
        Abstract method to handle a POST request.

        Args:
            command: Command to be processed. Must be a dict.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError

    def get_request(self, command) -> any:
        """
        Abstract method to handle a GET request.

        Args:
            command: Command to be processed. Must be a dict.

        Returns:
            result

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError


class KeyValueStoreMachine(BaseMachine):
    def __init__(self) -> None:
        """
        Initializes a KeyValueStoreMachine instance.
        """
        self.store = {}

    def post_request(self, command):
        """
        Handles a POST request by storing a key-value pair in the store.

        Args:
            command: Command containing the key-value pair to be stored.

        Returns:
            tuple: The key-value pair and a boolean indicating whether the operation was successful.
        """
        self.store[command["key"]] = command["value"]
        return (command["key"], command["value"]), True

    def get_request(self, command):
        """
        Handles a GET request by retrieving a value from the store.

        Args:
            command: Command containing the key to be retrieved.

        Returns:
            tuple: The retrieved value and a boolean indicating whether the operation was successful.
        """
        if self.store.get(command["key"], None):
            return self.store[command["key"]], True
        return None, False
