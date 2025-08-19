import requests


class CommitService:
    @staticmethod
    def commit(data: str):
        return requests.request(method='POST', url='http://localhost:8080/api/v1/commit', data=data,
                                headers={"Content-Type": "application/json"})
