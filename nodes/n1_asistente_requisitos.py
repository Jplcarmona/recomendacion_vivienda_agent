import json
import os
from tools.openai_client import OpenAIClient
from langchain_core.messages import SystemMessage, HumanMessage
from state import SystemState

SYSTEM_PROMPT = """Eres un asistente especializado en extracción de requisitos inmobiliarios.
Tu tarea es analizar el texto de un usuario y extraer sus preferencias de vivienda en formato JSON.

Extrae los siguientes campos. Si un campo no se menciona, usa el valor por defecto indicado:

{
  "region": "ciudad o barrio PRINCIPAL mencionado (default: 'Medellín')",
  "regiones": ["SOLO los barrios o zonas que el usuario mencione explícitamente como opciones.
                Si menciona UN solo barrio, lista solo ese. 
                Si menciona DOS o más separados por 'o', 'y', 'idealmente', listarlos todos.
                NUNCA añadas la ciudad como región extra.
                Ejemplos:
                - 'en Estadio' → ['Estadio']
                - 'en El Poblado o Laureles' → ['El Poblado', 'Laureles']
                - 'en Medellín, idealmente Belén o Robledo' → ['Belén', 'Robledo']
                - 'en Medellín' → ['Medellín']"],
  "area_min": número en m² mínimo (default: 40),
  "area_max": número en m² máximo (default: 200),
  "precio_min": precio mínimo en COP (default: 100000000),
  "precio_max": precio máximo en COP (default: 800000000),
  "tipo_inmueble": "apartamento | casa | estudio | local" (default: "apartamento"),
  "num_cuartos": número entero de habitaciones mínimas requeridas (default: 2),
  "num_banos": número entero de baños mínimos requeridos, o null si no se menciona (default: null),
  "parqueadero": true si el usuario menciona parqueadero, garaje o parking, si no false (default: false),
  "estrato": número del 1 al 6 o null (default: null),
  "amenities": lista de strings como ["piscina", "gym", "bbq"] (default: [])
}

IMPORTANTE:
- Convierte precios en millones: "300 millones" → 300000000
- Si dice "norte de Medellín", region = "Norte Medellín"
- Si dice "cerca a universidades", añade "universidades" a amenities
- Si dice "2 baños" o "dos baños" → num_banos = 2
- Si dice "al menos 3 habitaciones" → num_cuartos = 3
- Si dice "con parqueadero" o "que tenga garaje" → parqueadero = true
- Responde SOLO con el JSON, sin explicaciones adicionales.

EJEMPLOS COMPLETOS:
Input: "Busco apto en El Poblado, máximo 400 millones, 2 habitaciones y 2 baños, con parqueadero"
Output: {
  "region": "El Poblado",
  "regiones": ["El Poblado"],
  "area_min": 40, "area_max": 200,
  "precio_min": 100000000, "precio_max": 400000000,
  "tipo_inmueble": "apartamento",
  "num_cuartos": 2, "num_banos": 2,
  "parqueadero": true, "estrato": null, "amenities": []
}

Input: "Casa en Laureles o Envigado, 3 alcobas, sin importar baños, 500 millones"
Output: {
  "region": "Laureles",
  "regiones": ["Laureles", "Envigado"],
  "area_min": 40, "area_max": 200,
  "precio_min": 100000000, "precio_max": 500000000,
  "tipo_inmueble": "casa",
  "num_cuartos": 3, "num_banos": null,
  "parqueadero": false, "estrato": null, "amenities": []
}
"""

def nodo_asistente_requisitos(state: SystemState) -> SystemState:
    """
    Nodo 1: Interpreta el texto libre del usuario y estructura los criterios.
    """
    print("\n [Nodo 1] Interpretando requisitos del usuario...")
    llm = OpenAIClient.primary()
    
    try:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Texto del usuario: {state['input_usuario']}")
        ]
        
        response = llm.invoke(messages)
        raw_content = response.content.strip()
        
        # Limpiar posibles markdown code blocks
        if raw_content.startswith("```"):
            raw_content = raw_content.split("```")[1]
            if raw_content.startswith("json"):
                raw_content = raw_content[4:]
        
        criterios = json.loads(raw_content)
        
        # Validaciones básicas
        criterios["precio_max"] = max(criterios["precio_max"], criterios["precio_min"] + 50_000_000)
        criterios["area_max"] = max(criterios["area_max"], criterios["area_min"] + 20)
        
        print(f"Criterios extraídos:")
        print(f"Región: {criterios['region']}")
        print(f"Regiones: {criterios.get('regiones', [])}")
        print(f"Precio: ${criterios['precio_min']:,} - ${criterios['precio_max']:,}")
        print(f"Área: {criterios['area_min']}-{criterios['area_max']} m²")
        print(f"Tipo: {criterios['tipo_inmueble']} | Cuartos: {criterios['num_cuartos']}")
        
        return {**state, "criterios_originales": criterios.copy(), "criterios_actuales": criterios.copy(), "error": None}
        
    except json.JSONDecodeError as e:
        print(f"Error parseando JSON: {e}")
        # Criterios por defecto si falla el parsing
        criterios_default = {
            "region": "Medellín",
            "area_min": 50, "area_max": 150,
            "precio_min": 200_000_000, "precio_max": 600_000_000,
            "tipo_inmueble": "apartamento",
            "num_cuartos": 2, "num_banos": None,
            "parqueadero": False, "estrato": None, "amenities": []
        }
        return {**state, "criterios_originales": criterios_default.copy(), "criterios_actuales": criterios_default.copy(), "error": f"Error parsing criterios: {str(e)}"}
    
    except Exception as e:
        print(f"Error inesperado: {e}")
        return {**state, "error": str(e)}