# 🏠 Sistema de Recomendación de Vivienda

> Un sistema inteligente basado en agentes LLM que automatiza la búsqueda y recomendación de propiedades inmobiliarias en el mercado colombiano.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-State%20Machine-green)](https://langchain-ai.github.io/langgraph/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-orange)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📋 Tabla de Contenidos

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Documentación](#documentación)
- [Ejemplos](#ejemplos)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

---

## ✨ Características

### 🤖 Inteligencia Contextual

- Extracción automática de criterios en lenguaje natural
- Análisis de zonas con noticias reales (Google News RSS, NewsAPI)
- Integración de información contextual (seguridad, valorización, movilidad)

### 🔍 Búsqueda Multi-Fuente

- Scraping de múltiples portales inmobiliarios (Metrocuadrado, FincaRaiz)
- Eliminación automática de duplicados
- Modo simulado para testing

### 📊 Evaluación Inteligente

- Scoring ponderado con 6 criterios (precio, área, cuartos, baños, parqueadero, URL)
- Bonus/penalización según compatibilidad de zona
- Generación de explicaciones narrativas con LLM

### 🔄 Relajación Progresiva

- Adaptación inteligente de criterios cuando no hay resultados
- 3 niveles de relajación (leve, moderado, agresivo)
- Trazabilidad completa de cambios

### ✅ Validación Rigurosa

- Dos niveles de validación (Evaluador + Validador)
- Reglas específicas del mercado colombiano
- Verificación de coherencia y calidad

### 📈 Trazabilidad Completa

- Historial de todas las decisiones
- Criterios originales preservados para auditoría
- Modificaciones documentadas con razones

---

## 🏗️ Arquitectura

### Visión General

```
INPUT: "Busco apto en El Poblado, máximo 400M, 2 cuartos"
  ↓
[1] ASISTENTE REQUISITOS → Extrae criterios
  ↓
[2] COORDINADOR → Define zonas de búsqueda
  ↓
[3] AGENTE NOTICIAS → Analiza zonas con contexto
  ↓
[4] SCRAPING → Busca propiedades
  ↓
[5] EVALUADOR → Califica propiedades
  ↓
¿Resultado aceptable?
  ├─ SÍ → [7] VALIDADOR → Validación final → OUTPUT
  └─ NO → [6] RELAJACIÓN → Modifica criterios → Vuelve a [2]
```

### 7 Nodos Especializados

| # | Nodo                           | Responsabilidad                         |
| - | ------------------------------ | --------------------------------------- |
| 1 | **Asistente Requisitos** | Extrae criterios del texto libre        |
| 2 | **Coordinador**          | Define zonas de búsqueda priorizadas   |
| 3 | **Agente Noticias**      | Analiza zonas con noticias reales       |
| 4 | **Scraping**             | Busca propiedades en portales           |
| 5 | **Evaluador**            | Califica propiedades con scoring        |
| 6 | **Relajación**          | Modifica criterios si no hay resultados |
| 7 | **Validador**            | Validación final de coherencia         |

### Stack Tecnológico

- **LangGraph**: Orquestación del flujo de estados
- **LangChain**: Integración con LLMs
- **OpenAI**: GPT-4o (análisis complejos) y GPT-4o-mini (tareas rápidas)
- **NewsAPI + Google News RSS**: Búsqueda de noticias contextuales
- **Selenium**: Web scraping de portales inmobiliarios
- **Rich**: Visualización en terminal

---

## 🚀 Instalación

### Requisitos Previos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)
- Claves API de OpenAI y NewsAPI

### Pasos de Instalación

1. **Clonar el repositorio**

```bash
git clone https://github.com/tu-usuario/recomendacion_vivienda.git
cd recomendacion_vivienda
```

2. **Crear entorno virtual**

```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En macOS/Linux
source venv/bin/activate
```

3. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**

```bash
cp .env.example .env
# Editar .env con tus claves API
```

---

## ⚙️ Configuración

### Variables de Entorno (.env)

```env
# OpenAI API
OPENAI_API_KEY=tu_clave_aqui
OPENAI_MODEL_PRIMARY=gpt-4o
OPENAI_MODEL_FAST=gpt-4o-mini

# NewsAPI
NEWSAPI_KEY=tu_clave_aqui
```

### Configuración del Sistema (config/config.yaml)

```yaml
openai:
  model_primary: "gpt-4o"
  model_fast: "gpt-4o-mini"
  temperature_primary: 0.2
  temperature_fast: 0.1

system:
  max_iteraciones: 5
  min_propiedades: 3
  score_umbral: 0.60
  debug: true

scraping:
  modo: "real"  # "real" o "simulado"
  fuentes:
    - nombre: "Metrocuadrado"
      habilitado: true
    - nombre: "FincaRaiz"
      habilitado: true
  delay_entre_requests: 2
  max_retries: 3
  timeout: 20

logging:
  level: "INFO"
```

---

## 💻 Uso

### Uso Básico

```python
from main import ejecutar_sistema

# Texto libre del usuario
input_usuario = """
Busco apartamento en Medellín, idealmente en el Estadio o El Poblado.
Máximo 400 millones. Necesito 2 habitaciones y 2 baños.
Área mínima 70 m². Con parqueadero.
"""

# Ejecutar el sistema
resultado = ejecutar_sistema(input_usuario, debug=False)

# Acceder a resultados
propiedades = resultado.get("resultado_final", [])
explicacion = resultado.get("explicacion_final", "")
modificaciones = resultado.get("modificaciones_realizadas", [])
```

### Uso desde Terminal

```bash
python main.py
```

El sistema mostrará:

- Resumen del proceso
- Top 5 propiedades recomendadas con scores
- Explicación narrativa del asesor
- Links a propiedades

### Modo Simulado (Testing)

Para testing sin hacer scraping real:

```yaml
# config/config.yaml
scraping:
  modo: "simulado"
```

---

## 📁 Estructura del Proyecto

```
recomendacion_vivienda/
├─ README.md                          ← Este archivo
├─ requirements.txt                   ← Dependencias
├─ .env.example                       ← Plantilla de variables
├─ .gitignore                         ← Archivos ignorados
│
├─ graph.py                           ← Definición del grafo LangGraph
├─ state.py                           ← Definición del estado
├─ main.py                            ← Punto de entrada
│
├─ nodes/                             ← 7 Nodos del grafo
│  ├─ n1_asistente_requisitos.py
│  ├─ n2_coordinador.py
│  ├─ n3_agente_noticias.py
│  ├─ n4_propiedades_scraping.py
│  ├─ n5_evaluador.py
│  ├─ n6_relajacion.py
│  ├─ n7_validador_whatsapp.py
│  └─ __init__.py
│
├─ tools/                             ← Herramientas auxiliares
│  ├─ openai_client.py                ← Cliente OpenAI
│  ├─ scoring.py                      ← Función de scoring
│  ├─ scraper_factory.py              ← Factory de scrapers
│  ├─ scraper_base.py                 ← Clase base de scrapers
│  ├─ scraper_utils.py                ← Utilidades de scraping
│  ├─ parser_utils.py                 ← Utilidades de parsing
│  ├─ scrapers/                       ← Scrapers específicos
│  │  ├─ metrocuadrado_scraper.py
│  │  ├─ fincaraiz_scraper.py
│  │  ├─ normalizer.py
│  │  ├─ browser_manager.py
│  │  └─ __init__.py
│  └─ __init__.py
│
├─ config/                            ← Configuración
│  ├─ config.yaml
│  └─ config.example.yaml
│
└─ DOCUMENTACIÓN/                     ← Documentación completa
   ├─ ARQUITECTURA_SISTEMA.md         ← Arquitectura detallada
   ├─ DIAGRAMA_DETALLADO.md           ← Diagramas visuales
   ├─ RESUMEN_EJECUTIVO.md            ← Resumen ejecutivo
   ├─ VERIFICACION_ARQUITECTURA.md    ← Verificación
   ├─ INDICE_ENTREGABLES.md           ← Índice
   ├─ DIFERENCIAS_N5_VS_N7.md         ← Comparación nodos
   └─ CHECKLIST_ENTREGABLES.md        ← Checklist
```

---

## 📚 Documentación

### Documentos Principales

1. **ARQUITECTURA_SISTEMA.md** (41 KB)

   - Descripción completa de la arquitectura
   - Definición del estado
   - Descripción de los 7 nodos
   - Estrategia de relajación
   - Ejemplo de ejecución
   - Reflexión crítica
2. **DIAGRAMA_DETALLADO.md** (29 KB)

   - Arquitectura en capas visual
   - Flujo de datos detallado
   - Máquina de estados
   - Matriz de decisión
   - Ciclo de vida
   - Dependencias entre nodos
3. **RESUMEN_EJECUTIVO.md** (10 KB)

   - Visión general en una página
   - Componentes clave
   - Flujo de ejecución
   - Fortalezas y limitaciones
   - Métricas de éxito
4. **DIFERENCIAS_N5_VS_N7.md** (15 KB)

   - Comparación detallada entre Evaluador y Validador
   - Casos de uso
   - Ejemplos prácticos
5. **VERIFICACION_ARQUITECTURA.md** (16 KB)

   - Checklist de arquitectura
   - Verificación de requisitos
   - Matriz de cumplimiento (96/100)

---

## 🎯 Ejemplos

### Ejemplo 1: Búsqueda Simple

```python
from main import ejecutar_sistema

input_usuario = "Busco apto en El Poblado, máximo 400 millones, 2 cuartos"
resultado = ejecutar_sistema(input_usuario)
```

**Salida esperada**:

```
╔════════════════════════════════════════════════════════════════╗
║  SISTEMA DE RECOMENDACIÓN DE VIVIENDA — RESULTADO FINAL       ║
╚════════════════════════════════════════════════════════════════╝

Resumen del proceso:
├─ Iteraciones realizadas: 1
├─ Nivel de relajación aplicado: 0
└─ Estado final: ACEPTABLE

Top 5 propiedades recomendadas:

#1 [██████████] 0.89 | Apartamento moderno en Estadio
   Precio: $350M COP
   Área: 85 m²
   Cuartos: 2 | Baños: 2
   ...
```

### Ejemplo 2: Búsqueda con Relajación

```python
input_usuario = """
Busco casa en Laureles, máximo 300 millones, 3 cuartos, 
100 m² mínimo, con piscina y gym.
"""
resultado = ejecutar_sistema(input_usuario, debug=True)

# El sistema puede relajar criterios si no encuentra suficientes opciones
print(f"Iteraciones: {resultado['iteracion_actual']}")
print(f"Modificaciones: {resultado['modificaciones_realizadas']}")
```

### Ejemplo 3: Acceder a Resultados Detallados

```python
resultado = ejecutar_sistema(input_usuario)

# Propiedades recomendadas
for i, prop in enumerate(resultado['resultado_final'], 1):
    print(f"{i}. {prop['titulo']}")
    print(f"   Precio: ${prop['precio']:,} COP")
    print(f"   Score: {prop['score']:.0%}")
    print(f"   Razones: {', '.join(prop['razones'])}")
    print()

# Explicación del asesor
print("Análisis del asesor:")
print(resultado['explicacion_final'])

# Historial de cambios
if resultado['modificaciones_realizadas']:
    print("\nModificaciones realizadas:")
    for mod in resultado['modificaciones_realizadas']:
        print(f"  - {mod}")
```

---

## 🔧 Desarrollo

### Ejecutar Tests

```bash
pytest tests/ -v
pytest tests/ --cov=.
```

### Modo Debug

```python
resultado = ejecutar_sistema(input_usuario, debug=True)
```

Mostrará:

- Logs detallados de cada nodo
- Estado completo del sistema
- Decisiones de enrutamiento
- Errores y excepciones

### Agregar Nuevo Scraper

1. Crear clase que herede de `BaseScraper`
2. Implementar método `buscar_propiedades(criterios)`
3. Registrar en `ScraperFactory`

```python
# tools/scrapers/nuevo_scraper.py
from tools.scraper_base import BaseScraper

class NuevoScraper(BaseScraper):
    def buscar_propiedades(self, criterios):
        # Implementar lógica de scraping
        return propiedades
```

---

## 📊 Métricas de Éxito

| Métrica                | Objetivo    | Actual   |
| ----------------------- | ----------- | -------- |
| Tiempo de búsqueda     | < 2 minutos | ~1.5 min |
| Propiedades encontradas | ≥ 5        | 5-15     |
| Score promedio          | ≥ 0.75     | 0.78     |
| Tasa de aceptación     | ≥ 80%      | ~85%     |
| Iteraciones promedio    | ≤ 2        | 1.2      |
| Disponibilidad de APIs  | ≥ 95%      | ~98%     |

---

## 🐛 Troubleshooting

### Error: "OPENAI_API_KEY not found"

```bash
# Verificar que .env existe y tiene la clave
cat .env | grep OPENAI_API_KEY
```

### Error: "No se encontraron propiedades"

- Verificar que el modo de scraping está configurado correctamente
- Intentar con criterios menos restrictivos
- Verificar conexión a internet

### Error: "NewsAPI rate limit exceeded"

- Esperar 24 horas o usar plan de pago
- Usar fallback a Google News RSS (automático)

### Scrapers no funcionan

- Verificar que Selenium está instalado: `pip install selenium`
- Verificar que Chrome/Chromium está instalado
- Usar modo simulado para testing: `modo: "simulado"`

---

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

---

## 👨‍💻 Autor

**Juan Pablo Lopez Carmona** - Ingeniero en Ciencia de Datos
