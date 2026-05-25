from tools.scrapers.metrocuadrado_scraper import MetrocuadradoScraper
from tools.scrapers.fincaraiz_scraper import FincaRaizScraper

class ScraperFactory:
    @staticmethod
    def create_scrapers(config: dict):

        scrapers = []

        for fuente in config["scraping"]["fuentes"]:

            if not fuente["habilitado"]:
                continue

            nombre = fuente["nombre"].lower()

            if nombre == "metrocuadrado":
                scrapers.append(MetrocuadradoScraper(config))
            elif nombre == "fincaraiz":
                scrapers.append(FincaRaizScraper(config))
            elif nombre == "properati":
                scrapers.append(ProperatiScraper(config))

        return scrapers