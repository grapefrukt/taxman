from abc import ABC, abstractmethod

class Platform(ABC):
    @abstractmethod
    def download(self):
        pass

    @abstractmethod
    def parse(self):
        pass
