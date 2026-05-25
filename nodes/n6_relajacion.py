import json
import os
from tools.openai_client import OpenAIClient
from langchain_core.messages import SystemMessage, HumanMessage
from state import SystemState

SYSTEM_PROMPT = """Eres un agente especializado en relajación progresiva de criterios de búsqueda inmobiliaria.
Tu objetivo es modificar los criterios de forma mínima y gradual para ampliar la búsqueda.

REGLAS:
1. Modifica UN SOLO criterio a la vez (en relajación leve), máximo 2 en relajación moderada
2. Nunca cambies precio en más del 20% por iteración
3. Nunca cambies área en más del 30% por iteración
4. Prioridad de relajación: precio > área > cuartos > tipo > zona
5. Documenta SIEMPRE el cambio con una razón clara

Niveles de relajación:
- Nivel 1 (leve): +10-15% precio_max, o +10m² en area_max
- Nivel 2 (moderado): +20% precio_max, o -1 cuarto, o ampliar tipo
- Nivel 3 (agresivo): +20% precio_max Y -1 cuarto, o cambiar zona

Devuelve SOLO un JSON:
{
  "criterios_modificados": { ...criterios completos actualizados... },
  "cambios": [
    {
      "campo": "nombre_del_campo",
      "valor_anterior": valor,
      "valor_nuevo": valor,
      "razon": "por qué se cambió este campo"
    }
  ],
  "resumen": "descripción de los cambios realizados"
}
"""

# Orden de prioridad de relajación
ORDEN_RELAJACION = [
    "precio_max",
    "area_min", 
    "num_cuartos",
    "parqueadero",
    "estrato",
    "tipo_inmueble",
    "region"
]

def nodo_relajacion(state: SystemState) -> SystemState:
    """
    Nodo 6: Relaja los criterios de búsqueda de forma gradual y trazable.
    """
    llm = OpenAIClient.fast()
    
    print(f"\n [Nodo 6] Aplicando relajación de criterios (nivel {state['nivel_relajacion'] + 1})...")
    
    criterios_actuales = dict(state["criterios_actuales"])
    criterios_originales = dict(state["criterios_originales"])
    nivel = state["nivel_relajacion"] + 1
    iteracion = state["iteracion_actual"]
    causa = state.get("causa_insuficiencia", "No se encontraron suficientes propiedades")
    
    # Calcular la relajación ya aplicada para cada campo
    ya_relajado = {}
    for rel in state.get("historial_relajaciones", []):
        campo = rel.get("campo", "")
        ya_relajado[campo] = ya_relajado.get(campo, 0) + 1
    
    prompt = f"""
CRITERIOS ORIGINALES DEL USUARIO (no modificar más allá de lo necesario):
{json.dumps(criterios_originales, indent=2, ensure_ascii=False)}

CRITERIOS ACTUALES (a relajar):
{json.dumps(criterios_actuales, indent=2, ensure_ascii=False)}

CAUSA DE FALLO: {causa}

NIVEL DE RELAJACIÓN A APLICAR: {nivel} (1=leve, 2=moderado, 3=agresivo)

CAMPOS YA RELAJADOS PREVIAMENTE:
{json.dumps(ya_relajado, indent=2, ensure_ascii=False)}

ITERACIÓN ACTUAL: {iteracion}

Aplica la relajación apropiada. Prioriza modificar {ORDEN_RELAJACION[min(nivel-1, len(ORDEN_RELAJACION)-1)]}.
"""
    try:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        
        resultado = json.loads(raw)
        criterios_nuevos = resultado["criterios_modificados"]
        cambios = resultado.get("cambios", [])
        
        # Registrar en historial
        historial = list(state.get("historial_relajaciones", []))
        modificaciones = list(state.get("modificaciones_realizadas", []))
        
        for cambio in cambios:
            historial.append({
                "iteracion": iteracion,
                "campo": cambio["campo"],
                "valor_anterior": cambio["valor_anterior"],
                "valor_nuevo": cambio["valor_nuevo"],
                "razon": cambio["razon"]
            })
            desc = (f"Iter {iteracion}: {cambio['campo']} "
                    f"{cambio['valor_anterior']} → {cambio['valor_nuevo']} "
                    f"({cambio['razon']})")
            modificaciones.append(desc)
            print(f"{cambio['campo']}: {cambio['valor_anterior']} → {cambio['valor_nuevo']}")
            print(f"Razón: {cambio['razon']}")
        
        print(f"{resultado.get('resumen', '')}")
        
        return {
            **state,
            "criterios_actuales": criterios_nuevos,
            "nivel_relajacion": nivel,
            "historial_relajaciones": historial,
            "modificaciones_realizadas": modificaciones,
            # Limpiar propiedades para nueva búsqueda
            "propiedades_filtradas": [],
            "propiedades_evaluadas": [],
        }
        
    except Exception as e:
        print(f"Error en relajación: {e}. Aplicando relajación manual.")
        criterios_nuevos, cambio_desc = _relajacion_manual(criterios_actuales, nivel)
        
        historial = list(state.get("historial_relajaciones", []))
        historial.append({
            "iteracion": iteracion,
            "campo": "precio_max (manual)",
            "valor_anterior": criterios_actuales.get("precio_max"),
            "valor_nuevo": criterios_nuevos.get("precio_max"),
            "razon": "Relajación automática por error en LLM"
        })
        
        return {
            **state,
            "criterios_actuales": criterios_nuevos,
            "nivel_relajacion": nivel,
            "historial_relajaciones": historial,
            "propiedades_filtradas": [],
            "propiedades_evaluadas": [],
        }


def _relajacion_manual(criterios: dict, nivel: int) -> tuple:
    """Relajación manual como fallback."""
    nuevos = dict(criterios)
    
    if nivel == 1:
        nuevos["precio_max"] = int(criterios.get("precio_max", 500_000_000) * 1.15)
        desc = f"Precio máximo aumentado 15%: {criterios['precio_max']:,} → {nuevos['precio_max']:,}"
    elif nivel == 2:
        nuevos["precio_max"] = int(criterios.get("precio_max", 500_000_000) * 1.20)
        nuevos["area_min"] = max(20, criterios.get("area_min", 50) - 10)
        desc = "Precio +20% y área mínima -10m²"
    else:
        nuevos["precio_max"] = int(criterios.get("precio_max", 500_000_000) * 1.20)
        nuevos["num_cuartos"] = max(1, criterios.get("num_cuartos", 2) - 1)
        desc = "Precio +20% y cuartos -1"
    
    return nuevos, desc