from tools.scraper_factory import ScraperFactory
from state import SystemState
import time
import os
import yaml

with open("config/config.yaml", "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

scrapers = ScraperFactory.create_scrapers(CONFIG)

def nodo_propiedades_scraping(state: SystemState) -> SystemState:

    print("\n [Nodo 4] Iniciando scraping de propiedades...")

    criterios = state["criterios_actuales"]
    
    regiones = criterios.get(
        "regiones",
        [criterios.get("region", "Medellín")]
    )

    propiedades_totales = []
    
    # MODO SIMULADO

    if CONFIG["scraping"]["modo"] == "simulado":

        print(" Modo simulado activo")

        propiedades_totales = [
            {
                "id": "SIM-001",
                "titulo": "Apartamento en El Poblado",
                "precio": 450000000,
                "area": 82,
                "cuartos": 3,
                "banos": 2,
                "barrio": "El Poblado",
                "ciudad": "Medellín",
                "score": 0.85,
                "fuente": "simulado"
            }
        ]
    # MODO REAL

    else:
        scrapers = ScraperFactory.create_scrapers(CONFIG)
        
        for zona in regiones:
            print(f"\n Buscando en zona: {zona}")
            criterios_zona = {**criterios, "region": zona }
            
            for scraper in scrapers:
                try:
                    propiedades = scraper.buscar_propiedades(criterios_zona)
                    print(f" {scraper.__class__.__name__} [{zona}]: {len(propiedades)} propiedades")
                    propiedades_totales.extend(propiedades)

                except Exception as e:
                    print(f" Error {scraper.__class__.__name__} [{zona}]: {e}")

                finally:
                    time.sleep(5)
                    
    urls_vistas = set()
    propiedades_unicas = []
    
    for p in propiedades_totales:
        url = p.get("url")
        if not url:
            #propiedades_unicas.append(p)
            continue
        if url in urls_vistas:
            continue
        urls_vistas.add(url)
        propiedades_unicas.append(p)
        
    print(f"\n Total únicas: {len(propiedades_unicas)} propiedades")
    
    return {**state, "propiedades_brutas": propiedades_unicas, "propiedades_filtradas": propiedades_unicas}