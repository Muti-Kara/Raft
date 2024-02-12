class BaseMachine:
    """
    Abstract base class for defining the behavior of a Raft node's state machine.

    Subclasses must implement the methods to configure the machine and handle request processing.

    Attributes:
        None
    """

    def configure(self, config: dict):
        """
        Configure the state machine.

        This method should be implemented by subclasses to initialize the state machine
        with the necessary configurations.

        Args:
            config (dict): Configuration parameters for the state machine.
        """
        raise NotImplementedError

    def post_request(self, command):
        """
        Process a POST request in the state machine.

        This method should be implemented by subclasses to handle the processing
        of a POST request in the state machine.

        Args:
            command: The command to be processed.

        Returns:
            any: The result of the request processing.
        """
        raise NotImplementedError

    def get_request(self, command) -> any:
        """
        Process a GET request in the state machine.

        This method should be implemented by subclasses to handle the processing
        of a GET request in the state machine.

        Args:
            command: The command to be processed.

        Returns:
            any: The result of the request processing.
        """
        raise NotImplementedError