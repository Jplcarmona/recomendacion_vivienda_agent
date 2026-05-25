import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tools.scraper_base import BaseScraper
from tools.scrapers.browser_manager import BrowserManager
from tools.parser_utils import ParserUtils

BARRIOS_MEDELLIN = {
    "laureles":        ("laureles",      "occidente",    "medellin"),
    "el poblado":      ("el-poblado",    "suroriente",   "medellin"),
    "poblado":         ("el-poblado",    "suroriente",   "medellin"),
    "envigado":        ("envigado",      "sur",          "envigado"),
    "belen":           ("belen",         "suroccidente", "medellin"),
    "belén":           ("belen",         "suroccidente", "medellin"),  
    "robledo":         ("robledo",       "noroccidente", "medellin"),
    "sabaneta":        ("sabaneta",      "sur",          "sabaneta"),
    "itagui":          ("itagui",        "sur",          "itagui"),
    "itagüí":          ("itagui",        "sur",          "itagui"),    
    "estadio":         ("estadio",       "occidente",    "medellin"),
    "bello":           ("bello",         "norte",        "bello"),
    "aranjuez":        ("aranjuez",      "nororiental",  "medellin"),
    "castilla":        ("castilla",      "noroccidente", "medellin"),
}

TIPOS_FINCARAIZ = {
        "apartamento": "apartamentos",
        "casa":        "casas",
        "estudio":     "apartaestudios",
        "local":       "locales-comerciales",
    }

class FincaRaizScraper(BaseScraper):

    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://www.fincaraiz.com.co"

    def construir_url(self, criterios):
        region_raw = ParserUtils.normalizar_region(criterios.get("region", "medellin"))
        tipo_raw = criterios.get("tipo_inmueble","apartamento").lower().strip()
        tipo = TIPOS_FINCARAIZ.get(tipo_raw,"apartamentos")
        region = region_raw.replace(" ", "-")
        
        if region_raw in BARRIOS_MEDELLIN:
            barrio, zona, ciudad = BARRIOS_MEDELLIN[region_raw]
            return f"{self.base_url}/venta/{tipo}/{barrio}/{zona}/{ciudad}"
        else:
            ciudad = region_raw.replace(" ", "-")
            return f"{self.base_url}/venta/{tipo}/{ciudad}/antioquia"

        return (
            f"https://www.fincaraiz.com.co/venta/{tipo}/{region}"
        )

    def buscar_propiedades(self, criterios):
        url = self.construir_url(criterios)
        print(f"\nFincaRaiz URL: {url}")
        driver = BrowserManager.create_driver()
        propiedades = []

        try:
            driver.get(url)
            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid], article, .listingCard")))
            time.sleep(4)
            cards = (driver.find_elements(By.CSS_SELECTOR,"[data-testid='listing-card']"
            )
            or driver.find_elements(By.CSS_SELECTOR,".listingCard")
            or driver.find_elements(By.TAG_NAME,"article")
        )

            print(f"Cards encontradas: {len(cards)}")

            for idx, card in enumerate(cards[:20]):
                try:
                    texto = ParserUtils.limpiar_texto(card.text)
                    if len(texto) < 20:
                        continue

                    links = card.find_elements(By.TAG_NAME,"a")
                    url_prop = None

                    if links:
                        url_prop = links[0].get_attribute("href")
                        
                    barrio, ciudad = self._extraer_ubicacion_fincaraiz(texto)
                    
                    propiedad = {
                        "id": f"FR-{idx}",
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
                        "fuente": "FincaRaiz"
                    }

                    propiedades.append(propiedad)

                except Exception as e:
                    print(f"Error property: {e}")

        except Exception as e:
            print(f"\nError FincaRaiz: {e}")

        finally:
            driver.quit()

        return propiedades

    def _extraer_ubicacion_fincaraiz(self, texto: str):
        """Extrae barrio y ciudad del formato 'en Estadio, Medellín, Antioquia'"""
        try:
            match = re.search(
                r"(?:Apartamento|Casa|Estudio)\s+en\s+([^,]+),\s*([^,\n]+)",texto,re.IGNORECASE)
            
            if match:
                barrio = match.group(1).strip()
                ciudad = match.group(2).strip()
                return barrio, ciudad
            
        except Exception:
            pass
        return "", ""