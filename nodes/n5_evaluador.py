import json
from state import SystemState
from tools.scoring import calcular_score
from tools.openai_client import OpenAIClient
import yaml

with open("config/config.yaml", "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

def nodo_evaluador(state: SystemState) -> SystemState:

    print("\n [Nodo 5] Evaluando propiedades...")

    llm = OpenAIClient.primary()

    propiedades = state.get("propiedades_filtradas", [])
    criterios = state.get("criterios_actuales", {})
    info_zonas = state.get("info_zonas", {})

    if not propiedades:
        return {**state, "propiedades_evaluadas": [], "resultado_evaluacion": "vacio", "causa_insuficiencia": "No se encontraron propiedades"}

    # SCORING HEURÍSTICO
    propiedades_evaluadas = []

    for prop in propiedades:

        score_data = calcular_score(prop, criterios)
        barrio = prop.get("barrio", "")
        ciudad = prop.get("ciudad", "")
        
        zona_info = None
        for zona_key, zona_val in info_zonas.items():
            if zona_key.lower() in barrio.lower() or barrio.lower() in zona_key.lower():
                zona_info = zona_val
                break
        
        bonus_zona = 0.0
        nota_zona = ""
        
        if zona_info and "analisis" in zona_info:
            compatibilidad = zona_info["analisis"].get("compatibilidad", 0.5)
            recomendacion = zona_info["analisis"].get("recomendacion", "media")
            alerta = zona_info["analisis"].get("alerta_seguridad")
            
            if recomendacion == "alta":
                bonus_zona = 0.05
                nota_zona = f"zona recomendada ({compatibilidad:.0%} compatibilidad)"
            elif recomendacion == "baja" or (alerta and compatibilidad < 0.3):
                bonus_zona = -0.10
                nota_zona = f"zona con alertas de seguridad ({compatibilidad:.0%})"
            else:
                nota_zona = f"zona media ({compatibilidad:.0%} compatibilidad)"
                
            if nota_zona:
                score_data["razones"].append(nota_zona)
                
        score_final = min(1.0, max(0.05, round(score_data["score"] + bonus_zona, 2)))
        score_data["score"] = score_final
        
        prop.update(score_data)
        propiedades_evaluadas.append(prop)

    propiedades_evaluadas.sort(key=lambda x: x["score"], reverse=True)
    
    # DEBUG VISUAL
    print("\n TOP PROPIEDADES:")
    for prop in propiedades_evaluadas[:10]:
        score = prop["score"]
        barras = "█" * int(score * 10) + "░" * (10 - int(score * 10))
        print(f"[{barras}] {score:.2f} | {prop.get('titulo', 'Sin título')[:60]}")

    # UMBRALES MÁS FLEXIBLES
    umbral = CONFIG.get("system", {}).get("score_umbral", 0.45)
    aceptables = [p for p in propiedades_evaluadas if p["score"] >= umbral]

    min_propiedades = CONFIG.get("system", {}).get("min_propiedades", 3)
    
    # DECISIÓN FLEXIBLE
    if len(aceptables) >= min_propiedades:
        decision = "aceptable"
    elif len(propiedades_evaluadas) >= min_propiedades:
        decision = "aceptable"
        aceptables = propiedades_evaluadas[:3]
    else:
        decision = "insuficiente"

    print(f"\n Decisión: {decision.upper()}")
    print(f"Propiedades aceptables: {len(aceptables)}")

    resultado_final = aceptables[:5]
    
    # EXPLICACIÓN FINAL
    explicacion = _generar_explicacion(resultado_final, criterios, info_zonas, llm)

    return {
        **state,
        "propiedades_evaluadas": propiedades_evaluadas,
        "resultado_evaluacion": decision,
        "resultado_final": resultado_final,
        "explicacion_final": explicacion
    }

def _generar_explicacion(propiedades, criterios, info_zonas, llm):
    """Genera explicación narrativa usando propiedades Y contexto de zonas."""
    try:
        # resumir info de zonas relevantes
        zonas_relevantes = {}
        for prop in propiedades:
            barrio = prop.get("barrio", "")
            for zona_key, zona_val in info_zonas.items():
                if zona_key.lower() in barrio.lower() or barrio.lower() in zona_key.lower():
                    if zona_key not in zonas_relevantes:
                        analisis = zona_val.get("analisis", {})
                        zonas_relevantes[zona_key] = {
                            "compatibilidad": analisis.get("compatibilidad"),
                            "resumen":        analisis.get("resumen"),
                            "alerta":         analisis.get("alerta_seguridad"),
                            "oportunidad":    analisis.get("oportunidad"),
                        }

        prompt = f"""
Eres un asesor inmobiliario. Explica en 3-4 párrafos por qué estas propiedades
son las mejores opciones para el usuario, considerando tanto sus características
como el contexto de las zonas.

CRITERIOS DEL USUARIO:
{json.dumps(criterios, indent=2, ensure_ascii=False)}

PROPIEDADES RECOMENDADAS:
{json.dumps(propiedades[:5], indent=2, ensure_ascii=False)}

CONTEXTO DE ZONAS (noticias y análisis):
{json.dumps(zonas_relevantes, indent=2, ensure_ascii=False)}

Menciona explícitamente si alguna zona tiene alertas de seguridad o buenas oportunidades.
Sé honesto y conciso.
"""
        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content

    except Exception as e:
        print(f"Error generando explicación: {e}")
        return "Se encontraron propiedades alineadas con los criterios."