import argparse
import sys
from .config_loader import ConfigLoader
from .export_pdf import PDFExporter

def main():
    parser = argparse.ArgumentParser(
        description="CLI para la compilación y generación automática de la Guía de Estudio."
    )
    parser.add_argument(
        "-c", "--config",
        required=True,
        help="Ruta al archivo de configuración (JSON o YAML) con los contenidos."
    )
    parser.add_argument(
        "-o", "--output",
        default="guia_salida.pdf",
        help="Ruta del archivo PDF de salida (por defecto: guia_salida.pdf)."
    )

    args = parser.parse_args()

    try:
        print(f"Cargando configuración desde: {args.config}")
        config_data = ConfigLoader.load_config(args.config)

        print(f"Generando documento PDF en: {args.output}")
        exporter = PDFExporter(args.output)
        archivo_generado = exporter.exportar_guia(config_data)

        print(f"¡Guía generada exitosamente: {archivo_generado}!")
    except Exception as e:
        print(f"Error durante la ejecución: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
