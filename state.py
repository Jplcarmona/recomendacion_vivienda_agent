from typing import TypedDict, Optional, List, Dict, Any
from dataclasses import dataclass, field

@dataclass
class Criterios:
    """Criterios de búsqueda de vivienda."""
    region: str                        # Ej: "Medellín", "El Poblado"
    area_min: float                    # m² mínimos
    area_max: float                    # m² máximos
    precio_min: float                  # COP mínimo
    precio_max: float                  # COP máximo
    tipo_inmueble: str                 # "apartamento", "casa", "estudio"
    num_cuartos: int                   # Número de habitaciones
    num_banos: Optional[int] = None    # Número de baños
    parqueadero: bool = False          # ¿Requiere parqueadero?
    estrato: Optional[int] = None      # Estrato socioeconómico
    amenities: List[str] = field(default_factory=list)  # ["piscina", "gym", ...]

@dataclass
class Propiedad:
    """Representa una propiedad inmobiliaria encontrada."""
    id: str
    titulo: str
    precio: float
    area: float
    tipo: str
    cuartos: int
    banos: int
    direccion: str
    barrio: str
    ciudad: str
    descripcion: str
    url: Optional[str] = None
    score: float = 0.0
    razones: List[str] = field(default_factory=list)
    criterios_cumplidos: List[str] = field(default_factory=list)
    criterios_fallidos: List[str] = field(default_factory=list)

@dataclass 
class RelaxationRecord:
    """Registro de una relajación aplicada."""
    iteracion: int
    campo: str
    valor_anterior: Any
    valor_nuevo: Any
    razon: str

class SystemState(TypedDict):
    """Estado principal del sistema. Evoluciona a través del grafo."""

    #Entrada del usuario 
    input_usuario: str                         # Texto libre del usuario

    # Criterios
    criterios_originales: Optional[Dict]       # Criterios tal como llegaron (inmutables)
    criterios_actuales: Optional[Dict]         # Criterios en uso (pueden relajarse)

    # Información de zonas 
    zonas_analizadas: List[str]                # Barrios/zonas evaluadas
    info_zonas: Dict[str, Dict]                # {zona: {noticias, valoracion, etc.}}
    zonas_recomendadas: List[str]              # Zonas que pasan el filtro

    #Propiedades
    propiedades_brutas: List[Dict]             # Resultados crudos del scraping
    propiedades_filtradas: List[Dict]          # Después de aplicar criterios duros
    propiedades_evaluadas: List[Dict]          # Con score asignado

    #Evaluación
    score_umbral: float                        # Mínimo score aceptable (ej: 0.6)
    resultado_evaluacion: Optional[str]        # "aceptable" | "insuficiente" | "vacio"
    num_minimo_resultados: int                 # Mínimo de propiedades requeridas (ej: 3)

    #Iteración y relajación
    iteracion_actual: int                      # Contador de iteraciones
    max_iteraciones: int                       # Límite de ciclos (ej: 5)
    nivel_relajacion: int                      # 0=sin relajar, 1=leve, 2=moderado, 3=agresivo
    historial_relajaciones: List[Dict]         # Lista de RelaxationRecord serializados
    historial_iteraciones: List[Dict]          # Resumen de cada iteración

    #Diagnóstico
    diagnostico_fallos: List[str]              # Por qué falló la búsqueda anterior
    causa_insuficiencia: Optional[str]         # Diagnóstico del evaluador

    # Resultados finales
    resultado_final: Optional[List[Dict]]      # Propiedades recomendadas
    explicacion_final: Optional[str]           # Narrativa de cierre
    modificaciones_realizadas: List[str]       # Resumen de cambios a criterios

    #Control de flujo
    siguiente_nodo: Optional[str]              # Para routing explícito si se necesita
    error: Optional[str]                       # Mensaje de error si algo falla

def estado_inicial(input_usuario: str) -> SystemState:
    """Crea el estado inicial del sistema."""
    return SystemState(
        input_usuario=input_usuario,
        criterios_originales=None,
        criterios_actuales=None,
        zonas_analizadas=[],
        info_zonas={},
        zonas_recomendadas=[],
        propiedades_brutas=[],
        propiedades_filtradas=[],
        propiedades_evaluadas=[],
        score_umbral=0.60,
        resultado_evaluacion=None,
        num_minimo_resultados=3,
        iteracion_actual=0,
        max_iteraciones=5,
        nivel_relajacion=0,
        historial_relajaciones=[],
        historial_iteraciones=[],
        diagnostico_fallos=[],
        causa_insuficiencia=None,
        resultado_final=None,
        explicacion_final=None,
        modificaciones_realizadas=[],
        siguiente_nodo=None,
        error=None,
    )