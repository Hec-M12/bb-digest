# bb-digest — lo que vence en Blackboard, todos los días en tu Telegram

Un mensaje a las 7 de la mañana con las tareas que vencen en los próximos 7 días. Corre solo,
gratis y para siempre, con GitHub Actions. No hace falta servidor, ni tarjeta, ni saber Python.

```
📚 Blackboard · vie 11 sep · próximos 7 días

🔴 vie 11 sep 11:59 PM · Quiz 3
🟠 dom 13 sep 3:00 PM · Assignment 2
🟡 jue 17 sep 11:59 AM · Lab Report 1
```

Solo avisa. No entrega nada por vos.

---

## Los 3 pasos

### 1. Fork

Botón **Fork** arriba a la derecha. Te queda una copia del repo en tu cuenta.

### 2. Cargá los 3 secrets

En **tu** fork: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.
Creá estos tres, uno por uno:

| Nombre | Qué va adentro |
|---|---|
| `ICS_URL` | el link del calendario de Blackboard (paso de abajo) |
| `TG_BOT_TOKEN` | el token que te da BotFather |
| `TG_CHAT_ID` | tu chat id de Telegram |

Los secrets no se ven ni siquiera para vos después de guardarlos, y no aparecen en los logs.

### 3. Corré el workflow a mano para probar

**Actions** → si te pide habilitarlas, dale a **I understand my workflows, go ahead and enable them**
→ elegí **Digest diario de Blackboard** a la izquierda → **Run workflow**.

Si todo está bien, el mensaje te llega a Telegram en menos de un minuto. A partir de ahí sale
solo todos los días.

---

## De dónde sacás el link ICS

1. Entrá a Blackboard → **Calendar**.
2. Engranaje (**Calendar Settings**) → menú **"..."** arriba a la derecha → **Share calendar** → **Copy**.
3. Te da algo así:
   `https://tuuniversidad.blackboard.com/webapps/calendar/calendarFeed/<token>/learn.ics`

**Ese link es tu contraseña.** Cualquiera que lo tenga ve tu calendario. Por eso va en un
secret y no pegado en el código. Si se te filtra, volvé a la misma pantalla y dale
**Regenerate Link**: el viejo deja de servir al instante.

## Cómo creás el bot de Telegram

1. Abrí Telegram y buscá **@BotFather**.
2. Mandale `/newbot`. Te pide un nombre y un username que termine en `bot`.
3. Te devuelve un token que se ve así: `8123456789:AAF...`. Ese es tu `TG_BOT_TOKEN`.
4. **Buscá tu bot por su username y mandale un mensaje cualquiera** (un "hola"). Sin esto el
   bot no te puede escribir: Telegram no deja que un bot inicie la conversación.
5. Para el `TG_CHAT_ID`, abrí en el navegador:
   `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
   Buscá `"chat":{"id":123456789` . Ese número es tu `TG_CHAT_ID`.

Si `getUpdates` devuelve `{"ok":true,"result":[]}`, es porque todavía no le escribiste al bot.
Volvé al paso 4.

---

## Lo que el ICS NO te dice

Esto hay que decirlo de frente: el calendario de Blackboard trae **cinco propiedades por
evento** y nada más.

`SUMMARY` (el título) · `DTSTART` (cuándo vence) · `DTEND` · `UID` · `DTSTAMP`

O sea que el digest te dice **qué** vence y **cuándo**, pero no:

- **de qué clase es** (el ICS no trae el curso)
- **si ya la entregaste** (por eso te va a seguir avisando de algo que ya subiste)
- **qué pide la tarea** (no hay `DESCRIPTION`, el enunciado no está en el ICS)

Y solo aparecen las tareas a las que el profe les puso fecha en Blackboard. Lo que anunció
de boca en clase no está.

Si necesitás el curso y el estado de entrega, hay un camino B: la REST API de Blackboard con
la cookie de tu sesión del navegador. Es bastante más trabajo (hay que renovar la cookie cada
vez que Microsoft pida MFA) y anda mejor corriendo en tu propia computadora que en la nube.
El script ya lo soporta con `--api`, pero empezá por el ICS y agregá esto solo si de verdad
te hace falta después de usarlo dos semanas.

## El gotcha de los 60 días

GitHub **apaga solo** los workflows programados cuando un repo pasa 60 días sin actividad. Si
un día dejan de llegarte los mensajes, es casi seguro esto: entrá a Actions y volvé a
habilitar el workflow.

Este repo ya trae la vacuna: un job `keepalive` que los lunes commitea un archivo `.keepalive`
con la fecha, y eso cuenta como actividad. No usa ninguna action de terceros, es un `git commit`
y nada más.

## La alternativa: n8n

Si ya tenés n8n corriendo (self-hosted, que es gratis y sin límite de ejecuciones), importá
`n8n-blackboard-digest.json` y listo: son 4 nodos, cron de 7am, bajar el ICS, armar el mensaje,
mandarlo. Pegás tu link en el nodo "Bajar calendario ICS" y tu chat id en el nodo de Telegram.

Ojo: **n8n Cloud ya no tiene plan gratis permanente**, solo 14 días de prueba. Si no tenés n8n
propio, quedate con GitHub Actions, que es lo que hace este repo.

## Probarlo sin tu calendario real

El repo trae `sample.ics`, un calendario inventado con 4 eventos (uno hoy, uno en 2 días, uno
en 6 y uno en 30). Sirve para ver que todo funciona antes de meter tu link real.

```bash
python3 test_bb_digest.py                                  # las pruebas, sin red ni credenciales
python3 -m http.server 8000 &                              # servís el sample
python3 bb_digest.py --ics http://localhost:8000/sample.ics --days 7
```

El script **no acepta rutas de archivo** (`file://` no le sirve), por eso hay que servirlo por
HTTP.

Desde Actions también podés probar sin tocar tus secrets: en **Run workflow** hay un campo
`ics_url`. Pegá ahí la URL cruda de tu propio `sample.ics`:
`https://raw.githubusercontent.com/<tu-usuario>/bb-digest/main/sample.ics`

Las fechas del sample envejecen. Para refrescarlas: `python3 make_sample_ics.py`.

## Cambiar la hora

En `.github/workflows/digest.yml`, la línea `- cron: "0 11 * * *"`. El cron de GitHub **está en
UTC**, siempre. `0 11` son las 7 AM en la costa este durante el horario de verano y las 6 AM en
invierno. Si querés las 7 clavadas todo el año, cambialo a `0 12` cuando arranque el horario
estándar en noviembre.

## La otra mitad: el peer

`peer-template/` es un asistente de estudio por clase que ya sabe cómo funciona tu curso: el
profesor, las office hours, cuánto pesa cada cosa, si acepta trabajo tarde. No necesita
hosting ni API key, es un documento de texto que cargás en NotebookLM, ChatGPT o Claude.
Instrucciones en [`peer-template/README.md`](peer-template/README.md).

El digest te dice qué vence. El peer te ayuda a hacerlo.

## Archivos

| | |
|---|---|
| `bb_digest.py` | el digest, solo stdlib, sin dependencias |
| `test_bb_digest.py` | las pruebas, contra `sample.ics` |
| `sample.ics` | calendario inventado para probar |
| `make_sample_ics.py` | regenera `sample.ics` con fechas de hoy |
| `.github/workflows/digest.yml` | el cron diario + el keepalive |
| `n8n-blackboard-digest.json` | el mismo digest, para n8n |
| `peer-template/` | el asistente de estudio por clase |

Requiere Python 3.9 o más nuevo. Cero paquetes que instalar.

Licencia MIT, ver [`LICENSE`](LICENSE).

---

## In English (short version)

**bb-digest** sends you a daily Telegram message at 7 AM with what is due in Blackboard over
the next 7 days. It runs on GitHub Actions, so there is no server and no cost.

**Setup, three steps:**

1. **Fork** this repo.
2. In your fork, go to **Settings → Secrets and variables → Actions** and add three repository
   secrets:
   - `ICS_URL` — your Blackboard calendar feed. Get it at Blackboard → Calendar → gear
     (Calendar Settings) → "..." menu → **Share calendar** → Copy. That link is a credential:
     anyone holding it can read your calendar. If it leaks, hit **Regenerate Link**.
   - `TG_BOT_TOKEN` — create a bot with **@BotFather** on Telegram (`/newbot`), it hands you
     the token.
   - `TG_CHAT_ID` — message your new bot first (bots cannot start a conversation), then open
     `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` and read the `"chat":{"id":...}` value.
3. Go to **Actions**, enable workflows if prompted, pick **Digest diario de Blackboard**, and
   hit **Run workflow**. The message should land in Telegram within a minute.

**Known limits.** The Blackboard ICS feed carries only `SUMMARY`, `DTSTART`, `DTEND`, `UID` and
`DTSTAMP`. So the digest knows *what* is due and *when*, but not which course it belongs to,
whether you already submitted it, or what the assignment actually asks. Only items the
professor gave a due date to in Blackboard show up. For course and submission status you would
need the Blackboard REST API with a browser session cookie (`--api`), which is real extra work
and runs better on your own machine than in the cloud.

**Scheduled workflows get disabled after 60 days of repo inactivity.** This repo ships a
`keepalive` job that commits a `.keepalive` file every Monday to prevent that. No third-party
actions involved.

Python 3.9+, standard library only, no dependencies. MIT licensed.
