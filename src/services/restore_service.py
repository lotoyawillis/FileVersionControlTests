import requests


class RestoreService:
    @staticmethod
    def restore(data: str):
        requests.request(method='POST', url='http://localhost:8080/api/v1/restore',
                         data=data, headers={"Content-Type": "application/json"})
