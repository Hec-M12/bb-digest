# peer-template — tu compañero de estudio por clase, sin pagar nada

El digest te avisa **qué vence**. Esto es la otra mitad: un asistente que ya sabe
**cómo funciona tu clase** antes de que le preguntes nada. Quién es el profesor, cuándo
son las office hours, cuánto pesa cada cosa en la nota, si acepta trabajo tarde, y en qué
andás vos.

No necesita servidor, ni cron, ni API key. Es texto. Lo único que cuesta es mantenerlo.

## Por qué vale la pena

Sin esto, cada vez que abrís un chat arrancás de cero: "tengo una clase de sistemas
operativos, el profe pide...". Con esto, pegás un documento una vez y a partir de ahí
preguntás directo: "me queda tiempo de entregar el lab 3 tarde sin que me mate la nota".

El valor NO está en la herramienta. Está en el documento. Si lo llenás a medias, el
asistente te va a mentir con fechas viejas, que es peor que no tenerlo.

## Estructura: una carpeta por clase

```
MI-CLASE/
├── CLAUDE.md          <- el documento importante (el contexto de la clase)
├── syllabus/          <- el sílabo en PDF o texto, tal como lo subió el profe
├── assignments/       <- una subcarpeta por tarea, con el enunciado y tu trabajo
└── notes/             <- apuntes en vivo, un archivo por fecha: 2026-09-11.md
```

Copiá `CLASE-plantilla/` una vez por clase y renombrala. El archivo se llama `CLAUDE.md`
por costumbre de Claude Code, pero es un `.md` común: si no usás Claude Code, renombralo a
`contexto.md` y listo.

## Dónde cargarlo (las tres opciones gratis)

### 1. NotebookLM (google.com/notebooklm) — la recomendada

Un notebook por clase. Subís el sílabo en PDF, el `CLAUDE.md` y los apuntes como fuentes.
Acepta hasta 50 fuentes por notebook y hace OCR, así que un sílabo escaneado también sirve.

No hace falta pegar el system prompt: NotebookLM responde apoyado en los documentos, que es
justo lo que queremos. Si querés igual, pegá `system-prompt.md` como una fuente más.

Ventaja real: te cita de qué documento salió cada respuesta. Cuando dice "no acepta trabajo
tarde", podés hacer clic y ver la línea del sílabo.

### 2. ChatGPT free, con Projects

Creá un proyecto por clase. En las instrucciones del proyecto pegás `system-prompt.md` más
el contenido de tu `CLAUDE.md`. Subís los archivos (el plan gratis permite 5 archivos por
proyecto, así que priorizá el sílabo).

### 3. Claude.ai, con Projects

Mismo esquema: un proyecto por clase, `system-prompt.md` + `CLAUDE.md` en las custom
instructions, el sílabo en el knowledge.

Aviso: al 2026-09-11 la documentación de Anthropic y la página de precios se contradicen
sobre si Projects está disponible en cuentas gratis. Entrá con tu cuenta y fijate antes de
armar todo encima. Si no lo tenés, usá NotebookLM.

### Para código: Copilot Student

Si sos estudiante, GitHub te da el Student Developer Pack y con él "Copilot Student"
(completions ilimitadas). Eso reemplaza la parte de escribir código, no la del contexto.
Las dos cosas son complementarias: Copilot no sabe cuándo vence tu lab.

## Cómo mantenerlo sin que se pudra

Esto es lo que de verdad decide si funciona o no:

- **Al empezar el semestre (una vez, 30 min por clase):** llenás `CLAUDE.md` leyendo el
  sílabo. Especialmente la tabla de pesos y la política de trabajo tarde.
- **Después de cada clase (2 min):** un archivo nuevo en `notes/YYYY-MM-DD.md` con lo que
  dijo el profe. Lo que anuncia en clase y no está en el sílabo es justo lo que después no
  te acordás.
- **Cuando cambia una fecha (30 seg):** la corregís en `CLAUDE.md`. Una fecha vieja ahí es
  peor que ninguna fecha.
- **Los open loops:** la sección de abajo del `CLAUDE.md`. Es tu lista de "esto quedó sin
  resolver". Tacharla da más resultado que cualquier app de tareas.

Si en dos semanas no abriste `notes/`, no pasa nada: el `CLAUDE.md` con el sílabo bien
cargado ya te sirve solo. Empezá por ahí.

## Archivos de esta carpeta

- `CLASE-plantilla/CLAUDE.md` — el esqueleto a llenar, con comentarios de qué va en cada parte.
- `system-prompt.md` — el texto para pegar como instrucciones en ChatGPT o Claude.
