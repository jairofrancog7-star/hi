from pathlib import Path

class CanvasVectorial:
    """Gestiona el lienzo vectorial para el renderizado de elementos gráficos."""
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

    def guardar(self, output_path: str):
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("Documento generado exitosamente mediante Canvas Vectorial.")
        print(f"-> Archivo guardado correctamente en: {output_path}")
