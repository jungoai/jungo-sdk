from abc import ABC, abstractmethod

class PingApi(ABC):
    @abstractmethod
    def ping(self) -> str:
        ...
    def echo(self, msg: str) -> str:
        ...
