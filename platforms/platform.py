from abc import ABC, abstractmethod

class Platform(ABC):
	@abstractmethod
	def download(self, month):
		pass

	@abstractmethod
	def parse(self, month):
		pass
