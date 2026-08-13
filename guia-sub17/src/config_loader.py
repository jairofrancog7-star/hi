import json
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

class ConfigLoader:
    """Carga y valida la configuración de la guía desde archivos JSON o YAML."""

    @staticmethod
    def load_config(file_path: str) -> dict:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"El archivo de configuración no existe: {file_path}")

        ext = path.suffix.lower()
        with open(path, "r", encoding="utf-8-sig") as f:
            if ext in [".yaml", ".yml"]:
                if not HAS_YAML:
                    raise ImportError("Se requiere la librería 'PyYAML' para cargar archivos YAML.")
                return yaml.safe_load(f)
            elif ext == ".json":
                return json.load(f)
            else:
                raise ValueError(f"Formato de archivo no soportado: {ext}")
