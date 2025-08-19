class Response:
    def __init__(self, status: int, results: list[str], message: str):
        self.status = status
        self.results = results
        self.message = message

    def __repr__(self):
        return f"CommitResponse(status={self.status}, results={self.results}, message={self.message}"
