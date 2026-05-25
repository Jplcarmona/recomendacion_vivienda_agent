import json
from tools.openai_client import OpenAIClient
from state import SystemState
from langchain_core.messages import SystemMessage, HumanMessage

SYSTEM_PROMPT = """Eres un validador experto de calidad en recomendaciones inmobiliarias.
Tu rol es hacer una revisión crítica final antes de presentar resultados al usuario.

Evalúa:
1. ¿Las propiedades cumplen los criterios OBLIGATORIOS (precio, área mínima, cuartos mínimos)?
2. ¿Hay suficiente diversidad (no todas del mismo barrio/precio)?
3. ¿Los scores son razonables y justificados?
4. ¿Las explicaciones son claras y útiles?

REGLAS DE EVALUACIÓN — LEE CON ATENCIÓN:
- num_cuartos es un MÍNIMO. Tener MÁS cuartos es positivo, NUNCA negativo.
- num_banos es un MÍNIMO. Tener más baños es positivo.
- "parqueadero no confirmado" NO ES UN PROBLEMA CRÍTICO. Los portales inmobiliarios
  colombianos como FincaRaiz y Metrocuadrado frecuentemente omiten esta información
  y piden contactar al asesor. Esto es una limitación del portal, no de la propiedad.
  NUNCA rechaces por parqueadero no confirmado.
- precio_max es un límite duro — propiedades hasta 10% sobre el máximo son aceptables.
- Diversidad: si la mayoría de propiedades son de un mismo barrio pero ese barrio
  cumple los criterios del usuario, es aceptable.

SOLO rechaza si:
- Más del 50% de propiedades están SOBRE el precio máximo (no levemente, sino claramente)
- Las propiedades no cumplen los criterios básicos de área o cuartos
- Hay datos claramente erróneos (precio 0, área 0, etc.)

Devuelve un JSON:
{
  "veredicto": "aprobado" | "rechazado",
  "score_calidad": número del 0 al 1,
  "observaciones": ["comentarios constructivos, máximo 3"],
  "problemas_criticos": ["SOLO si hay motivo real de rechazo según las reglas anteriores"],
  "mensaje_usuario": "resumen amigable de las recomendaciones (solo si aprobado)"
}
"""

def nodo_validador_whatsapp(state: SystemState) -> SystemState:
    """
    Nodo 7: Validación final de coherencia y calidad del resultado.
    """
    llm = OpenAIClient.fast()
    
    print("\n [Nodo 7] Validación final del resultado...")
    
    resultado = state.get("resultado_final", [])
    criterios_orig = state.get("criterios_originales", {})
    modificaciones = state.get("modificaciones_realizadas", [])
    
    if not resultado:
        print(" No hay resultado final para validar.")
        return {**state, "resultado_evaluacion": "vacio"}
    
    prompt = f"""
CRITERIOS ORIGINALES:
{json.dumps(criterios_orig, indent=2, ensure_ascii=False)}

PROPIEDADES RECOMENDADAS:
{json.dumps(resultado, indent=2, ensure_ascii=False)}

MODIFICACIONES REALIZADAS A LOS CRITERIOS:
{json.dumps(modificaciones, indent=2, ensure_ascii=False) if modificaciones else "Ninguna"}

ITERACIONES REALIZADAS: {state.get('iteracion_actual', 1)}

¿Es este resultado de suficiente calidad para presentar al usuario?
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
        
        validacion = json.loads(raw)
        veredicto = validacion.get("veredicto", "aprobado")
        score_calidad = validacion.get("score_calidad", 0.7)
        
        print(f"   {'Aprobado' if veredicto == 'aprobado' else 'Rechazado'} Veredicto: {veredicto.upper()} (calidad: {score_calidad:.0%})")
        
        for obs in validacion.get("observaciones", []):
            print(f"{obs}")
        
        for prob in validacion.get("problemas_criticos", []):
            print(f"CRÍTICO: {prob}")
        
        if veredicto == "aprobado":
            msg = validacion.get("mensaje_usuario", "")
            return {
                **state,
                "resultado_evaluacion": "aceptable",
                "explicacion_final": (state.get("explicacion_final", "") + "\n\n" + msg).strip()
            }
        else:
            return {
                **state,
                "resultado_evaluacion": "insuficiente",
                "causa_insuficiencia": f"Validador rechazó: {'; '.join(validacion.get('problemas_criticos', []))}",
            }
            
    except Exception as e:
        print(f"Error en validación: {e}. Aprobando por defecto.")
        return {**state, "resultado_evaluacion": "aceptable"}