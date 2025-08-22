import requests


class RestoreService:
    """
    Service for restoring files via a POST request to an API endpoint.

    The service sends requests to the restore API endpoint at:
    http://localhost:8080/api/v1/restore
    """
    @staticmethod
    def restore(data: str):
        """
        Sends a JSON-formatted string to the restore API endpoint.

        Parameters
        __________
        data: str
            A JSON string representing the data to restore.

        Returns
        _______
        requests.Response
            The response object from the POST request.

        Raises
        ______
        requests.RequestException
            If the HTTP request encounters an error.
        """
        return requests.request(method='POST', url='http://localhost:8080/api/v1/restore',
                                data=data, headers={"Content-Type": "application/json"})
