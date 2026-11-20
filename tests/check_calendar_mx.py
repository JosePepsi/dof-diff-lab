from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dof_diff_lab.calendar_mx import holiday_name, no_edition_basis


def main() -> None:
    expected = {
        date(2026, 1, 1): "Año Nuevo",
        date(2026, 2, 2): "Día de la Constitución",
        date(2026, 3, 16): "Natalicio de Benito Juárez",
        date(2026, 5, 1): "Día del Trabajo",
        date(2026, 9, 16): "Día de la Independencia",
        date(2026, 11, 16): "Día de la Revolución",
        date(2026, 12, 25): "Navidad",
        date(2024, 10, 1): "Transmisión del Poder Ejecutivo Federal",
        date(2030, 10, 1): "Transmisión del Poder Ejecutivo Federal",
    }
    for day, name in expected.items():
        assert holiday_name(day) == name, day
    # Vecinos que NO son feriado (incluye el 20 de nov. fijo y fechas conmemoradas).
    for day in (
        date(2026, 11, 15), date(2026, 11, 17), date(2026, 11, 20), date(2026, 11, 23),
        date(2026, 2, 5), date(2026, 2, 9), date(2026, 3, 21), date(2026, 3, 23),
        date(2026, 10, 1), date(2025, 10, 1), date(2027, 10, 1),
        date(2026, 12, 24), date(2026, 5, 2), date(2026, 9, 15),
    ):
        assert holiday_name(day) is None, day
    assert no_edition_basis(date(2026, 11, 14)) == "weekend"
    assert no_edition_basis(date(2026, 11, 15)) == "weekend"
    assert no_edition_basis(date(2026, 11, 16)) == "holiday:Día de la Revolución"
    assert no_edition_basis(date(2026, 11, 17)) is None
    print("calendar_mx ok")


if __name__ == "__main__":
    main()
