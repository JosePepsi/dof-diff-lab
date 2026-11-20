"""Dias de descanso obligatorio en Mexico (funcion pura, sin red).

Base legal: Ley Federal del Trabajo, art. 74 (reforma 2006 y fraccion IX,
reforma 2006/2022):
  I.   1 de enero.
  II.  Primer lunes de febrero (conmemora el 5 de febrero).
  III. Tercer lunes de marzo (conmemora el 21 de marzo).
  IV.  1 de mayo.
  V.   16 de septiembre.
  VI.  Tercer lunes de noviembre (conmemora el 20 de noviembre).
  VII. 1 de octubre de cada seis anos (transmision del Poder Ejecutivo
       Federal); la primera ocurrencia vigente es 2024.
  VIII. 25 de diciembre.

Uso: el monitor solo acepta "sin edicion" un dia habil si es feriado oficial
y las fuentes oficiales no devolvieron notas. Esto NO afirma que el DOF no
publique en feriados (puede haber ediciones extraordinarias): solo habilita
la rama de "ausencia confirmada" cuando el contenido oficial esta vacio.
"""
from __future__ import annotations

from datetime import date, timedelta


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def holiday_name(day: date) -> str | None:
    """Nombre del feriado obligatorio (LFT art. 74) o None."""
    year = day.year
    if day == date(year, 1, 1):
        return "Año Nuevo"
    if day == _nth_weekday(year, 2, 0, 1):
        return "Día de la Constitución"
    if day == _nth_weekday(year, 3, 0, 3):
        return "Natalicio de Benito Juárez"
    if day == date(year, 5, 1):
        return "Día del Trabajo"
    if day == date(year, 9, 16):
        return "Día de la Independencia"
    if day == date(year, 10, 1) and year >= 2024 and (year - 2024) % 6 == 0:
        return "Transmisión del Poder Ejecutivo Federal"
    if day == _nth_weekday(year, 11, 0, 3):
        return "Día de la Revolución"
    if day == date(year, 12, 25):
        return "Navidad"
    return None


def no_edition_basis(day: date) -> str | None:
    """'weekend', 'holiday:<nombre>' o None si es un dia habil ordinario."""
    if day.weekday() >= 5:
        return "weekend"
    name = holiday_name(day)
    return f"holiday:{name}" if name else None
