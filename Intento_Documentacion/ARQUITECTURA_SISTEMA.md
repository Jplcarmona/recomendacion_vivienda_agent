# ARQUITECTURA DEL SISTEMA DE RECOMENDACIÓN DE VIVIENDA

## 1. DESCRIPCIÓN DE LA ARQUITECTURA DEL SISTEMA

### 1.1 Visión General

El sistema es un **agente inteligente de recomendación inmobiliaria** basado en **LangGraph** que implementa un flujo de decisión iterativo con relajación progresiva de criterios. Está diseñado específicamente para el mercado inmobiliario colombiano (Medellín y área metropolitana).

**Características principales:**
- Extracción inteligente de criterios en lenguaje natural
- Análisis contextual de zonas con noticias reales
- Búsqueda multi-fuente de propiedades (Metrocuadrado, FincaRaiz)
- Evaluación heurística con scoring ponderado
- Relajación progresiva de criterios cuando no hay suficientes resultados
- Validación final con reglas específicas del mercado colombiano
- Trazabilidad completa de todas las decisiones

### 1.2 Stack Tecnológico

```
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                 │
│  Rich (Terminal UI) - Visualización de resultados       │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE ORQUESTACIÓN                 │
│  LangGraph - Grafo de estados y enrutamiento            │
│  LangChain - Integración con LLMs                       │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE AGENTES                      │
│  7 Nodos especializados (requisitos, coordinador,       │
│  noticias, scraping, evaluador, relajación, validador) │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE HERRAMIENTAS                 │
│  Scoring | Scrapers | OpenAI Client | Parser Utils      │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE DATOS EXTERNOS               │
│  OpenAI API | NewsAPI | Google News RSS | Portales Web  │
└─────────────────────────────────────────────────────────┘
```

### 1.3 Patrones de Diseño Utilizados

1. **State Machine (Máquina de Estados)**: El grafo LangGraph implementa una máquina de estados donde cada nodo es una transición
2. **Factory Pattern**: `ScraperFactory` crea instancias de scrapers según configuración
3. **Strategy Pattern**: Diferentes estrategias de relajación según nivel
4. **Chain of Responsibility**: Fallback en búsqueda de noticias (Google RSS → NewsAPI → RSS local → Base de datos)
5. **Template Method**: `BaseScraper` define estructura, subclases implementan detalles

### 1.4 Principios Arquitectónicos

- **Separación de responsabilidades**: Cada nodo tiene una responsabilidad única y clara
- **Inmutabilidad de criterios originales**: Se preservan para auditoría y comparación
- **Trazabilidad completa**: Cada decisión se registra en historial
- **Robustez ante fallos**: Fallbacks en múltiples niveles (LLM, scrapers, APIs)
- **Configurabilidad**: Parámetros centralizados en `config.yaml`

---

## 2. DEFINICIÓN DEL ESTADO

### 2.1 Estructura del Estado (SystemState)

El estado es un `TypedDict` que evoluciona a través del grafo. Es la única fuente de verdad del sistema.

```python
class SystemState(TypedDict):
    # ENTRADA
    input_usuario: str                      # Texto libre del usuario
    
    # CRITERIOS
    criterios_originales: Optional[Dict]    # Inmutables (auditoría)
    criterios_actuales: Optional[Dict]      # Mutables (relajación)
    
    # ZONAS
    zonas_analizadas: List[str]             # Barrios evaluados
    info_zonas: Dict[str, Dict]             # {zona: {noticias, análisis}}
    zonas_recomendadas: List[str]           # Zonas priorizadas
    
    # PROPIEDADES
    propiedades_brutas: List[Dict]          # Resultados crudos scraping
    propiedades_filtradas: List[Dict]       # Después criterios duros
    propiedades_evaluadas: List[Dict]       # Con score asignado
    
    # EVALUACIÓN
    score_umbral: float                     # Mínimo score aceptable
    resultado_evaluacion: Optional[str]     # "aceptable"|"insuficiente"|"vacio"
    num_minimo_resultados: int              # Mínimo propiedades requeridas
    
    # ITERACIÓN Y RELAJACIÓN
    iteracion_actual: int                   # Contador (0-5)
    max_iteraciones: int                    # Límite de ciclos
    nivel_relajacion: int                   # 0=sin relajar, 1=leve, 2=moderado, 3=agresivo
    historial_relajaciones: List[Dict]      # Registro de cambios
    historial_iteraciones: List[Dict]       # Resumen por iteración
    
    # DIAGNÓSTICO
    diagnostico_fallos: List[str]           # Por qué falló búsqueda anterior
    causa_insuficiencia: Optional[str]      # Diagnóstico del evaluador
    
    # RESULTADOS FINALES
    resultado_final: Optional[List[Dict]]   # Top 5 propiedades
    explicacion_final: Optional[str]        # Narrativa de cierre
    modificaciones_realizadas: List[str]    # Resumen de cambios
    
    # CONTROL
    siguiente_nodo: Optional[str]           # Routing explícito
    error: Optional[str]                    # Mensaje de error
```

### 2.2 Estructura de Criterios

```python
{
    "region": "Medellín",                   # Ciudad/barrio principal
    "regiones": ["El Poblado", "Laureles"], # Opciones del usuario
    "area_min": 70,                         # m² mínimos
    "area_max": 200,                        # m² máximos
    "precio_min": 200_000_000,              # COP mínimo
    "precio_max": 400_000_000,              # COP máximo
    "tipo_inmueble": "apartamento",         # apartamento|casa|estudio|local
    "num_cuartos": 2,                       # Habitaciones mínimas
    "num_banos": 2,                         # Baños mínimos (opcional)
    "parqueadero": true,                    # ¿Requiere?
    "estrato": null,                        # 1-6 o null
    "amenities": ["piscina", "gym"]         # Servicios deseados
}
```

### 2.3 Estructura de Propiedad

```python
{
    "id": "MQ-12345",                       # ID único
    "titulo": "Apartamento en El Poblado",
    "precio": 350_000_000,                  # COP
    "area": 85,                             # m²
    "cuartos": 3,
    "banos": 2,
    "barrio": "El Poblado",
    "ciudad": "Medellín",
    "url": "https://...",
    "score": 0.82,                          # 0-1
    "razones": ["precio dentro del rango", "área cumple"],
    "criterios_cumplidos": ["precio", "área", "cuartos"],
    "criterios_fallidos": [],
    "parqueadero": true,
    "fuente": "Metrocuadrado"
}
```

### 2.4 Estructura de Información de Zona

```python
{
    "El Poblado": {
        "estrato_promedio": 6,
        "precio_m2_promedio": 8_500_000,
        "seguridad": "alta",
        "valorización_anual": "8%",
        "noticias_recientes": [
            {
                "titulo": "Nuevos proyectos en El Poblado",
                "descripcion": "...",
                "fecha": "2024-05-20",
                "fuente": "Google News",
                "categoria": "valorizacion"
            }
        ],
        "analisis": {
            "compatibilidad": 0.85,         # 0-1
            "recomendacion": "alta",        # alta|media|baja
            "resumen": "Zona de alta compatibilidad...",
            "fortalezas": ["seguridad", "comercio"],
            "debilidades": ["precio alto"],
            "alerta_seguridad": null,
            "oportunidad": "Proyectos de valorización"
        }
    }
}
```

---

## 3. DIAGRAMA DEL GRAFO PROPUESTO

### 3.1 Grafo de Flujo Completo

```
                    ┌─────────────────────────────────────┐
                    │   ENTRADA: input_usuario            │
                    └──────────────┬──────────────────────┘
                                   ↓
                    ┌─────────────────────────────────────┐
                    │  [1] ASISTENTE DE REQUISITOS        │
                    │  Extrae criterios del texto libre   │
                    │  Output: criterios_originales       │
                    │          criterios_actuales         │
                    └──────────────┬──────────────────────┘
                                   ↓
                    ┌─────────────────────────────────────┐
                    │  [2] COORDINADOR                    │
                    │  Define zonas de búsqueda           │
                    │  Output: zonas_recomendadas         │
                    └──────────────┬──────────────────────┘
                                   ↓
                    ┌─────────────────────────────────────┐
                    │  [3] AGENTE DE NOTICIAS             │
                    │  Busca noticias y analiza zonas     │
                    │  Output: info_zonas (con análisis)  │
                    └──────────────┬──────────────────────┘
                                   ↓
                    ┌─────────────────────────────────────┐
                    │  [4] PROPIEDADES SCRAPING           │
                    │  Busca en portales inmobiliarios    │
                    │  Output: propiedades_filtradas      │
                    └──────────────┬──────────────────────┘
                                   ↓
                    ┌─────────────────────────────────────┐
                    │  [5] EVALUADOR                      │
                    │  Califica propiedades (scoring)     │
                    │  Output: propiedades_evaluadas      │
                    │          resultado_evaluacion       │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ↓                             ↓
        ┌─────────────────────┐    ┌──────────────────────┐
        │ ¿Resultado          │    │ ¿Iteraciones        │
        │ aceptable?          │    │ < max?              │
        │ (≥1 prop score≥0.45)│    │                     │
        └──────────┬──────────┘    └──────────┬───────────┘
                   │                          │
            SÍ ────┼──────────────────────────┼──── NO
                   │                          │
                   ↓                          ↓
        ┌─────────────────────┐    ┌──────────────────────┐
        │  [7] VALIDADOR      │    │  FIN POR LÍMITE      │
        │  Validación final   │    │  (sin resultados)    │
        │  Output: resultado_ │    └──────────────────────┘
        │          evaluacion │
        └──────────┬──────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ↓                     ↓
    ┌─────────────┐    ┌──────────────────┐
    │ APROBADO    │    │ RECHAZADO        │
    │ FIN EXITOSO │    │ ¿Iteraciones<max?│
    └─────────────┘    └────────┬─────────┘
                                │
                        ┌───────┴────────┐
                        │                │
                    SÍ  ↓            NO  ↓
                    ┌────────┐    ┌──────────────┐
                    │ [6]    │    │ FIN POR      │
                    │RELAJAR │    │ LÍMITE       │
                    └────┬───┘    └──────────────┘
                         │
                         ↓
                    ┌──────────┐
                    │ [2] COORD│ (nueva iteración)
                    └──────────┘
```

### 3.2 Tabla de Transiciones

| Nodo Actual | Condición | Nodo Siguiente | Acción |
|-------------|-----------|----------------|--------|
| Asistente | Siempre | Coordinador | Pasar criterios |
| Coordinador | Siempre | Agente Noticias | Pasar zonas |
| Agente Noticias | Siempre | Scraping | Pasar info_zonas |
| Scraping | Siempre | Evaluador | Pasar propiedades |
| Evaluador | resultado="aceptable" | Validador | Validar resultado |
| Evaluador | resultado="insuficiente" ∧ iter<max | Relajación | Relajar criterios |
| Evaluador | iter≥max | FIN | Terminar |
| Validador | veredicto="aprobado" | FIN | Éxito |
| Validador | veredicto="rechazado" ∧ iter<max | Relajación | Relajar más |
| Validador | veredicto="rechazado" ∧ iter≥max | FIN | Terminar |
| Relajación | Siempre | Coordinador | Nueva búsqueda |

---

## 4. DESCRIPCIÓN DE LAS ACTIVIDADES Y SU IMPLEMENTACIÓN

### 4.1 Nodo 1: Asistente de Requisitos

**Responsabilidad**: Extraer y estructurar criterios del texto libre del usuario

**Entrada**: `input_usuario` (texto libre)

**Proceso**:
1. Usa GPT-4o con prompt especializado para parsear preferencias
2. Extrae campos: región, área, precio, tipo, cuartos, baños, parqueadero, estrato, amenities
3. Valida que `precio_max > precio_min` y `area_max > area_min`
4. Maneja fallback a criterios por defecto si falla el parsing JSON

**Salida**: 
- `criterios_originales`: Copia inmutable para auditoría
- `criterios_actuales`: Copia mutable para relajación

**Ejemplo**:
```
Input: "Busco apto en El Poblado, máximo 400 millones, 2 habitaciones"
Output: {
  "region": "El Poblado",
  "regiones": ["El Poblado"],
  "precio_max": 400_000_000,
  "num_cuartos": 2,
  "area_min": 40,
  "area_max": 200,
  ...
}
```

**Código relevante**: `nodes/n1_asistente_requisitos.py`

---

### 4.2 Nodo 2: Coordinador

**Responsabilidad**: Definir zonas de búsqueda priorizadas

**Entrada**: Criterios actuales + información de zonas disponible

**Proceso**:
1. Usa GPT-4o-mini para analizar criterios e información de contexto
2. Genera lista de 3-5 zonas en orden de relevancia
3. Considera: tipo de inmueble, precio, estrato, noticias recientes
4. Registra cada iteración en `historial_iteraciones`
5. **Garantía**: Las zonas preferidas del usuario SIEMPRE se incluyen

**Salida**: 
- `zonas_recomendadas`: Lista priorizada
- `zonas_analizadas`: Acumula todas las zonas vistas

**Lógica de priorización**:
- Estrato compatible con precio
- Noticias positivas de valorización
- Seguridad histórica
- Servicios y comercio

**Código relevante**: `nodes/n2_coordinador.py`

---

### 4.3 Nodo 3: Agente de Noticias

**Responsabilidad**: Buscar noticias reales y analizar compatibilidad de zonas

**Entrada**: Zonas recomendadas + criterios

**Proceso**:
1. **Búsqueda de noticias** (en orden de preferencia):
   - Google News RSS (categorizado: valorización, seguridad, movilidad, etc.)
   - NewsAPI (fallback)
   - RSS de El Colombiano/El Tiempo (fallback)
   - Base de datos estática de zonas (fallback final)

2. **Análisis con LLM**:
   - Usa GPT-4o-mini para evaluar compatibilidad (0-1)
   - Considera: noticias recientes, datos históricos, criterios del usuario
   - Genera: fortalezas, debilidades, alertas de seguridad, oportunidades

3. **Almacenamiento**:
   - `info_zonas[zona]` = {datos_base, noticias, análisis}

**Salida**: `info_zonas` poblado con análisis de cada zona

**Base de datos estática** (fallback):
- El Poblado: estrato 6, $8.5M/m², seguridad alta
- Laureles: estrato 5, $6.2M/m², seguridad alta
- Belén: estrato 3, $4M/m², seguridad media
- (+ 8 zonas más)

**Código relevante**: `nodes/n3_agente_noticias.py`

---

### 4.4 Nodo 4: Propiedades Scraping

**Responsabilidad**: Obtener propiedades de portales inmobiliarios

**Entrada**: Criterios actuales + zonas recomendadas

**Proceso**:
1. Itera sobre cada zona recomendada
2. Para cada zona, ejecuta scrapers habilitados (Metrocuadrado, FincaRaiz)
3. Elimina duplicados por URL
4. Modo simulado para testing (devuelve propiedades mock)

**Salida**: 
- `propiedades_brutas`: Resultados crudos
- `propiedades_filtradas`: Copia para evaluación

**Scrapers disponibles**:
- MetrocuadradoScraper
- FincaRaizScraper

**Código relevante**: `nodes/n4_propiedades_scraping.py`

---

### 4.5 Nodo 5: Evaluador

**Responsabilidad**: Calificar propiedades y decidir si hay suficientes resultados

**Entrada**: Propiedades filtradas + criterios + info de zonas

**Proceso**:
1. **Scoring heurístico** (función `calcular_score`):
   - Precio (30%): Mejor score cuanto más alejado del techo
   - Área (25%): Bonus proporcional al área extra
   - Cuartos (20%): Exacto o superior
   - Baños (10%): Si se requieren
   - Parqueadero (10%): Si se requiere
   - URL verificable (5%)

2. **Bonus por zona**:
   - +5% si zona tiene compatibilidad "alta"
   - -10% si zona tiene alertas de seguridad

3. **Decisión**:
   - Si ≥1 propiedad con score ≥0.45 → "aceptable"
   - Si ≥3 propiedades (cualquier score) → "aceptable"
   - Si no → "insuficiente"

4. **Explicación narrativa**:
   - Usa GPT-4o para generar análisis considerando propiedades + contexto de zonas

**Salida**: 
- `propiedades_evaluadas`: Ordenadas por score
- `resultado_evaluacion`: "aceptable" | "insuficiente" | "vacio"
- `resultado_final`: Top 5 propiedades
- `explicacion_final`: Narrativa

**Código relevante**: `nodes/n5_evaluador.py`

---

### 4.6 Nodo 6: Relajación

**Responsabilidad**: Modificar criterios de forma gradual y trazable

**Entrada**: Criterios actuales + nivel de relajación + causa de fallo

**Proceso**:
1. **Niveles de relajación**:
   - Nivel 1 (leve): +10-15% precio_max O +10m² área_max
   - Nivel 2 (moderado): +20% precio_max O -1 cuarto O ampliar tipo
   - Nivel 3 (agresivo): +20% precio_max Y -1 cuarto

2. **Orden de prioridad**:
   - Precio → Área → Cuartos → Parqueadero → Estrato → Tipo → Región

3. **Documentación**:
   - Cada cambio se registra en `historial_relajaciones`
   - Se mantiene `criterios_originales` intacto

4. **Fallback manual**:
   - Si falla el LLM, aplica relajación manual predefinida

**Salida**: 
- `criterios_actuales`: Modificados
- `nivel_relajacion`: Incrementado
- `historial_relajaciones`: Actualizado
- Propiedades limpiadas para nueva búsqueda

**Código relevante**: `nodes/n6_relajacion.py`

---

### 4.7 Nodo 7: Validador WhatsApp

**Responsabilidad**: Validación final de coherencia y calidad

**Entrada**: Resultado final + criterios originales + modificaciones

**Proceso**:
1. **Reglas de validación**:
   - ✅ Más cuartos que lo requerido = positivo
   - ✅ Parqueadero no confirmado = NO es problema (limitación de portales)
   - ✅ Precio hasta 10% sobre máximo = aceptable
   - ❌ Rechaza solo si >50% propiedades están claramente sobre precio
   - ❌ Rechaza si no cumplen área/cuartos básicos

2. **Evaluación**:
   - Score de calidad (0-1)
   - Observaciones constructivas
   - Problemas críticos (si los hay)

3. **Decisión**:
   - Si aprobado → `resultado_evaluacion = "aceptable"` → FIN
   - Si rechazado → `resultado_evaluacion = "insuficiente"` → Relajación

**Salida**: 
- `resultado_evaluacion`: "aceptable" | "insuficiente"
- `explicacion_final`: Actualizada con mensaje del validador

**Código relevante**: `nodes/n7_validador_whatsapp.py`



---

## 5. ESTRATEGIA DE RELAJACIÓN DE CONDICIONES

### 5.1 Filosofía de Relajación

La relajación es un mecanismo de **adaptación progresiva** que permite al sistema encontrar soluciones cuando los criterios iniciales son demasiado restrictivos. No es un fracaso, sino una estrategia inteligente de búsqueda.

**Principios**:
1. **Gradualidad**: Cambios pequeños y medibles en cada iteración
2. **Trazabilidad**: Cada cambio se documenta con razón clara
3. **Reversibilidad**: Los criterios originales se preservan para auditoría
4. **Inteligencia**: Prioriza cambios que menos afectan la experiencia del usuario

### 5.2 Niveles de Relajación

```
NIVEL 0 (Sin relajación)
├─ Criterios originales sin cambios
└─ Primera búsqueda

NIVEL 1 (Relajación leve)
├─ Precio máximo: +10-15%
│  Ejemplo: $400M → $460M
├─ O Área mínima: -10m²
│  Ejemplo: 70m² → 60m²
└─ Impacto: Bajo, usuario probablemente aceptaría

NIVEL 2 (Relajación moderada)
├─ Precio máximo: +20%
│  Ejemplo: $400M → $480M
├─ O Número de cuartos: -1
│  Ejemplo: 3 cuartos → 2 cuartos
├─ O Ampliar tipo de inmueble
│  Ejemplo: Solo apartamento → Apartamento o estudio
└─ Impacto: Moderado, requiere consideración del usuario

NIVEL 3 (Relajación agresiva)
├─ Precio máximo: +20% Y Cuartos: -1
│  Ejemplo: $400M + 3 cuartos → $480M + 2 cuartos
├─ O Cambiar zona de búsqueda
│  Ejemplo: El Poblado → Laureles + Belén
└─ Impacto: Alto, cambio significativo en búsqueda
```

### 5.3 Orden de Prioridad de Relajación

```python
ORDEN_RELAJACION = [
    "precio_max",           # 1. Precio (menos impacto en experiencia)
    "area_min",             # 2. Área mínima
    "num_cuartos",          # 3. Número de cuartos
    "parqueadero",          # 4. Parqueadero
    "estrato",              # 5. Estrato socioeconómico
    "tipo_inmueble",        # 6. Tipo de inmueble
    "region"                # 7. Región (máximo impacto)
]
```

**Justificación**:
- **Precio**: Flexible, usuario puede encontrar mejor valor
- **Área**: Menos crítica que cuartos
- **Cuartos**: Afecta funcionalidad pero menos que zona
- **Parqueadero**: Amenidad, no necesidad básica
- **Estrato**: Afecta seguridad/servicios
- **Tipo**: Cambio fundamental (apto vs casa)
- **Región**: Cambio más drástico, último recurso

### 5.4 Algoritmo de Relajación

```
ENTRADA: criterios_actuales, nivel_relajacion, causa_insuficiencia
SALIDA: criterios_nuevos, historial_cambios

1. Determinar qué campo relajar según nivel y orden de prioridad
2. Calcular nuevo valor según nivel:
   - Nivel 1: Cambio pequeño (10-15%)
   - Nivel 2: Cambio moderado (20%)
   - Nivel 3: Cambio agresivo (20% + cambio adicional)
3. Validar que nuevo valor sea razonable
4. Registrar cambio en historial con razón
5. Limpiar propiedades para nueva búsqueda
6. Retornar criterios_nuevos
```

### 5.5 Ejemplo de Relajación Progresiva

**Caso**: Usuario busca apartamento en El Poblado, máximo $400M, 3 cuartos, 70m²

```
ITERACIÓN 1 (Nivel 0 - Sin relajación)
├─ Criterios: $400M, 3 cuartos, 70m²
├─ Resultado: 0 propiedades encontradas
└─ Decisión: Relajar

ITERACIÓN 2 (Nivel 1 - Relajación leve)
├─ Cambio: Precio $400M → $460M (+15%)
├─ Criterios: $460M, 3 cuartos, 70m²
├─ Resultado: 2 propiedades encontradas
├─ Score: 0.35, 0.42 (ambas < 0.45)
└─ Decisión: Relajar más

ITERACIÓN 3 (Nivel 2 - Relajación moderada)
├─ Cambio: Cuartos 3 → 2 (-1)
├─ Criterios: $460M, 2 cuartos, 70m²
├─ Resultado: 8 propiedades encontradas
├─ Top scores: 0.78, 0.72, 0.68
└─ Decisión: ACEPTABLE ✓

RESULTADO FINAL
├─ Iteraciones: 3
├─ Modificaciones: 2 (precio +15%, cuartos -1)
├─ Propiedades recomendadas: 5
└─ Explicación: "Se encontraron excelentes opciones con 2 cuartos..."
```

### 5.6 Protecciones contra Relajación Excesiva

```python
# Límites máximos de relajación
MAX_RELAJACION_PRECIO = 1.5          # No más de 50% sobre original
MAX_RELAJACION_AREA = 0.5            # No menos de 50% del original
MIN_CUARTOS = 1                      # Nunca menos de 1 cuarto
MAX_ITERACIONES = 5                  # Máximo 5 ciclos

# Validación en cada relajación
if criterios_nuevos["precio_max"] > criterios_originales["precio_max"] * MAX_RELAJACION_PRECIO:
    criterios_nuevos["precio_max"] = criterios_originales["precio_max"] * MAX_RELAJACION_PRECIO
    
if criterios_nuevos["area_min"] < criterios_originales["area_min"] * MAX_RELAJACION_AREA:
    criterios_nuevos["area_min"] = criterios_originales["area_min"] * MAX_RELAJACION_AREA
```

---

## 6. EJEMPLO DE EJECUCIÓN

### 6.1 Caso de Prueba Completo

**Input del usuario**:
```
Busco apartamento en Medellín, idealmente en el Estadio o en El Poblado o Aranjuez.
Máximo 400 millones de pesos. Necesito al menos 2 habitaciones y 2 baños.
Área mínima de 70 metros cuadrados. Sería ideal que tuviera parqueadero.
Somos una familia de 3 personas.
```

### 6.2 Ejecución Paso a Paso

#### PASO 1: Asistente de Requisitos

```
[Nodo 1] Interpretando requisitos del usuario...

Criterios extraídos:
├─ Región: Medellín
├─ Regiones: ["Estadio", "El Poblado", "Aranjuez"]
├─ Precio: $200M - $400M
├─ Área: 70-200 m²
├─ Tipo: apartamento
├─ Cuartos: 2
├─ Baños: 2
├─ Parqueadero: true
└─ Amenities: []

✓ Criterios validados
```

#### PASO 2: Coordinador

```
[Nodo 2] Coordinando zonas de búsqueda (iteración 1)...

Análisis LLM:
├─ Precio $400M compatible con: Estadio, Aranjuez, Belén
├─ Preferencias usuario: Estadio, El Poblado, Aranjuez
├─ Noticias recientes: Estadio con proyectos nuevos
└─ Estrategia: Priorizar Estadio, incluir El Poblado como premium

Zonas priorizadas: ["Estadio", "Aranjuez", "El Poblado", "Belén"]
```

#### PASO 3: Agente de Noticias

```
[Nodo 3] Buscando noticias reales de zonas...

Estadio:
├─ Google News: 5 artículos encontrados
├─ Temas: Nuevos proyectos, metro, comercio
├─ Compatibilidad: 0.78 (alta)
└─ Oportunidad: "Proyectos de valorización en zona"

El Poblado:
├─ Google News: 8 artículos encontrados
├─ Temas: Seguridad, comercio, turismo
├─ Compatibilidad: 0.85 (alta)
└─ Alerta: "Algunos incidentes aislados de seguridad"

Aranjuez:
├─ Google News: 3 artículos encontrados
├─ Temas: Movilidad, servicios
├─ Compatibilidad: 0.65 (media)
└─ Nota: "Zona en desarrollo"

Belén:
├─ Base de datos: Datos históricos
├─ Compatibilidad: 0.72 (media-alta)
└─ Nota: "Buena relación precio-servicios"
```

#### PASO 4: Propiedades Scraping

```
[Nodo 4] Iniciando scraping de propiedades...

Buscando en zona: Estadio
├─ Metrocuadrado [Estadio]: 12 propiedades
├─ FincaRaiz [Estadio]: 8 propiedades
└─ Únicas: 18 propiedades

Buscando en zona: Aranjuez
├─ Metrocuadrado [Aranjuez]: 15 propiedades
├─ FincaRaiz [Aranjuez]: 10 propiedades
└─ Únicas: 22 propiedades

Buscando en zona: El Poblado
├─ Metrocuadrado [El Poblado]: 25 propiedades
├─ FincaRaiz [El Poblado]: 18 propiedades
└─ Únicas: 38 propiedades

Buscando en zona: Belén
├─ Metrocuadrado [Belén]: 8 propiedades
├─ FincaRaiz [Belén]: 6 propiedades
└─ Únicas: 12 propiedades

Total únicas: 90 propiedades
```

#### PASO 5: Evaluador

```
[Nodo 5] Evaluando propiedades...

TOP PROPIEDADES:
[██████████] 0.89 | Apartamento moderno en Estadio, 85m², 2 cuartos
[█████████░] 0.85 | Apto El Poblado, 92m², 3 cuartos, parqueadero
[█████████░] 0.82 | Apartamento Aranjuez, 78m², 2 cuartos, 2 baños
[████████░░] 0.78 | Apto Belén, 88m², 2 cuartos, parqueadero
[████████░░] 0.76 | Apartamento Estadio, 75m², 2 cuartos, 1 baño

Decisión: ACEPTABLE ✓
Propiedades aceptables: 15 (score ≥ 0.45)

Explicación generada:
"Se encontraron excelentes opciones en Estadio y El Poblado que cumplen
perfectamente con sus criterios. La zona del Estadio ofrece buena relación
precio-servicios con proyectos de valorización. El Poblado mantiene su
posición premium con seguridad alta y servicios completos. Recomendamos
considerar también Aranjuez como alternativa con mejor precio..."
```

#### PASO 6: Validador

```
[Nodo 7] Validación final del resultado...

Verificación:
├─ Criterios obligatorios: ✓ Cumplidos
├─ Diversidad de zonas: ✓ 4 zonas representadas
├─ Scores razonables: ✓ Rango 0.76-0.89
├─ Parqueadero: ✓ 8 de 15 tienen confirmado
└─ Precio: ✓ Todos dentro de rango

Veredicto: APROBADO ✓
Score de calidad: 0.92

Observaciones:
- Excelente diversidad de opciones
- Precios competitivos en todas las zonas
- Buena representación de preferencias del usuario
```

#### RESULTADO FINAL

```
╔════════════════════════════════════════════════════════════════╗
║  SISTEMA DE RECOMENDACIÓN DE VIVIENDA — RESULTADO FINAL       ║
╚════════════════════════════════════════════════════════════════╝

Resumen del proceso:
├─ Iteraciones realizadas: 1
├─ Nivel de relajación aplicado: 0 (sin relajación)
└─ Estado final: ACEPTABLE

Top 5 propiedades recomendadas:

#1 [██████████] 0.89 | Apartamento moderno en Estadio
   Precio: $350M COP
   Área: 85 m²
   Cuartos: 2 | Baños: 2
   Ubicación: Estadio, Medellín
   Cumple: precio, área, cuartos, baños, parqueadero
   Link: https://metrocuadrado.com/...

#2 [█████████░] 0.85 | Apto El Poblado con vista
   Precio: $380M COP
   Área: 92 m²
   Cuartos: 3 | Baños: 2
   Ubicación: El Poblado, Medellín
   Cumple: precio, área, cuartos, baños, parqueadero
   Link: https://fincaraiz.com.co/...

#3 [█████████░] 0.82 | Apartamento Aranjuez
   Precio: $320M COP
   Área: 78 m²
   Cuartos: 2 | Baños: 2
   Ubicación: Aranjuez, Medellín
   Cumple: precio, área, cuartos, baños
   Link: https://metrocuadrado.com/...

#4 [████████░░] 0.78 | Apto Belén con parqueadero
   Precio: $280M COP
   Área: 88 m²
   Cuartos: 2 | Baños: 2
   Ubicación: Belén, Medellín
   Cumple: precio, área, cuartos, baños, parqueadero
   Link: https://fincaraiz.com.co/...

#5 [████████░░] 0.76 | Apartamento Estadio
   Precio: $340M COP
   Área: 75 m²
   Cuartos: 2 | Baños: 1
   Ubicación: Estadio, Medellín
   Cumple: precio, área, cuartos
   No cumple: baños (1 vs 2 requeridos)
   Link: https://metrocuadrado.com/...

╔════════════════════════════════════════════════════════════════╗
║  Análisis del asesor                                          ║
╚════════════════════════════════════════════════════════════════╝

Se encontraron excelentes opciones que se alinean perfectamente con
sus criterios. La zona del Estadio emerge como la mejor relación
precio-servicios, con proyectos de valorización en curso. El Poblado
mantiene su posición premium con seguridad alta y servicios completos.

Recomendamos considerar también Aranjuez como alternativa con mejor
precio y Belén como opción económica sin sacrificar calidad. Todas
las propiedades cumplen con sus requisitos básicos de 2 habitaciones,
2 baños y área mínima de 70m².

La mayoría de propiedades incluyen parqueadero, lo cual es un plus
importante para su familia. Sugerimos contactar directamente con los
asesores para confirmar detalles y agendar visitas.
```

---

## 7. REFLEXIÓN CRÍTICA

### 7.1 Fortalezas del Sistema

#### 1. **Inteligencia Contextual**
- Integra noticias reales de zonas (Google News, NewsAPI)
- Considera seguridad, valorización, movilidad, calidad de vida
- Análisis dinámico que se adapta a cambios del mercado

#### 2. **Adaptabilidad Progresiva**
- Relajación inteligente de criterios cuando no hay resultados
- Cada cambio es documentado y reversible
- Máximo 5 iteraciones evita búsquedas infinitas

#### 3. **Trazabilidad Completa**
- Historial de todas las decisiones
- Criterios originales preservados para auditoría
- Modificaciones realizadas documentadas con razones

#### 4. **Robustez ante Fallos**
- Múltiples niveles de fallback (LLM, scrapers, APIs)
- Base de datos estática de zonas como último recurso
- Manejo graceful de errores en cada nodo

#### 5. **Validación Rigurosa**
- Dos niveles de validación (Evaluador + Validador)
- Reglas específicas para mercado colombiano
- Manejo inteligente de datos incompletos

#### 6. **Experiencia de Usuario**
- Explicaciones narrativas generadas por LLM
- Visualización clara de resultados con Rich
- Información sobre por qué se relajaron criterios

### 7.2 Limitaciones y Desafíos

#### 1. **Dependencia de APIs Externas**
- **Problema**: NewsAPI y Google News pueden no estar disponibles
- **Impacto**: Fallback a base de datos estática (menos actualizado)
- **Solución**: Caché local de noticias, múltiples fuentes

#### 2. **Calidad del Scraping**
- **Problema**: Portales inmobiliarios cambian estructura HTML
- **Impacto**: Scrapers pueden fallar o devolver datos incompletos
- **Solución**: Usar APIs oficiales si están disponibles, monitoring de cambios

#### 3. **Limitaciones del Scoring Heurístico**
- **Problema**: Pesos fijos (30% precio, 25% área, etc.) pueden no ser óptimos
- **Impacto**: Propiedades con buen score pueden no ser ideales
- **Solución**: Machine learning para aprender pesos óptimos

#### 4. **Contexto Limitado del LLM**
- **Problema**: GPT-4o-mini tiene contexto limitado
- **Impacto**: Análisis de zonas puede ser superficial con muchas noticias
- **Solución**: Resumen previo de noticias, usar GPT-4o para análisis complejos

#### 5. **Falta de Feedback del Usuario**
- **Problema**: Sistema no aprende de preferencias del usuario
- **Impacto**: Recomendaciones pueden no mejorar con el tiempo
- **Solución**: Agregar feedback loop, guardar preferencias

#### 6. **Relajación Puede Ser Excesiva**
- **Problema**: Después de 5 iteraciones, criterios pueden estar muy relajados
- **Impacto**: Propiedades finales pueden no satisfacer al usuario
- **Solución**: Límites máximos de relajación, alertas al usuario

### 7.3 Mejoras Futuras

#### Corto Plazo (1-2 semanas)
1. **Caché de noticias**: Guardar noticias localmente para reducir llamadas a APIs
2. **Logging mejorado**: Registrar todas las decisiones para debugging
3. **Validación de scrapers**: Tests automáticos para detectar cambios en portales
4. **Feedback del usuario**: Agregar endpoint para que usuario califique recomendaciones

#### Mediano Plazo (1-2 meses)
1. **Machine Learning**: Aprender pesos óptimos de scoring basado en feedback
2. **APIs oficiales**: Integrar APIs de Metrocuadrado y FincaRaiz si están disponibles
3. **Análisis de tendencias**: Detectar patrones de valorización por zona
4. **Recomendaciones personalizadas**: Guardar preferencias del usuario para futuras búsquedas

#### Largo Plazo (3-6 meses)
1. **Predicción de precios**: Modelo de ML para predecir evolución de precios
2. **Análisis de riesgo**: Evaluar riesgo de inversión por zona
3. **Integración con WhatsApp**: Enviar recomendaciones directamente a WhatsApp
4. **Análisis de vecindario**: Información detallada de servicios, transporte, etc.

### 7.4 Consideraciones Éticas

#### 1. **Sesgo en Recomendaciones**
- **Riesgo**: Sistema podría favorecer ciertas zonas o tipos de propiedad
- **Mitigación**: Auditar scores, incluir diversidad de opciones, transparencia en criterios

#### 2. **Privacidad del Usuario**
- **Riesgo**: Guardar preferencias de vivienda es información sensible
- **Mitigación**: Encriptación, consentimiento explícito, política de privacidad clara

#### 3. **Información Incompleta**
- **Riesgo**: Datos de scrapers pueden ser inexactos o desactualizados
- **Mitigación**: Advertencias claras, recomendación de verificar directamente

#### 4. **Impacto en Mercado Inmobiliario**
- **Riesgo**: Scraping masivo podría afectar portales
- **Mitigación**: Respetar robots.txt, delays entre requests, contactar portales

### 7.5 Conclusiones

El sistema de recomendación de vivienda es una **solución robusta y bien arquitecturada** que demuestra cómo los agentes LLM pueden resolver problemas complejos del mundo real. Sus principales fortalezas son:

1. **Arquitectura modular**: Cada nodo tiene responsabilidad clara
2. **Inteligencia contextual**: Integra múltiples fuentes de información
3. **Adaptabilidad**: Relajación progresiva permite encontrar soluciones
4. **Trazabilidad**: Todas las decisiones son auditables

Sin embargo, hay oportunidades de mejora en:

1. **Aprendizaje**: Incorporar feedback del usuario
2. **Escalabilidad**: Optimizar para búsquedas masivas
3. **Precisión**: Mejorar scoring con ML
4. **Integración**: Conectar con APIs oficiales

En conclusión, este es un **prototipo excelente** que puede evolucionar hacia una **plataforma de recomendación de viviendas de clase mundial** con las mejoras sugeridas.

---

## 8. REFERENCIAS Y RECURSOS

### Archivos del Proyecto
- `graph.py`: Definición del grafo LangGraph
- `state.py`: Definición del estado del sistema
- `main.py`: Punto de entrada y visualización
- `nodes/`: Implementación de los 7 nodos
- `tools/`: Herramientas auxiliares (scoring, scrapers, etc.)
- `config/config.yaml`: Configuración centralizada

### Dependencias Principales
- **LangGraph**: Orquestación de flujos
- **LangChain**: Integración con LLMs
- **OpenAI**: GPT-4o y GPT-4o-mini
- **Selenium**: Web scraping
- **Rich**: Visualización en terminal
- **NewsAPI**: Búsqueda de noticias

### Documentación Relacionada
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Documentation](https://python.langchain.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [NewsAPI Documentation](https://newsapi.org/docs)

