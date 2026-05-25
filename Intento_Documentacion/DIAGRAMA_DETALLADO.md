# DIAGRAMA DETALLADO DEL SISTEMA

## 1. ARQUITECTURA EN CAPAS

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CAPA DE PRESENTACIÓN                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Rich Console - Visualización de resultados en terminal      │  │
│  │  - Paneles con propiedades recomendadas                      │  │
│  │  - Tablas de comparación                                     │  │
│  │  - Gráficos de scores                                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      CAPA DE ORQUESTACIÓN                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  LangGraph - Máquina de estados                              │  │
│  │  - Nodos: 7 agentes especializados                           │  │
│  │  - Aristas: Enrutamiento condicional                         │  │
│  │  - Estado: TypedDict compartido                              │  │
│  │  - Compilación: Grafo compilado para ejecución              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  LangChain - Integración con LLMs                            │  │
│  │  - ChatOpenAI wrapper                                        │  │
│  │  - Message formatting                                        │  │
│  │  - Prompt templates                                          │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       CAPA DE AGENTES (NODOS)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Asistente    │  │ Coordinador  │  │ Agente       │              │
│  │ Requisitos   │→ │              │→ │ Noticias     │              │
│  │              │  │              │  │              │              │
│  │ Extrae       │  │ Prioriza     │  │ Analiza      │              │
│  │ criterios    │  │ zonas        │  │ zonas        │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│         ↓                                      ↓                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Scraping     │  │ Evaluador    │  │ Relajación   │              │
│  │              │→ │              │→ │              │              │
│  │ Busca        │  │ Califica     │  │ Modifica     │              │
│  │ propiedades  │  │ propiedades  │  │ criterios    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│         ↓                                      ↓                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Validador - Validación final de coherencia                  │  │
│  │ - Verifica cumplimiento de criterios                        │  │
│  │ - Evalúa calidad de recomendaciones                         │  │
│  │ - Genera mensaje final                                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      CAPA DE HERRAMIENTAS                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Scoring      │  │ Scrapers     │  │ OpenAI       │              │
│  │              │  │              │  │ Client       │              │
│  │ calcular_    │  │ - Base       │  │              │              │
│  │ score()      │  │ - Metrocuad. │  │ - primary()  │              │
│  │              │  │ - FincaRaiz  │  │ - fast()     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Parser Utils │  │ Scraper      │  │ Normalizer   │              │
│  │              │  │ Factory      │  │              │              │
│  │ JSON parsing │  │              │  │ Normaliza    │              │
│  │ Validation   │  │ Instancia    │  │ datos        │              │
│  │              │  │ scrapers     │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA DE DATOS EXTERNOS                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ OpenAI API   │  │ NewsAPI      │  │ Google News  │              │
│  │              │  │              │  │ RSS          │              │
│  │ GPT-4o       │  │ Noticias     │  │              │              │
│  │ GPT-4o-mini  │  │ recientes    │  │ Noticias     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Metrocuadrado│  │ FincaRaiz    │  │ El Colombiano│              │
│  │              │  │              │  │ El Tiempo    │              │
│  │ Portal web   │  │ Portal web   │  │ RSS feeds    │              │
│  │ Propiedades  │  │ Propiedades  │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. FLUJO DE DATOS DETALLADO

```
INPUT: "Busco apto en El Poblado, máximo 400M, 2 cuartos"
  │
  ├─→ [NODO 1: ASISTENTE REQUISITOS]
  │   ├─ Input: input_usuario
  │   ├─ Proceso:
  │   │  ├─ Enviar a GPT-4o con prompt especializado
  │   │  ├─ Parsear JSON de respuesta
  │   │  └─ Validar criterios
  │   └─ Output:
  │      ├─ criterios_originales: {region, precio_max, num_cuartos, ...}
  │      └─ criterios_actuales: {copia de criterios_originales}
  │
  ├─→ [NODO 2: COORDINADOR]
  │   ├─ Input: criterios_actuales, info_zonas (vacío en iter 1)
  │   ├─ Proceso:
  │   │  ├─ Enviar a GPT-4o-mini con contexto
  │   │  ├─ Parsear JSON con zonas priorizadas
  │   │  └─ Registrar en historial_iteraciones
  │   └─ Output:
  │      ├─ zonas_recomendadas: ["El Poblado", "Laureles", "Belén"]
  │      └─ zonas_analizadas: ["El Poblado", "Laureles", "Belén"]
  │
  ├─→ [NODO 3: AGENTE NOTICIAS]
  │   ├─ Input: zonas_recomendadas, criterios_actuales
  │   ├─ Proceso (para cada zona):
  │   │  ├─ Buscar noticias:
  │   │  │  ├─ Google News RSS (50 artículos)
  │   │  │  ├─ NewsAPI (fallback)
  │   │  │  ├─ RSS local (fallback)
  │   │  │  └─ Base de datos estática (fallback)
  │   │  ├─ Enviar a GPT-4o-mini para análisis
  │   │  ├─ Parsear JSON con compatibilidad
  │   │  └─ Guardar en info_zonas[zona]
  │   └─ Output:
  │      └─ info_zonas: {
  │           "El Poblado": {
  │             estrato_promedio: 6,
  │             noticias_recientes: [...],
  │             analisis: {compatibilidad: 0.85, ...}
  │           },
  │           ...
  │         }
  │
  ├─→ [NODO 4: PROPIEDADES SCRAPING]
  │   ├─ Input: criterios_actuales, zonas_recomendadas
  │   ├─ Proceso (para cada zona):
  │   │  ├─ Instanciar scrapers (Metrocuadrado, FincaRaiz)
  │   │  ├─ Ejecutar buscar_propiedades(criterios)
  │   │  ├─ Eliminar duplicados por URL
  │   │  └─ Acumular en propiedades_totales
  │   └─ Output:
  │      ├─ propiedades_brutas: [90 propiedades]
  │      └─ propiedades_filtradas: [90 propiedades]
  │
  ├─→ [NODO 5: EVALUADOR]
  │   ├─ Input: propiedades_filtradas, criterios_actuales, info_zonas
  │   ├─ Proceso:
  │   │  ├─ Para cada propiedad:
  │   │  │  ├─ Calcular score (precio 30%, área 25%, cuartos 20%, ...)
  │   │  │  ├─ Aplicar bonus/penalización por zona
  │   │  │  └─ Guardar razones y criterios cumplidos
  │   │  ├─ Ordenar por score descendente
  │   │  ├─ Decidir: ¿aceptable o insuficiente?
  │   │  └─ Generar explicación narrativa con GPT-4o
  │   └─ Output:
  │      ├─ propiedades_evaluadas: [90 propiedades con score]
  │      ├─ resultado_evaluacion: "aceptable"
  │      ├─ resultado_final: [top 5 propiedades]
  │      └─ explicacion_final: "Se encontraron excelentes opciones..."
  │
  ├─→ [ROUTER: ¿resultado_evaluacion == "aceptable"?]
  │   │
  │   ├─ SÍ → [NODO 7: VALIDADOR]
  │   │   ├─ Input: resultado_final, criterios_originales
  │   │   ├─ Proceso:
  │   │   │  ├─ Verificar cumplimiento de criterios
  │   │   │  ├─ Evaluar diversidad
  │   │   │  ├─ Enviar a GPT-4o-mini para validación
  │   │   │  └─ Parsear veredicto
  │   │   └─ Output:
  │   │      ├─ resultado_evaluacion: "aceptable"
  │   │      └─ explicacion_final: (actualizada)
  │   │
  │   └─ NO → [ROUTER: ¿iteracion_actual < max_iteraciones?]
  │       │
  │       ├─ SÍ → [NODO 6: RELAJACIÓN]
  │       │   ├─ Input: criterios_actuales, nivel_relajacion
  │       │   ├─ Proceso:
  │       │   │  ├─ Determinar qué campo relajar
  │       │   │  ├─ Calcular nuevo valor
  │       │   │  ├─ Registrar en historial_relajaciones
  │       │   │  └─ Limpiar propiedades
  │       │   └─ Output:
  │       │      ├─ criterios_actuales: (modificados)
  │       │      ├─ nivel_relajacion: (incrementado)
  │       │      └─ propiedades_filtradas: []
  │       │
  │       │   → Volver a [NODO 2: COORDINADOR] (nueva iteración)
  │       │
  │       └─ NO → FIN (sin resultados)
  │
  └─→ OUTPUT: resultado_final con top 5 propiedades
```

---

## 3. MÁQUINA DE ESTADOS

```
┌─────────────────────────────────────────────────────────────────┐
│                    ESTADOS DEL SISTEMA                          │
└─────────────────────────────────────────────────────────────────┘

ESTADO INICIAL
├─ input_usuario: "Busco apto en El Poblado..."
├─ criterios_originales: null
├─ criterios_actuales: null
├─ iteracion_actual: 0
├─ nivel_relajacion: 0
└─ resultado_evaluacion: null

        ↓ [NODO 1]

ESTADO DESPUÉS DE ASISTENTE
├─ input_usuario: "Busco apto en El Poblado..."
├─ criterios_originales: {region: "El Poblado", precio_max: 400M, ...}
├─ criterios_actuales: {region: "El Poblado", precio_max: 400M, ...}
├─ iteracion_actual: 0
├─ nivel_relajacion: 0
└─ resultado_evaluacion: null

        ↓ [NODO 2]

ESTADO DESPUÉS DE COORDINADOR
├─ criterios_actuales: {...}
├─ zonas_recomendadas: ["El Poblado", "Laureles", "Belén"]
├─ zonas_analizadas: ["El Poblado", "Laureles", "Belén"]
├─ iteracion_actual: 1
├─ historial_iteraciones: [{iteracion: 1, zonas: [...], ...}]
└─ resultado_evaluacion: null

        ↓ [NODO 3]

ESTADO DESPUÉS DE AGENTE NOTICIAS
├─ zonas_recomendadas: ["El Poblado", "Laureles", "Belén"]
├─ info_zonas: {
│    "El Poblado": {
│      estrato_promedio: 6,
│      noticias_recientes: [...],
│      analisis: {compatibilidad: 0.85, ...}
│    },
│    ...
│  }
└─ resultado_evaluacion: null

        ↓ [NODO 4]

ESTADO DESPUÉS DE SCRAPING
├─ propiedades_brutas: [90 propiedades]
├─ propiedades_filtradas: [90 propiedades]
└─ resultado_evaluacion: null

        ↓ [NODO 5]

ESTADO DESPUÉS DE EVALUADOR
├─ propiedades_evaluadas: [90 propiedades con score]
├─ resultado_evaluacion: "aceptable" | "insuficiente" | "vacio"
├─ resultado_final: [top 5 propiedades]
├─ explicacion_final: "Se encontraron excelentes opciones..."
└─ causa_insuficiencia: null | "No se encontraron suficientes propiedades"

        ↓ [ROUTER]

        ├─ SI (aceptable) → [NODO 7]
        │
        │   ESTADO DESPUÉS DE VALIDADOR
        │   ├─ resultado_evaluacion: "aceptable"
        │   ├─ explicacion_final: (actualizada)
        │   └─ → FIN EXITOSO
        │
        └─ NO (insuficiente) → [ROUTER]
            │
            ├─ SI (iter < max) → [NODO 6]
            │
            │   ESTADO DESPUÉS DE RELAJACIÓN
            │   ├─ criterios_actuales: (modificados)
            │   ├─ nivel_relajacion: (incrementado)
            │   ├─ iteracion_actual: (incrementado)
            │   ├─ historial_relajaciones: [{campo, valor_anterior, valor_nuevo, ...}]
            │   ├─ propiedades_filtradas: []
            │   └─ → Volver a [NODO 2]
            │
            └─ NO (iter >= max) → FIN POR LÍMITE
```

---

## 4. FLUJO DE RELAJACIÓN

```
ITERACIÓN 1 (Nivel 0 - Sin relajación)
┌─────────────────────────────────────────┐
│ Criterios: $400M, 3 cuartos, 70m²       │
│ Resultado: 0 propiedades                │
│ Decisión: RELAJAR                       │
└─────────────────────────────────────────┘
                ↓
ITERACIÓN 2 (Nivel 1 - Relajación leve)
┌─────────────────────────────────────────┐
│ Cambio: Precio $400M → $460M (+15%)     │
│ Criterios: $460M, 3 cuartos, 70m²       │
│ Resultado: 2 propiedades (score 0.35)   │
│ Decisión: RELAJAR MÁS                   │
└─────────────────────────────────────────┘
                ↓
ITERACIÓN 3 (Nivel 2 - Relajación moderada)
┌─────────────────────────────────────────┐
│ Cambio: Cuartos 3 → 2 (-1)              │
│ Criterios: $460M, 2 cuartos, 70m²       │
│ Resultado: 15 propiedades (score 0.78)  │
│ Decisión: ACEPTABLE ✓                   │
└─────────────────────────────────────────┘
                ↓
RESULTADO FINAL
┌─────────────────────────────────────────┐
│ Iteraciones: 3                          │
│ Modificaciones: 2                       │
│ - Precio +15%                           │
│ - Cuartos -1                            │
│ Propiedades recomendadas: 5             │
└─────────────────────────────────────────┘
```

---

## 5. MATRIZ DE DECISIÓN DEL EVALUADOR

```
┌──────────────────────────────────────────────────────────────────┐
│                    SCORING DE PROPIEDADES                        │
└──────────────────────────────────────────────────────────────────┘

CRITERIO          PESO    CÁLCULO                    RANGO
─────────────────────────────────────────────────────────────────
Precio            30%     1.0 - (precio/max * 0.5)   0.15 - 0.30
Área              25%     0.20 + (exceso/min * 0.05) 0.02 - 0.25
Cuartos           20%     1.0 si cumple              0.00 - 0.20
Baños             10%     1.0 si cumple              0.00 - 0.10
Parqueadero       10%     1.0 si cumple              0.00 - 0.10
URL verificable   5%      1.0 si existe              0.00 - 0.05
─────────────────────────────────────────────────────────────────
TOTAL             100%                               0.00 - 1.00

BONUS/PENALIZACIÓN POR ZONA
├─ Compatibilidad "alta": +5%
├─ Compatibilidad "media": 0%
├─ Compatibilidad "baja": -5%
└─ Alerta de seguridad: -10%

DECISIÓN FINAL
├─ Si ≥1 propiedad con score ≥0.45 → "aceptable"
├─ Si ≥3 propiedades (cualquier score) → "aceptable"
└─ Si no → "insuficiente"
```

---

## 6. CICLO DE VIDA DE UNA BÚSQUEDA

```
START
  │
  ├─→ Usuario ingresa texto libre
  │
  ├─→ [NODO 1] Extrae criterios
  │   └─ Crea criterios_originales (inmutable)
  │   └─ Crea criterios_actuales (mutable)
  │
  ├─→ LOOP ITERATIVO (máximo 5 veces)
  │   │
  │   ├─→ [NODO 2] Coordinador
  │   │   └─ Define zonas de búsqueda
  │   │
  │   ├─→ [NODO 3] Agente Noticias
  │   │   └─ Analiza zonas con contexto
  │   │
  │   ├─→ [NODO 4] Scraping
  │   │   └─ Busca propiedades
  │   │
  │   ├─→ [NODO 5] Evaluador
  │   │   └─ Califica propiedades
  │   │
  │   ├─→ ¿Resultado aceptable?
  │   │   │
  │   │   ├─ SÍ → [NODO 7] Validador
  │   │   │        └─ Validación final
  │   │   │        └─ → SALIDA
  │   │   │
  │   │   └─ NO → ¿Iteraciones < max?
  │   │           │
  │   │           ├─ SÍ → [NODO 6] Relajación
  │   │           │        └─ Modifica criterios
  │   │           │        └─ Vuelve a LOOP
  │   │           │
  │   │           └─ NO → SALIDA (sin resultados)
  │   │
  │   └─ FIN LOOP
  │
  ├─→ Formatea resultados con Rich
  │
  └─→ END

SALIDA
├─ Top 5 propiedades recomendadas
├─ Scores y razones
├─ Explicación narrativa
├─ Historial de modificaciones
└─ Links a propiedades
```

---

## 7. DEPENDENCIAS ENTRE NODOS

```
┌─────────────────────────────────────────────────────────────────┐
│                    GRAFO DE DEPENDENCIAS                        │
└─────────────────────────────────────────────────────────────────┘

[NODO 1: Asistente]
├─ Requiere: input_usuario
├─ Produce: criterios_originales, criterios_actuales
└─ Depende de: OpenAI API

[NODO 2: Coordinador]
├─ Requiere: criterios_actuales, info_zonas
├─ Produce: zonas_recomendadas, zonas_analizadas
└─ Depende de: OpenAI API

[NODO 3: Agente Noticias]
├─ Requiere: zonas_recomendadas, criterios_actuales
├─ Produce: info_zonas
└─ Depende de: Google News RSS, NewsAPI, OpenAI API

[NODO 4: Scraping]
├─ Requiere: criterios_actuales, zonas_recomendadas
├─ Produce: propiedades_brutas, propiedades_filtradas
└─ Depende de: Metrocuadrado, FincaRaiz

[NODO 5: Evaluador]
├─ Requiere: propiedades_filtradas, criterios_actuales, info_zonas
├─ Produce: propiedades_evaluadas, resultado_evaluacion, resultado_final
└─ Depende de: OpenAI API

[NODO 6: Relajación]
├─ Requiere: criterios_actuales, criterios_originales, resultado_evaluacion
├─ Produce: criterios_actuales (modificados), nivel_relajacion
└─ Depende de: OpenAI API

[NODO 7: Validador]
├─ Requiere: resultado_final, criterios_originales, modificaciones_realizadas
├─ Produce: resultado_evaluacion (final), explicacion_final
└─ Depende de: OpenAI API

ORDEN DE EJECUCIÓN
1. Nodo 1 (sin dependencias)
2. Nodo 2 (depende de Nodo 1)
3. Nodo 3 (depende de Nodo 2)
4. Nodo 4 (depende de Nodo 3)
5. Nodo 5 (depende de Nodo 4)
6. Nodo 6 o 7 (depende de Nodo 5)
```

---

## 8. TABLA DE TRANSICIONES DETALLADA

```
┌──────────────────────────────────────────────────────────────────┐
│                    TABLA DE TRANSICIONES                         │
└──────────────────────────────────────────────────────────────────┘

NODO ACTUAL    │ CONDICIÓN                    │ NODO SIGUIENTE
───────────────┼──────────────────────────────┼─────────────────────
Asistente      │ Siempre                      │ Coordinador
───────────────┼──────────────────────────────┼─────────────────────
Coordinador    │ Siempre                      │ Agente Noticias
───────────────┼──────────────────────────────┼─────────────────────
Agente Noticias│ Siempre                      │ Scraping
───────────────┼──────────────────────────────┼─────────────────────
Scraping       │ Siempre                      │ Evaluador
───────────────┼──────────────────────────────┼─────────────────────
Evaluador      │ resultado="aceptable"        │ Validador
               │ resultado="insuficiente" AND │ Relajación
               │ iteracion < max              │
               │ resultado="insuficiente" AND │ FIN
               │ iteracion >= max             │
───────────────┼──────────────────────────────┼─────────────────────
Validador      │ veredicto="aprobado"         │ FIN (exitoso)
               │ veredicto="rechazado" AND    │ Relajación
               │ iteracion < max              │
               │ veredicto="rechazado" AND    │ FIN (límite)
               │ iteracion >= max             │
───────────────┼──────────────────────────────┼─────────────────────
Relajación     │ Siempre                      │ Coordinador
───────────────┴──────────────────────────────┴─────────────────────
```

