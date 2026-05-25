import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

class OpenAIClient:
    @staticmethod
    def primary():
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL_PRIMARY", "gpt-4o"),
            temperature=0.2,
            api_key=os.getenv("OPENAI_API_KEY")
        )

    @staticmethod
    def fast():
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL_FAST", "gpt-4o-mini"),
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )