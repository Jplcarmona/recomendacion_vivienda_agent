import os
import json
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from graph import construir_grafo
from state import estado_inicial

load_dotenv()

console = Console()

def formatear_precio(precio: float) -> str:
    """Formatea precio en COP de forma legible."""
    if precio >= 1_000_000_000:
        return f"${precio/1_000_000_000:.1f}B"
    elif precio >= 1_000_000:
        return f"${precio/1_000_000:.0f}M"
    return f"${precio:,.0f}"

def imprimir_resultado_final(state: dict):
    """Imprime el resultado final de forma formateada."""
    console.print("\n")
    console.print(Panel.fit(
        "SISTEMA DE RECOMENDACIÓN DE VIVIENDA — RESULTADO FINAL",
        style="bold green"
    ))
    
    # Resumen del proceso
    console.print(f"\nResumen del proceso:")
    console.print(f"Iteraciones realizadas: {state.get('iteracion_actual', 0)}")
    console.print(f"Nivel de relajación aplicado: {state.get('nivel_relajacion', 0)}")
    console.print(f"Estado final: {state.get('resultado_evaluacion', 'desconocido').upper()}")
    
    # Modificaciones realizadas
    modificaciones = state.get("modificaciones_realizadas", [])
    if modificaciones:
        console.print("\n🔧 Modificaciones a los criterios originales:")
        for mod in modificaciones:
            console.print(f" • {mod}")
    
    # Propiedades recomendadas
    propiedades = state.get("resultado_final") or state.get("propiedades_evaluadas", [])[:3]
    
    if propiedades:
        console.print(f"\nTop {len(propiedades)} propiedades recomendadas:\n")
        
        for i, prop in enumerate(propiedades, 1):
            score = prop.get("score", 0)
            barras = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            
            console.print(Panel(
                f"[bold]{prop.get('titulo', 'Sin título')}[/bold]\n"
                f"Score: [{barras}] {score:.0%}\n"
                f"Precio: {formatear_precio(prop.get('precio', 0))} COP\n"
                f"Área: {prop.get('area', 0)} m²\n"
                f"Cuartos: {prop.get('cuartos', 0)} | Baños: {prop.get('banos', 0)}\n"
                f"Ubicación: {prop.get('barrio', '')}, {prop.get('ciudad', '')}\n"
                f"Link: {prop.get('url', 'N/A')}\n\n"
                f"Cumple: {', '.join(prop.get('criterios_cumplidos', []))}\n"
                f"No cumple: {', '.join(prop.get('criterios_fallidos', [])) or 'ninguno'}",
                title=f"#{i}",
                style="blue" if i == 1 else "cyan"
            ))
    else:
        console.print("\n No se encontraron propiedades que cumplan los criterios mínimos.")
    
    # Explicación final
    explicacion = state.get("explicacion_final")
    if explicacion:
        console.print(Panel(
            explicacion,
            title=" Análisis del asesor",
            style="yellow"
        ))

def ejecutar_sistema(input_usuario: str, debug: bool = False):
    """
    Función principal para ejecutar el sistema.
    """
    console.print(Panel.fit(
        f"Iniciando búsqueda para:\n'{input_usuario}'",
        style="bold blue"
    ))
    
    # Construir grafo
    app = construir_grafo()
    
    # Estado inicial
    estado = estado_inicial(input_usuario)
    
    # Ejecutar el grafo
    console.print("\n Ejecutando el sistema de decisión...\n")
    
    try:
        resultado = app.invoke(estado)
        
        if debug:
            console.print("\n[dim]DEBUG — Estado final completo:[/dim]")
            console.print(json.dumps(
                {k: v for k, v in resultado.items() 
                 if k not in ["propiedades_brutas", "propiedades_filtradas"]},
                indent=2, 
                ensure_ascii=False,
                default=str
            ))
        
        imprimir_resultado_final(resultado)
        return resultado
        
    except Exception as e:
        console.print(f"\nError en la ejecución: {e}")
        raise

if __name__ == "__main__":
    # Ejemplo de uso 
    CASO_PRUEBA = """
    Busco apartamento en Medellín, idealmente en el Estadio o en El Poblado o Aranjuez.
    Máximo 400 millones de pesos. Necesito al menos 2 habitaciones y 2 baños.
    Área mínima de 70 metros cuadrados. Sería ideal que tuviera parqueadero.
    Somos una familia de 3 personas.
    """
    
    resultado = ejecutar_sistema(CASO_PRUEBA, debug=False)