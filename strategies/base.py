from abc import ABC, abstractmethod

class CareStageStrategy(ABC):
    @abstractmethod
    def get_metadata(self) -> dict:
        """Returns metadata for the UI (title, description, input fields, etc.)"""
        pass

    @abstractmethod
    def process_action(self, data: dict) -> dict:
        """Processes an action and returns a result"""
        pass
