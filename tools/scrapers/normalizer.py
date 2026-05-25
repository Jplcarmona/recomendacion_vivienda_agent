import json
from tools.openai_client import OpenAIClient

llm = OpenAIClient.fast()

def normalizar_propiedad(texto):

    prompt = f"""
    Extrae información inmobiliaria de este texto.

    Texto:
    {texto}

    Devuelve JSON:
    {{
      "precio": int,
      "area": int,
      "cuartos": int,
      "banos": int,
      "parqueadero": bool
    }}
    """
    response = llm.invoke(prompt)

    return json.loads(response.content)

