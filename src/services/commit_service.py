import requests


class CommitService:
    """
        Service for committing files via a POST request to an API endpoint.

        The service sends requests to the commit API endpoint at:
        http://localhost:8080/api/v1/commit
        """
    @staticmethod
    def commit(data: str):
        """
        Sends a JSON-formatted string to the commit API endpoint.

        Parameters
        __________
        data: str
            A JSON string representing the data to commit.

        Returns
        _______
        requests.Response
            The response object from the POST request.

        Raises
        ______
        requests.RequestException
            If the HTTP request encounters an error.
        """
        return requests.request(method='POST', url='http://localhost:8080/api/v1/commit', data=data,
                                headers={"Content-Type": "application/json"})
