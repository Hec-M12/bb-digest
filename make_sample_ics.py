#!/usr/bin/env python3
"""Regenera sample.ics con fechas relativas a HOY (solo stdlib).

El sample que viene en el repo se generó el día que se publicó, así que sus
fechas envejecen. Corré esto cuando quieras volver a ver los 4 eventos vivos:

    python3 make_sample_ics.py

Genera 4 eventos: uno hoy, uno en 2 días, uno en 6 días y uno en 30 días.
Los tres primeros caen dentro de la ventana de 7 días, el cuarto queda afuera
a propósito para probar el filtro.
"""
from datetime import datetime, timedelta
from pathlib import Path

TZID = "America/New_York"
OUT = Path(__file__).with_name("sample.ics")

# (uid, título, días desde hoy, hora, minuto)
EVENTOS = [
    ("sample-hoy@bb-digest", "Quiz 3 (evento de HOY)", 0, 23, 59),
    ("sample-en-2-dias@bb-digest", "Assignment 2 (en 2 dias)", 2, 15, 0),
    ("sample-en-6-dias@bb-digest", "Lab Report 1 (en 6 dias)", 6, 11, 59),
    ("sample-en-30-dias@bb-digest", "Midterm Project (en 30 dias)", 30, 13, 0),
]


def main():
    hoy = datetime.now().date()
    stamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    lineas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//bb-digest//sample//ES",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:bb-digest sample (datos inventados)",
    ]
    for uid, titulo, delta, hh, mm in EVENTOS:
        d = hoy + timedelta(days=delta)
        lineas += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{stamp}",
            f"SUMMARY:{titulo}",
            f"DTSTART;TZID={TZID}:{d:%Y%m%d}T{hh:02d}{mm:02d}00",
            f"DTEND;TZID={TZID}:{d:%Y%m%d}T{hh:02d}{mm:02d}00",
            "END:VEVENT",
        ]
    lineas.append("END:VCALENDAR")
    OUT.write_text("\r\n".join(lineas) + "\r\n", encoding="utf-8")
    print(f"escrito {OUT} con {len(EVENTOS)} eventos (hoy = {hoy})")


if __name__ == "__main__":
    main()
