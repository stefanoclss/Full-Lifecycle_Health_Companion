from abc import ABC, abstractmethod

class CareStageStrategy(ABC):
    @abstractmethod
    def build_interface(self, parent_frame):
        pass

    @abstractmethod
    def process_action(self, data):
        pass
