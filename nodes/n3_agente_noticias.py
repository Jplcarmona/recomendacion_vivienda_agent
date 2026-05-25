import json
import os
import requests
from datetime import datetime, timedelta
from langchain_core.messages import SystemMessage, HumanMessage
from tools.openai_client import OpenAIClient
from state import SystemState
import xml.etree.ElementTree as ET
from urllib.parse import quote
import xml.etree.ElementTree as ET
import re
from tools.scoring import _score_categoria

CATEGORIAS_BUSQUEDA = {
    "valorizacion": [
        "valorización",
        "plusvalía",
        "inversión",
        "finca raíz",
        "proyectos inmobiliarios",
        "precio vivienda",
    ],
    "seguridad": [
        "seguridad",
        "hurto",
        "criminalidad",
        "convivencia",
    ],
    "movilidad": [
        "metro",
        "movilidad",
        "infraestructura",
        "urbanismo",
    ],
    "calidad_vida": [
        "comercio",
        "restaurantes",
        "turismo",
        "parques",
        "calidad de vida",
    ],
    "riesgos": [
        "deslizamientos",
        "inundaciones",
        "contaminación",
        "riesgo",
    ],
    "educacion_servicios": [
        "colegios",
        "universidades",
        "hospitales",
        "servicios",
    ]
}

def construir_queries_zona(zona: str):
    queries = []
    for categoria, keywords in CATEGORIAS_BUSQUEDA.items():
        query = (
            f'"{zona}" Medellin ('
            + " OR ".join(keywords)
            + ")"
        )
        queries.append({
            "categoria": categoria,
            "query": query
        })
    return queries

# Base de datos estática de zonas (fallback si no hay noticias)

ZONAS_DATABASE = {
    "El Poblado":  {"estrato_promedio": 6, "precio_m2_promedio": 8_500_000, "seguridad": "alta",      "valorización_anual": "8%"},
    "Laureles":    {"estrato_promedio": 5, "precio_m2_promedio": 6_200_000, "seguridad": "alta",      "valorización_anual": "6%"},
    "Envigado":    {"estrato_promedio": 4, "precio_m2_promedio": 5_800_000, "seguridad": "alta",      "valorización_anual": "7%"},
    "Belén":       {"estrato_promedio": 3, "precio_m2_promedio": 4_000_000, "seguridad": "media",     "valorización_anual": "5%"},
    "Robledo":     {"estrato_promedio": 3, "precio_m2_promedio": 3_500_000, "seguridad": "media",     "valorización_anual": "4%"},
    "Estadio":     {"estrato_promedio": 4, "precio_m2_promedio": 5_000_000, "seguridad": "media",     "valorización_anual": "5%"},
    "Aranjuez":    {"estrato_promedio": 3, "precio_m2_promedio": 3_200_000, "seguridad": "media",     "valorización_anual": "4%"},
    "Sabaneta":    {"estrato_promedio": 4, "precio_m2_promedio": 5_200_000, "seguridad": "alta",      "valorización_anual": "6%"},
    "Itagüí":      {"estrato_promedio": 3, "precio_m2_promedio": 3_800_000, "seguridad": "media",     "valorización_anual": "5%"},
    "Bello":       {"estrato_promedio": 2, "precio_m2_promedio": 2_500_000, "seguridad": "media",     "valorización_anual": "3%"},
    "Castilla":    {"estrato_promedio": 2, "precio_m2_promedio": 2_800_000, "seguridad": "media",     "valorización_anual": "3%"},
    "El Centro":   {"estrato_promedio": 2, "precio_m2_promedio": 2_800_000, "seguridad": "baja-media","valorización_anual": "3%"},
}

SYSTEM_PROMPT_ANALISIS = """Eres un analista de mercado inmobiliario colombiano.
Dado el perfil de una zona, sus noticias recientes y los criterios del usuario,
genera un análisis de compatibilidad en JSON:

{
  "compatibilidad": número del 0 al 1,
  "resumen": "análisis de 2-3 oraciones considerando las noticias recientes",
  "fortalezas": ["lista basada en noticias y datos"],
  "debilidades": ["lista basada en noticias y datos"],
  "recomendacion": "alta | media | baja",
  "alerta_seguridad": "descripción si hay noticias negativas de seguridad, o null",
  "oportunidad": "descripción si hay noticias positivas de valorización, o null"
}

INSTRUCCIONES DE PONDERACIÓN:
- La compatibilidad mide qué tan adecuada es la zona para VIVIR EN FAMILIA, no para invertir.
- Incidentes aislados de violencia NO deben bajar la compatibilidad por debajo de 0.5 si la zona
  tiene historial positivo de seguridad — todas las ciudades tienen incidentes.
- Pondera principalmente: calidad de vida, servicios, conectividad, valorización y seguridad ESTRUCTURAL.
- Solo baja por debajo de 0.4 si hay un patrón sostenido de inseguridad, no por noticias aisladas.
- El precio m² promedio vs el precio_max del usuario es el factor más importante.
"""
# Funciones de NewsAPI
def _buscar_noticias_newsapi(zona: str, max_noticias: int = 5) -> list:
    """
    Busca noticias reales de la zona en NewsAPI.
    Temas: calidad de vida, seguridad, valorización, infraestructura.
    """
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        print(f"NEWSAPI_KEY no encontrada en .env")
        return []

    # Buscar noticias de los últimos 30 días
    fecha_desde = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    zona_query = zona.replace("í", "i").replace("é", "e").replace("á", "a").replace("ó", "o").replace("ú", "u")

    # Queries específicas por zona y temas relevantes
    queries = [
        f"Medellin seguridad barrios",
        f"Medellin calidad vida vivienda",
        f"Medellin valorización inmuebles",
    ]

    noticias_encontradas = []
    urls_vistas = set()

    for query in queries:
        if len(noticias_encontradas) >= max_noticias:
            break

        try:
            response = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": query,
                    "from": fecha_desde,
                    "language": "es",
                    "sortBy": "relevancy",
                    "pageSize": 3,
                    "apiKey": api_key,
                },
                timeout=10
            )
            data = response.json()
            print(f"NewsAPI [{response.status_code}] '{query}': {len(data.get('articles', []))} articulos")
            
            if response.status_code != 200:
                print(f"Error NewsAPI: {data.get('message', 'sin mensaje')}")
                continue

            for articulo in data.get("articles", []):
                url = articulo.get("url", "")
                titulo = articulo.get("title", "")
                descripcion = articulo.get("description", "") or ""

                # evitar duplicados y artículos sin título
                if not titulo or url in urls_vistas:
                    continue
                if "[Removed]" in titulo:
                    continue

                urls_vistas.add(url)
                
                menciona_zona = zona_query.lower() in (titulo + descripcion).lower()
                
                noticias_encontradas.append({
                    "titulo": titulo,
                    "descripcion": descripcion[:200],
                    "fuente": articulo.get("source", {}).get("name", ""),
                    "fecha": articulo.get("publishedAt", "")[:10],
                    "url": url,
                    "relevante_zona": menciona_zona,
                })

                if len(noticias_encontradas) >= max_noticias:
                    break

        except Exception as e:
            print(f"Error consultando NewsAPI para '{query}': {e}")
            continue

    return noticias_encontradas

def _buscar_noticias_rss_fallback(zona: str) -> list:
    """
    Fallback con RSS de El Colombiano y El Tiempo
    """
    feeds = [
        "https://www.elcolombiano.com/rss/feed.xml",
        "https://www.eltiempo.com/rss/medellin.xml",
    ]

    noticias = []
    zona_lower = zona.lower()

    for feed_url in feeds:
        try:
            response = requests.get(feed_url, timeout=8)
            if response.status_code != 200:
                continue

            root = ET.fromstring(response.content)
            items = root.findall(".//item")

            for item in items[:30]:
                titulo = item.findtext("title") or ""
                descripcion = item.findtext("description") or ""
                link = item.findtext("link") or ""
                fecha = item.findtext("pubDate") or ""

                # filtrar por zona
                texto_completo = (titulo + descripcion).lower()
                if zona_lower not in texto_completo and "medellín" not in texto_completo:
                    continue

                noticias.append({
                    "titulo": titulo,
                    "descripcion": descripcion[:200],
                    "fuente": feed_url.split("/")[2],
                    "fecha": fecha[:10],
                    "url": link,
                })

                if len(noticias) >= 3:
                    break

        except Exception as e:
            continue

    return noticias

def _buscar_noticias_google_rss(zona: str, max_noticias: int = 5) -> list:
    
    queries = construir_queries_zona(zona)
    
    noticias_totales = []
    urls_vistas = set()
    
    for q in queries:
        
        categoria = q["categoria"]
        zona_query = q["query"]
        
        url = (
            f"https://news.google.com/rss/search"
            f"?q={quote(zona_query)}"
            f"&hl=es-419&gl=CO&ceid=CO:es-419"
        )

        try:
            response = requests.get(url, timeout=10, headers={
                "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36")
            })

            if response.status_code != 200:
                print(f"Google RSS status: {response.status_code}")
                continue

            root = ET.fromstring(response.content)
            items = root.findall(".//item")
        
            for item in items:
                titulo = item.findtext("title") or ""
                link   = item.findtext("link") or ""
                fecha  = item.findtext("pubDate") or ""
                desc   = item.findtext("description") or ""

                if not titulo:
                    continue
                
                # Limpiar HTML
                desc = re.sub(r"<.*?>", "", desc)
                
                # Evitar cuplicados
                if link in urls_vistas:
                    continue
                
                urls_vistas.add(link)
                texto_total = f"{titulo} {desc}".lower()
                
                noticias_totales.append({
                    "titulo": titulo,
                    "descripcion": desc[:300],
                    "fuente": "Google News",
                    "fecha": fecha[:16],
                    "url": link,
                    "categoria": categoria,
                    "relevante_zona": zona.lower() in texto_total,
                    "score_categoria": _score_categoria(categoria,titulo,desc)
                })
                
                if len(noticias_totales) >= max_noticias:
                    break
        except Exception as e:
            print(f"Error Google RSS [{categoria}]: {e}")
    
    # Ordenar por score descendente
    noticias_totales.sort(key=lambda x: x.get("score_categoria", 0),reverse=True)
                       
    print(f"Google RSS: {len(noticias_totales)} noticias para {zona}")
    
    return noticias_totales[:max_noticias]


# Nodo principal

def nodo_agente_noticias(state: SystemState) -> SystemState:
    """
    Nodo 3: Busca noticias reales via Google News o NEWSAPI y analiza compatibilidad de zonas.
    """
    llm = OpenAIClient.fast()

    print("\n [Nodo 3] Buscando noticias reales de zonas...")

    zonas_usuario = state.get("criterios_actuales", {}).get("regiones", [])
    zonas_coordinador = state.get("zonas_recomendadas", [])
    zonas = zonas_usuario if zonas_usuario else zonas_coordinador
    criterios = state.get("criterios_actuales", {})
    info_zonas = dict(state.get("info_zonas", {}))

    nivel_relajacion = state.get("nivel_relajacion", 0)

    for zona in zonas:

        if zona in info_zonas:
            print(f" {zona}: ya analizada, omitiendo.")
            continue

        print(f"Buscando noticias de: {zona}")

        # 1. Datos base de la zona
        zona_data = dict(ZONAS_DATABASE.get(zona, {
            "estrato_promedio": 3,
            "precio_m2_promedio": 4_000_000,
            "seguridad": "media",
            "valorización_anual": "5%",
        }))

        # 2. Buscar noticias reales 
        noticias = _buscar_noticias_google_rss(zona, max_noticias=50)

        if not noticias:
            print(f" Google RSS sin resultados, intentando NewsAPI")
            noticias = _buscar_noticias_newsapi(zona, max_noticias=50)

        if not noticias:
            print(f" NewsAPI sin resultados, usando RSS fallback")
            noticias = _buscar_noticias_rss_fallback(zona)
            
        if not noticias:
            print(f" Sin noticias encontradas para {zona}, usando datos base")

        zona_data["noticias_recientes"] = noticias
        print(f"{len(noticias)} noticias encontradas para {zona}")

        # ── 3. Analizar compatibilidad con LLM ────────────────────────────────
        try:
            noticias_texto = "\n".join([
                f"- [{n['fecha']}] {'⭐' if n.get('relevante_zona') else '🌆'} "
                f"{n['titulo']} ({n['fuente']}): {n['descripcion']}"
                for n in noticias
            ]) if noticias else "No se encontraron noticias recientes."

            prompt = f"""
ZONA: "{zona}"
DATOS BASE:
- Estrato promedio: {zona_data.get('estrato_promedio')}
- Precio m² promedio: ${zona_data.get('precio_m2_promedio', 0):,} COP
- Seguridad histórica: {zona_data.get('seguridad')}
- Valorización anual histórica: {zona_data.get('valorización_anual')}

NOTICIAS RECIENTES (últimos 30 días):
{noticias_texto}

CRITERIOS DEL USUARIO:
- Precio máximo: ${criterios.get('precio_max', 0):,} COP
- Tipo: {criterios.get('tipo_inmueble', 'apartamento')}
- Cuartos: {criterios.get('num_cuartos', 2)}
- Estrato deseado: {criterios.get('estrato', 'cualquiera')}
- Familia: {criterios.get('amenities', [])}
"""
            messages = [
                SystemMessage(content=SYSTEM_PROMPT_ANALISIS),
                HumanMessage(content=prompt)
            ]

            response = llm.invoke(messages)
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            analisis = json.loads(raw)
            zona_data["analisis"] = analisis

            compat = analisis.get("compatibilidad", 0.5)
            rec    = analisis.get("recomendacion", "?")
            alerta = analisis.get("alerta_seguridad")
            op     = analisis.get("oportunidad")

            print(f" {zona}: compatibilidad {compat:.0%} ({rec})")
            if alerta:
                print(f" Alerta: {alerta}")
            if op:
                print(f" Oportunidad: {op}")

        except Exception as e:
            print(f" Error en análisis LLM ({e}), usando datos base")
            zona_data["analisis"] = {
                "compatibilidad": 0.5,
                "recomendacion": "media",
                "resumen": "Análisis no disponible.",
                "fortalezas": [],
                "debilidades": [],
                "alerta_seguridad": None,
                "oportunidad": None,
            }

        info_zonas[zona] = zona_data

    return {**state, "info_zonas": info_zonas}