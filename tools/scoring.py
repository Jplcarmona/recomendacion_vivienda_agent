def calcular_score(propiedad, criterios):
    score = 0.0
    peso_total = 0.0
    razones = []
    criterios_cumplidos = []
    criterios_fallidos = []

    # PRECIO (peso 30%)
    precio     = propiedad.get("precio")
    precio_max = criterios.get("precio_max", 999_999_999)
    precio_min = criterios.get("precio_min", 0)

    if precio:
        peso_total += 0.30
        if precio <= precio_max:
            # Mejor score cuanto más alejado del techo
            ratio = precio / precio_max
            puntos = 0.30 * (1.0 - ratio * 0.5)  # entre 0.15 y 0.30
            score += puntos
            criterios_cumplidos.append("precio")
            razones.append(f"precio dentro del rango (${precio/1_000_000:.0f}M)")
        elif precio <= precio_max * 1.10:
            score += 0.10
            criterios_fallidos.append("precio levemente alto")
            razones.append("precio ligeramente sobre el máximo")
        else:
            criterios_fallidos.append("precio alto")
            razones.append(f"precio supera el máximo en {((precio/precio_max)-1)*100:.0f}%")

    # ÁREA (peso 25%)
    area     = propiedad.get("area")
    area_min = criterios.get("area_min", 0)
    area_max = criterios.get("area_max", 9999)

    if area:
        peso_total += 0.25
        if area >= area_min:
            # Bonus proporcional al área extra sobre el mínimo
            exceso = min((area - area_min) / max(area_min, 1), 1.0)
            puntos = 0.20 + 0.05 * exceso
            score += puntos
            criterios_cumplidos.append("área")
            razones.append(f"{area}m² cumple mínimo de {area_min}m²")
        elif area >= area_min * 0.85:
            score += 0.10
            criterios_fallidos.append("área algo pequeña")
            razones.append(f"{area}m² ligeramente bajo el mínimo ({area_min}m²)")
        else:
            score += 0.02
            criterios_fallidos.append("área insuficiente")
            razones.append(f"{area}m² muy por debajo del mínimo ({area_min}m²)")

    # CUARTOS (peso 20%)
    req_cuartos = criterios.get("num_cuartos", 2)
    cuartos     = propiedad.get("cuartos")

    if cuartos is not None:
        peso_total += 0.20
        if cuartos >= req_cuartos:
            puntos = 0.20
            if cuartos == req_cuartos:
                razones.append(f"{cuartos} cuartos — exacto")
            else:
                razones.append(f"{cuartos} cuartos — supera el mínimo ({req_cuartos})")
            score += puntos
            criterios_cumplidos.append("cuartos")
        elif cuartos == req_cuartos - 1:
            score += 0.08
            criterios_fallidos.append(f"cuartos insuficientes ({cuartos}/{req_cuartos})")
            razones.append(f"falta 1 cuarto")
        else:
            criterios_fallidos.append(f"cuartos muy insuficientes ({cuartos}/{req_cuartos})")
            razones.append(f"faltan {req_cuartos - cuartos} cuartos")

    # BAÑOS (peso 10%)

    req_banos = criterios.get("num_banos")
    banos     = propiedad.get("banos")

    if req_banos and banos is not None:
        peso_total += 0.10
        if banos >= req_banos:
            score += 0.10
            criterios_cumplidos.append("baños")
            razones.append(f"{banos} baños cumple el mínimo")
        else:
            score += 0.03
            criterios_fallidos.append(f"baños insuficientes ({banos}/{req_banos})")

    # PARQUEADERO (peso 10%)

    if criterios.get("parqueadero"):
        peso_total += 0.10
        if propiedad.get("parqueadero") is True:
            score += 0.10
            criterios_cumplidos.append("parqueadero")
            razones.append("tiene parqueadero")
        elif propiedad.get("parqueadero") is None:
            score += 0.05
            criterios_fallidos.append("parqueadero no confirmado")
            razones.append("parqueadero no confirmado en el anuncio")
        else:
            criterios_fallidos.append("sin parqueadero")
            razones.append("no tiene parqueadero")

    # FUENTE CONFIABLE (peso 5%)

    if propiedad.get("url"):
        score += 0.05
        peso_total += 0.05
        criterios_cumplidos.append("URL verificable")

    # NORMALIZAR al rango real de pesos usados
    if peso_total > 0:
        score = score / peso_total
    
    score = max(0.05, min(1.0, round(score, 2)))

    return {
        "score": score,
        "razones": razones,
        "criterios_cumplidos": criterios_cumplidos,
        "criterios_fallidos": criterios_fallidos,
    }
    
def _score_categoria(categoria: str, titulo: str, descripcion: str):

    texto = f"{titulo} {descripcion}".lower()
    score = 0
    positivos = [
        "valorización",
        "inversión",
        "nuevo",
        "proyecto",
        "metro",
        "parque",
        "renovación",
        "desarrollo",
        "comercio",
        "turismo",
    ]
    negativos = [
        "hurto",
        "robo",
        "homicidio",
        "deslizamiento",
        "inundación",
        "contaminación",
        "crimen",
    ]

    for p in positivos:
        if p in texto:
            score += 2
    for n in negativos:
        if n in texto:
            score -= 3
    if categoria == "valorizacion":
        score += 2

    return score