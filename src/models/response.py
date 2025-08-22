class Response:
    """
    Represents a response object with status, results, and a message.
    """
    def __init__(self, status: int, results: list[str], message: str):
        """
        Initialize a Response

        Parameters
        __________
        status: int
            Status code value
        results: list[str]
            List of results of using an API endpoint
        message: str
            Results summary message
        """
        self._status = status
        self._results = results
        self._message = message

    @property
    def status(self) -> int:
        """
        Get the status code value.

        Returns
        _______
        int
            The status code value of the Response.
        """
        return self._status

    @status.setter
    def status(self, status: int):
        """
        Set the status code value.

        Parameters
        __________
        status: int
            The status code value of the Response.
        """
        self._status = status

    @property
    def results(self) -> list[str]:
        """
        Get the results list.

        Returns
        _______
        list[str]
            The results list of the Response.
        """
        return self._results

    @results.setter
    def results(self, results: list[str]):
        """
        Set the results list.

        Parameters
        __________
        results: list[str]
            The results list of the Response.
        """
        self._results = results

    @property
    def message(self) -> str:
        """
        Get the results summary message.

        Returns
        _______
        str
            The results summary message of the Response.
        """
        return self._message

    @message.setter
    def message(self, message: str):
        """
        Set the results summary message.

        Parameters
        __________
        message: str
            The results summary message of the Response.
        """
        self._message = message

    def __repr__(self):
        return f"CommitResponse(status={self.status}, results={self.results}, message={self.message}"
