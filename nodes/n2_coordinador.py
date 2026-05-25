import json
import os
from tools.openai_client import OpenAIClient
from langchain_core.messages import SystemMessage, HumanMessage
from state import SystemState

SYSTEM_PROMPT = """Eres el coordinador de un sistema de búsqueda de vivienda en Colombia.
Tu rol es analizar los criterios del usuario, la información de zonas disponible, 
y decidir qué barrios o zonas son más prometedores para la búsqueda.

Dado el contexto, devuelve un JSON con:
{
  "zonas_priorizadas": ["lista de 3-5 zonas/barrios en orden de relevancia"],
  "razonamiento": "por qué estas zonas",
  "estrategia_busqueda": "descripción de cómo abordar la búsqueda",
  "alertas": ["lista de posibles problemas o restricciones detectadas"]
}

Considera:
- El tipo de inmueble y precio para determinar estratos adecuados
- Las noticias recientes de las zonas (si están disponibles)
- La preferencia de región del usuario como punto de partida
- Zonas alternativas si el precio es muy restrictivo
- En Colombia: estrato 4-6 suele ser El Poblado, Laureles, Envigado; estrato 2-3 Belén, Robledo, etc.
"""

def nodo_coordinador(state: SystemState) -> SystemState:
    """
    Nodo 2: Define zonas de búsqueda sintetizando criterios e información de contexto.
    """
    
    llm = OpenAIClient.fast()
    
    print(f"\n [Nodo 2] Coordinando zonas de búsqueda (iteración {state['iteracion_actual'] + 1})...")
    
    criterios = state["criterios_actuales"]
    info_zonas = state.get("info_zonas", {})
    
    regiones_usuario = criterios.get(
        "regiones",
        [criterios.get("region", "Medellín")]
    )
    
    contexto = f"""
CRITERIOS DEL USUARIO:
{json.dumps(criterios, indent=2, ensure_ascii=False)}

ZONAS PREFERIDAS POR EL USUARIO (TODAS deben considerarse):
{json.dumps(regiones_usuario, ensure_ascii=False)}

INFORMACIÓN DE ZONAS DISPONIBLE:
{json.dumps(info_zonas, indent=2, ensure_ascii=False) if info_zonas else "No hay información de zonas aún."}

NIVEL DE RELAJACIÓN ACTUAL: {state['nivel_relajacion']} (0=ninguno, 3=máximo)
ITERACIÓN: {state['iteracion_actual'] + 1}

INSTRUCCIÓN: Las zonas priorizadas DEBEN incluir todas las zonas preferidas por el usuario
como mínimo, más zonas alternativas compatibles con el precio y tipo de inmueble.
"""
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=contexto)
    ]
    
    try:
        response = llm.invoke(messages)
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        
        resultado = json.loads(raw)
        zonas = resultado.get("zonas_priorizadas", [criterios.get("region", "Medellín")])
        
        print(f"Zonas priorizadas: {', '.join(zonas)}")
        if resultado.get("alertas"):
            for alerta in resultado["alertas"]:
                print(f"Alerta: {alerta}")
        
        # Registrar iteración
        historial = list(state.get("historial_iteraciones", []))
        historial.append({
            "iteracion": state["iteracion_actual"] + 1,
            "zonas": zonas,
            "estrategia": resultado.get("estrategia_busqueda", ""),
        })
        
        return {
            **state,
            "zonas_recomendadas": zonas,
            "zonas_analizadas": list(set(state.get("zonas_analizadas", []) + zonas)),
            "iteracion_actual": state["iteracion_actual"] + 1,
            "historial_iteraciones": historial,
        }
        
    except Exception as e:
        print(f"Error en coordinador: {e}")
        region = criterios.get("region", "Medellín")
        return {
            **state,
            "zonas_recomendadas": [region, f"Norte de {region}", f"Sur de {region}"],
            "iteracion_actual": state["iteracion_actual"] + 1,
        }