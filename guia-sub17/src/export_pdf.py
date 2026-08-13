from pathlib import Path
try:
    from .layout import Cursor, Modelo_Paginas
    from .draw import CanvasVectorial
except ImportError:
    from layout import Cursor, Modelo_Paginas
    from draw import CanvasVectorial

class PDFExporter:
    """Gestiona la compilación y exportación de la guía a formato PDF."""

    def __init__(self, output_path: str, pageSize: tuple = (595.27, 841.89)):
        self.output_path = Path(output_path)
        self.pageSize = pageSize
        self.canvas = CanvasVectorial(pageSize[0], pageSize[1])

    def exportar_guia(self, estructura_contenido: dict):
        cursor = Cursor()
        modelo = Modelo_Paginas(cursor)

        # Generar Portada
        portada_data = estructura_contenido.get("portada", {})
        modelo.agregar_portada(
            titulo=portada_data.get("titulo", "Guía de Estudio"),
            subtitulo=portada_data.get("subtitulo", "Edición Oficial")
        )

        # Generar Índice Dinámico
        modelo.agregar_indice(estructura_contenido.get("capitulos", []))

        # Generar Capítulos y Contenido
        for cap in estructura_contenido.get("capitulos", []):
            modelo.fijar_capitulo(cap.get("id"), cap.get("titulo"))
            for seccion in cap.get("secciones", []):
                modelo.agregar_bloque_texto(seccion.get("texto", ""))

        # Compilar y guardar salida vectorial/PDF
        self.canvas.guardar(str(self.output_path))
        return str(self.output_path)
