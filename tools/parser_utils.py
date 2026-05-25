import re

class ParserUtils:
    @staticmethod
    def limpiar_texto(texto: str) -> str:
        if not texto:
            return ""

        texto = texto.replace("\n", " ")
        texto = texto.replace("\t", " ")
        texto = re.sub(r"\s+", " ", texto)
        return texto.strip()

    @staticmethod
    def extraer_precio(texto: str):
        try:
            texto = texto.lower()
            texto = texto.replace(".", "")

            patrones = [
                r"\$\s?([\d]{6,12})",
                r"([\d]+)\s?millones",
                r"([\d]+)\s?m",
                r"cop\s?([\d]+)"
            ]

            for patron in patrones:
                match = re.search(patron,texto,re.IGNORECASE)

                if match:
                    valor = int(match.group(1))
                    if valor < 10000:
                        valor *= 1_000_000
                    return valor

        except Exception:
            pass

        return None

    @staticmethod
    def extraer_area(texto: str):
        try:
            patrones = [
                r"(\d+)\s?m²",
                r"(\d+)\s?mts",
                r"(\d+)\s?metros"
            ]

            for patron in patrones:
                match = re.search(patron,texto,re.IGNORECASE)
                if match:
                    return int(match.group(1))

        except Exception:
            pass

        return None

    @staticmethod
    def extraer_habitaciones(texto: str):
        try:
            patrones = [
                r"(\d+)\s?habitaciones",
                r"(\d+)\s?hab",
                r"(\d+)\s?alcobas",
                r"(\d+)\s?hab\b",
                r"(\d+)\s?Habs",
                r"(\d+)\s?Hab\."
            ]
            for patron in patrones:
                match = re.search(patron, texto, re.IGNORECASE)
                if match:
                    return int(match.group(1))
                
        except Exception:
            pass
        
        return None

    @staticmethod
    def extraer_banos(texto: str):
        try:
            patrones = [
                r"(\d+)\s?baños",
                r"(\d+)\s?banos",
                r"(\d+)\s?bañ\.",
                r"(\d+)\s?ban\.",
                r"(\d+)\s?Baños",
                r"(\d+)\s?Baño\b",
            ]
            for patron in patrones:
                match = re.search(patron, texto, re.IGNORECASE)
                if match:
                    return int(match.group(1))
                
        except Exception:
            pass
        
        return None

    @staticmethod
    def detectar_parqueadero(texto: str):
        texto_lower = texto.lower()
        keywords = ["parqueadero", "garaje", "garage", "parking"]

        if any(k in texto_lower for k in keywords):
            return True
        
        return None
    
    @staticmethod
    def normalizar_region(region):
        region = region.lower()
        return region.strip()