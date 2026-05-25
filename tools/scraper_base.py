from abc import ABC, abstractmethod
from typing import List, Dict


class BaseScraper(ABC):
    """Clase abstracta base para scrapers."""

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def buscar_propiedades(self, criterios: dict) -> List[Dict]:
        pass