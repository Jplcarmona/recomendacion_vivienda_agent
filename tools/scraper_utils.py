import random
import time
import requests
from bs4 import BeautifulSoup

class ScraperUtils:

    @staticmethod
    def random_user_agent(user_agents: list):
        return random.choice(user_agents)

    @staticmethod
    def request_with_retry(
        url: str,
        headers: dict,
        max_retries: int = 3,
        timeout: int = 20
    ):

        for attempt in range(max_retries):
            try:
                response = requests.get(url,headers=headers,timeout=timeout)
                response.raise_for_status()
                return response

            except Exception as e:
                print(f"Error request {attempt+1}: {e}")
                time.sleep(2)

        return None

    @staticmethod
    def soup(html: str):
        return BeautifulSoup(html, "lxml")