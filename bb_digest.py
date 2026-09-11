#!/usr/bin/env python3
"""bb_digest.py — digest de tareas pendientes de Blackboard (solo stdlib, Python 3.9+).

Dos formas de leer Blackboard, elegí una:

  --ics URL   Cero credenciales. Usa el link "Share calendar" que Blackboard te da en
              Calendar > Settings (engranaje) > menú "..." > Share calendar.
              Solo trae título y fecha de entrega (sin curso, sin estado entregado/pendiente).

  --api       Datos completos. Usa la REST API pública de Blackboard con la cookie de sesión
              del navegador (~/.bb-session.json, la escribe bb_session.py; o $BB_COOKIE).
              Sabe el curso, la fecha Y si ya entregaste.

Entrega opcional del mensaje:
  --send whatsapp --to <jid>   POST al bridge local ($WA_BRIDGE_URL, default http://localhost:8080/api/send)
  --send telegram              necesita $TG_BOT_TOKEN y $TG_CHAT_ID

Exit codes: 0 ok · 2 uso incorrecto · 3 sesión vencida (correr bb_session.py) · 4 error de red/API
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TZ = ZoneInfo(os.environ.get("BB_TZ", "America/New_York"))
HOST = os.environ.get("BB_HOST", "gannon.blackboard.com")
SESSION_FILE = os.path.expanduser(os.environ.get("BB_SESSION_FILE", "~/.bb-session.json"))
MAX_WINDOW_DAYS = 16 * 7  # Blackboard: "since and until cannot span more than 16 weeks"
SUBMITTED = {"Graded", "NeedsGrading", "Completed", "NeedsGradingAgain"}

DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


class SessionExpired(Exception):
    pass


class ApiError(Exception):
    pass


# ----------------------------------------------------------------------------- http
UA = "bb-digest/1.0 (+https://github.com/Hec-M12/bb-digest)"  # sin User-Agent, el WAF de Blackboard deja la conexión colgada


def http(url, headers=None, data=None, timeout=30):
    hdrs = {"User-Agent": UA, **(headers or {})}
    req = urllib.request.Request(url, headers=hdrs, data=data)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


# ----------------------------------------------------------------------------- ICS
def parse_ics_dt(value, tzid=None):
    """'20260910T150000' + TZID, '20260910T190000Z', o '20260910' (todo el día)."""
    if value.endswith("Z"):
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).astimezone(TZ)
    zone = TZ
    if tzid:
        try:
            zone = ZoneInfo(tzid)
        except Exception:
            pass
    if len(value) == 8:
        return datetime.strptime(value, "%Y%m%d").replace(tzinfo=zone)
    return datetime.strptime(value[:15], "%Y%m%dT%H%M%S").replace(tzinfo=zone)


def parse_ics(text):
    lines = text.replace("\r\n", "\n").split("\n")
    unfolded = []
    for ln in lines:  # RFC 5545: una línea que empieza con espacio continúa la anterior
        if ln[:1] in (" ", "\t") and unfolded:
            unfolded[-1] += ln[1:]
        else:
            unfolded.append(ln)
    events, cur = [], None
    for ln in unfolded:
        if ln == "BEGIN:VEVENT":
            cur = {}
        elif ln == "END:VEVENT":
            if cur is not None:
                events.append(cur)
            cur = None
        elif cur is not None and ":" in ln:
            key, val = ln.split(":", 1)
            name, _, params = key.partition(";")
            cur[name] = (val, dict(p.split("=", 1) for p in params.split(";") if "=" in p))
    items = []
    for ev in events:
        if "DTSTART" not in ev:
            continue
        val, params = ev["DTSTART"]
        uid = ev.get("UID", ("", {}))[0]
        m = re.search(r"(_\d+_\d+)$", uid)
        items.append({
            "title": ev.get("SUMMARY", ("(sin título)", {}))[0].replace("\\,", ",").replace("\;", ";"),
            "course": None,
            "due": parse_ics_dt(val, params.get("TZID")),
            "status": "unknown",
            "column_id": m.group(1) if m else None,
            "url": None,
        })
    return items


def ics_items(url):
    status, body = http(url)
    if status != 200:
        raise ApiError(f"ICS respondió HTTP {status}")
    return parse_ics(body)


# ----------------------------------------------------------------------------- REST API
class Blackboard:
    def __init__(self, host, cookie):
        self.host = host
        self.headers = {"Cookie": cookie, "Accept": "application/json"}

    def get(self, path, **params):
        if not path.startswith("/learn/api/public"):
            path = "/learn/api/public" + path
        url = f"https://{self.host}{path}"
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        status, body = http(url, self.headers)
        if status == 401:
            raise SessionExpired()
        if status >= 400:
            raise ApiError(f"HTTP {status} {path}: {body[:200]}")
        return json.loads(body) if body else {}

    def results(self, path, **params):
        page = self.get(path, **params)
        while True:
            for r in page.get("results", []):
                yield r
            nxt = page.get("paging", {}).get("nextPage")
            if not nxt:
                break
            page = self.get(nxt)


def short_course(name):
    """'26FACIS27701: 26FA Mobile Appl Devlp 1 01' -> 'CIS 277 · Mobile Appl Devlp 1'."""
    code, _, title = name.partition(": ")
    m = re.match(r"^\d{2}[A-Z]{2}([A-Z]{3})(\d{3})(\w+)$", code.strip())
    title = re.sub(r"^\d{2}[A-Z]{2}\s+", "", title.strip())
    title = re.sub(r"\s+\d{1,2}[A-Z]?$", "", title)  # sección: " 01", " 02", " 2E"
    if m:
        return f"{m.group(1)} {m.group(2)} · {title}" if title else f"{m.group(1)} {m.group(2)}"
    return title or name


def load_cookie():
    cookie = os.environ.get("BB_COOKIE")
    if cookie:
        return cookie
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE) as f:
            return json.load(f).get("cookie", "")
    return ""


def iso_utc(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def api_items(bb, now, days_ahead, overdue_days):
    total = days_ahead + overdue_days
    if total > MAX_WINDOW_DAYS:
        overdue_days = max(0, MAX_WINDOW_DAYS - days_ahead)
        print(f"aviso: ventana recortada a {MAX_WINDOW_DAYS} días (límite de Blackboard)", file=sys.stderr)
    me = bb.get("/v1/users/me")["id"]
    cal_names = {c["id"]: c["name"] for c in bb.results("/v1/calendars", limit=200)}
    since, until = now - timedelta(days=overdue_days), now + timedelta(days=days_ahead)
    items = []
    for it in bb.results("/v1/calendars/items", since=iso_utc(since), until=iso_utc(until), limit=200):
        if it.get("type") != "GradebookColumn":
            continue
        course_id, col_id = it["calendarId"], it["id"]
        try:
            rec = bb.get(f"/v2/courses/{course_id}/gradebook/columns/{col_id}/users/{me}")
            status = "submitted" if rec.get("status") in SUBMITTED else "pending"
        except ApiError:
            status = "unknown"
        due = datetime.strptime(it["start"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc).astimezone(TZ)
        items.append({
            "title": it["title"],
            "course": short_course(cal_names.get(course_id) or it.get("calendarName", "")),
            "due": due,
            "status": status,
            "column_id": col_id,
            "url": f"https://{bb.host}/ultra/courses/{course_id}/outline",
        })
    return items


# ----------------------------------------------------------------------------- format
def fmt_dt(dt):
    h = dt.strftime("%I:%M %p").lstrip("0")
    return f"{DIAS[dt.weekday()]} {dt.day} {MESES[dt.month - 1]} {h}"


def urgency(due, now):
    d = (due.date() - now.date()).days
    if d < 0:
        return "⚠️"
    if d == 0:
        return "🔴"
    if d <= 2:
        return "🟠"
    if d <= 7:
        return "🟡"
    return "⚪"


def fmt_text(items, now, days, pending_only=False):
    head = f"📚 Blackboard · {DIAS[now.weekday()]} {now.day} {MESES[now.month - 1]} · próximos {days} días"
    overdue = sorted((i for i in items if i["due"] < now and i["status"] == "pending"), key=lambda i: i["due"])
    upcoming = sorted((i for i in items if i["due"] >= now), key=lambda i: i["due"])
    if pending_only:
        upcoming = [i for i in upcoming if i["status"] != "submitted"]
    lines = [head]
    if overdue:
        lines.append("")
        lines.append("Vencidas sin entregar:")
        for i in overdue:
            lines.append(f"⚠️ {fmt_dt(i['due'])} · {i['title']}" + (f" — {i['course']}" if i["course"] else ""))
    lines.append("")
    if not upcoming:
        lines.append("Nada por entregar en esta ventana 🎉")
    for i in upcoming:
        tag = {"pending": " · ⏳ pendiente", "submitted": " · ✅ entregada"}.get(i["status"], "")
        course = f" — {i['course']}" if i["course"] else ""
        lines.append(f"{urgency(i['due'], now)} {fmt_dt(i['due'])} · {i['title']}{course}{tag}")
    return "\n".join(lines)


# ----------------------------------------------------------------------------- send
def send_whatsapp(text, to):
    url = os.environ.get("WA_BRIDGE_URL", "http://localhost:8080/api/send")
    data = json.dumps({"recipient": to, "message": text}).encode()
    status, body = http(url, {"Content-Type": "application/json"}, data)
    ok = status == 200 and json.loads(body or "{}").get("success", True)
    if not ok:
        raise ApiError(f"bridge whatsapp: HTTP {status} {body[:200]}")


def send_telegram(text):
    token, chat = os.environ.get("TG_BOT_TOKEN"), os.environ.get("TG_CHAT_ID")
    if not (token and chat):
        raise ApiError("faltan TG_BOT_TOKEN / TG_CHAT_ID")
    data = json.dumps({"chat_id": chat, "text": text}).encode()
    status, body = http(f"https://api.telegram.org/bot{token}/sendMessage", {"Content-Type": "application/json"}, data)
    if status != 200:
        raise ApiError(f"telegram: HTTP {status} {body[:200]}")


# ----------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--ics", metavar="URL", help="link 'Share calendar' de Blackboard")
    src.add_argument("--api", action="store_true", help="REST API con cookie de sesión")
    ap.add_argument("--days", type=int, default=7, help="días hacia adelante (default 7)")
    ap.add_argument("--overdue-days", type=int, default=14, help="cuántos días atrás buscar vencidas sin entregar (solo --api)")
    ap.add_argument("--pending-only", action="store_true", help="ocultar las ya entregadas")
    ap.add_argument("--json", action="store_true", help="salida JSON en vez de texto")
    ap.add_argument("--send", choices=["whatsapp", "telegram"])
    ap.add_argument("--to", help="JID de WhatsApp, ej. 50412345678@s.whatsapp.net")
    args = ap.parse_args(argv)

    if args.send == "whatsapp" and not args.to:
        ap.error("--send whatsapp necesita --to <jid>")

    now = datetime.now(TZ)
    try:
        if args.ics:
            items = ics_items(args.ics)
            horizon = now + timedelta(days=args.days)
            items = [i for i in items if now - timedelta(days=1) <= i["due"] <= horizon]
        else:
            cookie = load_cookie()
            if not cookie:
                print(f"No hay sesión. Corré: python3 bb_session.py --login   (escribe {SESSION_FILE})", file=sys.stderr)
                return 3
            items = api_items(Blackboard(HOST, cookie), now, args.days, args.overdue_days)
    except SessionExpired:
        print("Sesión de Blackboard vencida (401). Corré: python3 bb_session.py", file=sys.stderr)
        return 3
    except (ApiError, urllib.error.URLError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 4

    if args.json:
        out = [dict(i, due=i["due"].isoformat()) for i in items]
        print(json.dumps(out, ensure_ascii=False, indent=1))
    text = fmt_text(items, now, args.days, args.pending_only)
    if not args.json:
        print(text)
    if args.send:
        try:
            (send_whatsapp(text, args.to) if args.send == "whatsapp" else send_telegram(text))
            print(f"enviado por {args.send}", file=sys.stderr)
        except ApiError as e:
            print(f"error al enviar: {e}", file=sys.stderr)
            return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
