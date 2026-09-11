#!/usr/bin/env python3
"""Prueba bb_digest.py contra sample.ics, sin credenciales ni red.

Corré:  python3 test_bb_digest.py

El test se ancla al evento con UID 'sample-hoy@bb-digest': toma SU fecha como
"hoy", así que sigue pasando aunque regeneres sample.ics con make_sample_ics.py.
"""
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bb_digest as m

SAMPLE = Path(__file__).resolve().parent / "sample.ics"
fallas = []


def check(cond, msg):
    if cond:
        print(f"  ok   {msg}")
    else:
        print(f"  FALLA {msg}")
        fallas.append(msg)


print("bb-digest · pruebas con sample.ics\n")

# --- parseo del ICS -----------------------------------------------------------
items = m.parse_ics(SAMPLE.read_text(encoding="utf-8"))
check(len(items) == 4, f"el sample trae 4 eventos (trae {len(items)})")

titulos = sorted(i["title"] for i in items)
check(any("HOY" in t for t in titulos), "hay un evento de hoy")
check(all(i["course"] is None for i in items), "el ICS no trae curso (limite conocido)")
check(all(i["status"] == "unknown" for i in items), "el ICS no trae estado de entrega")

# "hoy" = el dia del evento ancla, a las 9 de la manana
ancla = next(i for i in items if "HOY" in i["title"])
now = ancla["due"].replace(hour=9, minute=0, second=0, microsecond=0)

# --- filtro de ventana (lo mismo que hace main() con --days) -------------------
def ventana(dias):
    horizonte = now + timedelta(days=dias)
    return [i for i in items if now - timedelta(days=1) <= i["due"] <= horizonte]


v7 = ventana(7)
check(len(v7) == 3, f"con --days 7 quedan 3 eventos (quedan {len(v7)})")
check(not any("30 dias" in i["title"] for i in v7), "el evento a 30 dias queda afuera de la ventana de 7")

v40 = ventana(40)
check(len(v40) == 4, f"con --days 40 entran los 4 (entran {len(v40)})")

# --- formato del mensaje ------------------------------------------------------
texto = m.fmt_text(v7, now, 7)
check(texto.startswith("📚 Blackboard"), "el mensaje arranca con el encabezado")
check("próximos 7 días" in texto, "el encabezado dice la ventana")
check("🔴" in texto, "lo que vence hoy sale en rojo")
check("🟠" in texto, "lo que vence en 2 dias sale en naranja")
check("🟡" in texto, "lo que vence en 6 dias sale en amarillo")
check("Quiz 3" in texto and "Lab Report 1" in texto, "los titulos aparecen en el mensaje")

vacio = m.fmt_text([], now, 7)
check("Nada por entregar" in vacio, "sin tareas, avisa que no hay nada")

# --- utilidades de formato ----------------------------------------------------
check(m.short_course("26FAABC10101: 26FA Curso De Prueba 01") == "ABC 101 · Curso De Prueba",
      "short_course limpia el codigo y la seccion")
check(m.urgency(now, now) == "🔴", "urgency: vence hoy")
check(m.urgency(now + timedelta(days=1), now) == "🟠", "urgency: vence manana")
check(m.urgency(now + timedelta(days=5), now) == "🟡", "urgency: vence esta semana")
check(m.urgency(now + timedelta(days=20), now) == "⚪", "urgency: falta mucho")
check(m.urgency(now - timedelta(days=1), now) == "⚠️", "urgency: ya vencio")

# --- plegado de lineas del RFC 5545 -------------------------------------------
plegado = (
    "BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nUID:x@y\r\n"
    "SUMMARY:Titulo muy largo que el servidor\r\n  parte en dos lineas\r\n"
    "DTSTART;TZID=America/New_York:20260101T120000\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
)
p = m.parse_ics(plegado)
check(p and p[0]["title"] == "Titulo muy largo que el servidor parte en dos lineas",
      "une las lineas plegadas del ICS")

print("\n--- mensaje de ejemplo ---")
print(texto)
print("--------------------------\n")

if fallas:
    print(f"{len(fallas)} PRUEBA(S) FALLARON")
    sys.exit(1)
print("TODAS LAS PRUEBAS PASARON")
