import os
from langgraph.graph import StateGraph, END
from state import SystemState

from nodes.n1_asistente_requisitos import nodo_asistente_requisitos
from nodes.n2_coordinador import nodo_coordinador
from nodes.n3_agente_noticias import nodo_agente_noticias
from nodes.n4_propiedades_scraping import nodo_propiedades_scraping
from nodes.n5_evaluador import nodo_evaluador
from nodes.n6_relajacion import nodo_relajacion
from nodes.n7_validador_whatsapp import nodo_validador_whatsapp

# Funciones de enrutamiento (aristas condicionales)

def router_post_evaluacion(state: SystemState) -> str:
    """
    Decide qué hacer después del Evaluador:
    - Si el resultado es aceptable → Validador
    - Si no hay resultados y se puede iterar → Relajación  
    - Si se agotaron los intentos → Fin
    """
    evaluacion = state.get("resultado_evaluacion")
    iteracion = state.get("iteracion_actual", 0)
    max_iter = state.get("max_iteraciones", 5)
    
    if evaluacion == "aceptable":
        print(f"\n Router: Resultado aceptable. Enviando a validación final.")
        return "validar"
    
    if iteracion >= max_iter:
        print(f"\n Router: Límite de {max_iter} iteraciones alcanzado. Terminando.")
        return "fin_por_limite"
    
    print(f"\n Router: Resultado insuficiente. Enviando a relajación (iter {iteracion}/{max_iter}).")
    return "relajar"

def router_post_validacion(state: SystemState) -> str:
    """
    Decide qué hacer después del Validador:
    - Si aprobó → Fin exitoso
    - Si rechazó y quedan iteraciones → Relajar más
    - Si rechazó y no quedan → Fin por límite
    """
    evaluacion = state.get("resultado_evaluacion")
    iteracion = state.get("iteracion_actual", 0)
    max_iter = state.get("max_iteraciones", 5)
    
    if evaluacion == "aceptable":
        return "fin_exitoso"
    
    if iteracion >= max_iter:
        return "fin_por_limite"
    
    return "relajar"

def router_post_relajacion(state: SystemState) -> str:
    """Siempre vuelve al coordinador después de relajar."""
    return "coordinador"

# Construcción del Grafo 

def construir_grafo() -> StateGraph:
    """Construye y compila el grafo de decisión del sistema."""
    
    grafo = StateGraph(SystemState)
    
    # Agregar nodos
    grafo.add_node("asistente_requisitos", nodo_asistente_requisitos)
    grafo.add_node("agente_noticias", nodo_agente_noticias)
    grafo.add_node("coordinador", nodo_coordinador)
    grafo.add_node("scraping", nodo_propiedades_scraping)
    grafo.add_node("evaluador", nodo_evaluador)
    grafo.add_node("relajacion", nodo_relajacion)
    grafo.add_node("validador", nodo_validador_whatsapp)
    
    # Definir punto de entrada
    grafo.set_entry_point("asistente_requisitos")
    
    # Aristas directas (sin condición)
    grafo.add_edge("asistente_requisitos", "coordinador")
    grafo.add_edge("coordinador", "agente_noticias")
    grafo.add_edge("agente_noticias", "scraping")
    grafo.add_edge("scraping", "evaluador")
    
    # Aristas condicionales
    grafo.add_conditional_edges(
        "evaluador",
        router_post_evaluacion,
        {
            "validar": "validador",
            "relajar": "relajacion",
            "fin_por_limite": END
        }
    )
    
    grafo.add_conditional_edges(
        "validador",
        router_post_validacion,
        {
            "fin_exitoso": END,
            "relajar": "relajacion",
            "fin_por_limite": END
        }
    )
    
    grafo.add_conditional_edges(
        "relajacion",
        router_post_relajacion,
        {
            "coordinador": "coordinador"
        }
    )
    
    # Compilar 
    app = grafo.compile()
    
    print("Grafo compilado exitosamente.")
    print("Nodos:", ["asistente_requisitos", "agente_noticias", "coordinador", 
                        "scraping", "evaluador", "relajacion", "validador"])
    
    return app