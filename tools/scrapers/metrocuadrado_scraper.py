import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tools.scraper_base import BaseScraper
from tools.scrapers.browser_manager import BrowserManager
from tools.parser_utils import ParserUtils

TIPOS_METRO = {
    "apartamento": "apartamentos",
    "casa":        "casas",
    "estudio":     "apartaestudios",
    "local":       "locales",
}

CIUDADES_METRO = {
    "el poblado":  ("medellin", "el-poblado"),
    "poblado":     ("medellin", "el-poblado"),
    "laureles":    ("medellin", "laureles"),
    "envigado":    ("envigado", ""),
    "belen":       ("medellin", "belen"),
    "belén":       ("medellin", "belen"),
    "robledo":     ("medellin", "robledo"),
    "sabaneta":    ("sabaneta", ""),
    "itagui":      ("itagui",   ""),
    "itagüí":      ("itagui",   ""),
    "estadio":     ("medellin", "estadio"),
    "bello":       ("bello",    ""),
    "aranjuez":    ("medellin", "aranjuez"),
    "castilla":    ("medellin", "castilla"),
    "medellin":    ("medellin", ""),
    "medellín":    ("medellin", ""),
}

class MetrocuadradoScraper(BaseScraper):

    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://www.metrocuadrado.com"

    def construir_url(self, criterios):

        region_raw = ParserUtils.normalizar_region(
            criterios.get("region", "medellin")
        ).lower().strip()

        tipo_raw = criterios.get("tipo_inmueble", "apartamento").lower()
        tipo = TIPOS_METRO.get(tipo_raw, "apartamentos")

        if region_raw in CIUDADES_METRO:
            ciudad, barrio = CIUDADES_METRO[region_raw]
            if barrio:
                return f"{self.base_url}/{tipo}/venta/{ciudad}/{barrio}/"
            else:
                return f"{self.base_url}/{tipo}/venta/{ciudad}/"
        else:
            region = region_raw.replace(" ", "-")
            return f"{self.base_url}/{tipo}/venta/{region}/"

    def buscar_propiedades(self, criterios):

        url = self.construir_url(criterios)
        print(f"\nMetrocuadrado URL: {url}")

        driver = BrowserManager.create_driver(headless=False)
        propiedades = []

        try:
            driver.get(url)
            time.sleep(6)

            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[class*='card']")
                )
            )

            time.sleep(2)

            # ← selector correcto confirmado por el test
            todas_cards = driver.find_elements(
                By.CSS_SELECTOR, "div[class*='card']"
            )

            # filtrar solo cards de propiedades — tienen precio en el texto
            cards = [
                c for c in todas_cards
                if "$" in c.text and len(c.text) > 40
            ]

            print(f"Cards de propiedades: {len(cards)}")

            for idx, card in enumerate(cards[:20]):

                try:
                    texto = ParserUtils.limpiar_texto(card.text)

                    # extraer URL — buscar el <a> con href de inmueble
                    url_prop = None
                    links = card.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        href = link.get_attribute("href") or ""
                        if "/inmueble/" in href:
                            url_prop = href
                            break

                    # extraer barrio y ciudad del texto
                    # formato: "Estadio | Medellín\n$830.000.000\n..."
                    barrio, ciudad = self._extraer_ubicacion(texto)

                    propiedades.append({
                        "id": f"MC-{idx}",
                        "titulo": texto[:80],
                        "texto_raw": texto,
                        "precio": ParserUtils.extraer_precio(texto),
                        "area": ParserUtils.extraer_area(texto),
                        "cuartos": ParserUtils.extraer_habitaciones(texto),
                        "banos": ParserUtils.extraer_banos(texto),
                        "parqueadero": ParserUtils.detectar_parqueadero(texto),
                        "barrio": barrio,
                        "ciudad": ciudad,
                        "url": url_prop,
                        "fuente": "Metrocuadrado"
                    })

                except Exception as e:
                    print(f"Error card MC-{idx}: {e}")

        except Exception as e:
            print(f"\nError Metrocuadrado: {e}")

        finally:
            driver.quit()

        return propiedades

    def _extraer_ubicacion(self, texto: str):
        """Extrae barrio y ciudad del formato 'Aranjuez | Nororiente | Medellín'"""
        try:
            # toma la primera línea del texto
            primera_linea = texto.split("$")[0].strip()
            partes = [p.strip() for p in primera_linea.split("|")]

            if len(partes) >= 3:
                # "Aranjuez | Nororiente | Medellín" → barrio=Aranjuez, ciudad=Medellín
                return partes[0].strip(), partes[-1].strip()
            elif len(partes) == 2:
                # "Aranjuez | Medellín"
                return partes[0].strip(), partes[1].strip()
            elif len(partes) == 1:
                return partes[0].strip(), ""
        except Exception:
            pass
        return "", ""