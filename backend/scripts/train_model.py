"""
Script de entrenamiento del modelo ML — NutricioNar
=====================================================
Wrapper CLI para ml/train.py. Ejecutar desde la raíz del backend.

Uso:
    python scripts/train_model.py --file data/dataset_sintetico_maule.xlsx
    python scripts/train_model.py --file data/dataset_sintetico_maule.xlsx --eval
"""

import sys
from pathlib import Path

# Asegurar que el directorio raíz del backend esté en el path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.train import entrenar  # noqa: E402

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Entrena el modelo de riesgo nutricional de NutricioNar"
    )
    parser.add_argument(
        "--file", required=True,
        help="Ruta al archivo dataset_sintetico_maule.xlsx"
    )
    parser.add_argument(
        "--eval", action="store_true",
        help="Ejecutar validación cruzada 5-fold (más lento)"
    )
    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"Error: no se encontró el archivo: {args.file}")
        sys.exit(1)

    entrenar(args.file, evaluar=args.eval)
