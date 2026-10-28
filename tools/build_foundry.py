#!/usr/bin/env python3
"""Genera el contenido Foundry de MR- EIDOLON: una aventura (Adventure) por idioma desde la carpeta de trabajo.

Fuente: «Trabajo EIDOLON» (texto/<idioma>/, img/, salida/<idioma>/*.pdf y tools/mapas.py).
Salida: assets/ · _data/aventura-<idioma>.json · content/direccion-<idioma>.json
Uso: python3 tools/build_foundry.py     (antes: EIDOLON_LANG=<idioma> python3 "Trabajo EIDOLON/tools/build.py" todo)
     luego `npm run build` compila _data/ a packs/ y crea el zip.
"""
import hashlib, html, importlib, json, os, re, shutil, sys
from pathlib import Path

import fitz
import markdown
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MODID = "mr-eidolon"
MOD = f"modules/{MODID}"
TRAB = Path(os.environ.get("EIDOLON_TRABAJO", "/Volumes/Datos_Dock/FoundryVTT/Trabajo EIDOLON"))
NADIR_AUDIO = Path(os.environ.get("NADIR_AUDIO", ROOT.parent / "mr-nadir" / "assets" / "audio"))
A = ROOT / "assets"
LANGS = ("es", "en")
sys.path.insert(0, str(TRAB / "tools"))
import mapas  # noqa: E402

CHAR = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def fid(key):
    h = int(hashlib.sha256(("eidolon:" + key).encode()).hexdigest(), 16)
    return "".join(CHAR[(h >> (6 * i)) % 62] for i in range(16))


def esc(t):
    return html.escape(str(t))


def md(t):
    return markdown.markdown(t, extensions=["tables"])


def ilm(t):
    return re.sub(r"^<p>|</p>$", "", md(t).strip())


def webp(src, dst, ancho=None, q=84, caja=None):
    dst.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGB")
    if caja:
        im = im.crop(caja)
    if ancho and im.width > ancho:
        im = im.resize((ancho, round(im.height * ancho / im.width)), Image.LANCZOS)
    im.save(dst, "WEBP", quality=q, method=6)
    return im.size


# ------------------------------------------------------------------ textos fijos de Foundry por idioma
L = {
 "es": {
  "titulo": "MR- EIDOLON: Nadie recuerda morir", "lema": "Nadie recuerda morir",
  "carp": {"manual": "EIDOLON · Dosier del Guardián", "docs": "EIDOLON · Documentos de mesa", "tripu": "EIDOLON · Tripulación (pregenerados)",
           "pnj": "EIDOLON · Supervivientes", "amenaza": "EIDOLON · Amenaza", "mapas": "EIDOLON · Planos", "imagen": "EIDOLON · Escenas de imagen",
           "audio": "EIDOLON · Banda sonora", "tablas": "EIDOLON · Tablas", "macros": "EIDOLON"},
  "planos": "Planos de LIMEN-9", "plano_trip": "Cubierta {d} · tripulación", "plano_gm": "Cubierta {d} · Guardián",
  "escena_mapa": "LIMEN-9 · Cubierta {d}", "pantalla": "Pantalla del Guardián", "registro": "Registro de Ausencias", "lecturas": "Lecturas para la tripulación",
  "doc_texto": "Texto del documento", "doc_imagen": "Documento", "entrega": "Cuándo se entrega",
  "bio": {"rol": "Puesto", "edad": "Edad", "trasto": "Trasto", "parche": "Parche", "vinculo": "Vínculo", "secreto": "Secreto personal", "decision": "Decisión difícil",
          "conf": "Solo para quien lleva este personaje."},
  "botones": {"ver": "Ver la escena", "mostrar": "Mostrar a todos", "volver": "Volver a la cubierta {d}"},
  "sup": {"donde": "Dónde está", "voz": "Cómo habla", "relaciones": "Relaciones", "pistas": "Lo que puede aportar", "copia": "Si es una copia", "parche": "Parche"},
  "rango": {10: "Trained", 15: "Expert", 20: "Master"},
  "irA": "Ir a la cubierta {d}", "tabla_copia": "Primera copia latente", "tabla_copia_txt": "Sortéala antes de jugar y anótala en el Registro de Ausencias.",
  "sorteo": "Sorteo de sustitución", "pistola": "Pistola de servicio", "filamento": "Filamento", "membrana": "Presión de membrana",
  "musica": "EIDOLON · Música", "efectos": "EIDOLON · Efectos (Guardián)",
  "esc": {"portada": "EIDOLON", "vesperina": "Vesperina (V-17)", "cuarentena": "02 · Vestíbulo de cuarentena", "laboratorio": "10 · Analítica HERMES",
          "nido": "09 · Nido Cero", "morgue": "12 · Morgue", "reactor": "14 · Reactor", "hangar": "16 · Hangar Barquero", "pasillo": "15-B · Conductos"},
  "desc": "<p><b>EIDOLON</b> — aventura de horror científico para Mothership 1e (3–6 jugadores, una sesión de 2 h). Dosier del Guardián completo, 10 documentos de mesa, 6 pregenerados, 8 supervivientes, planos con muros y puertas, y escenas de imagen con música y efectos para MR- Dirección.</p>",
 },
 "en": {
  "titulo": "MR- EIDOLON: No One Remembers Dying", "lema": "No One Remembers Dying",
  "carp": {"manual": "EIDOLON · Warden’s Dossier", "docs": "EIDOLON · Table Handouts", "tripu": "EIDOLON · Crew (pregenerated)",
           "pnj": "EIDOLON · Survivors", "amenaza": "EIDOLON · Threat", "mapas": "EIDOLON · Deck Plans", "imagen": "EIDOLON · Image Scenes",
           "audio": "EIDOLON · Soundtrack", "tablas": "EIDOLON · Tables", "macros": "EIDOLON"},
  "planos": "LIMEN-9 Deck Plans", "plano_trip": "Deck {d} · crew", "plano_gm": "Deck {d} · Warden",
  "escena_mapa": "LIMEN-9 · Deck {d}", "pantalla": "Warden’s Screen", "registro": "Absence Log", "lecturas": "Read-aloud Text",
  "doc_texto": "Document text", "doc_imagen": "Document", "entrega": "When to hand it out",
  "bio": {"rol": "Position", "edad": "Age", "trasto": "Trinket", "parche": "Patch", "vinculo": "Bond", "secreto": "Personal secret", "decision": "Hard choice",
          "conf": "For the player of this character only."},
  "botones": {"ver": "View the scene", "mostrar": "Show to everyone", "volver": "Back to Deck {d}"},
  "sup": {"donde": "Where to find them", "voz": "How they talk", "relaciones": "Relationships", "pistas": "What they can offer", "copia": "If they are a copy", "parche": "Patch"},
  "rango": {10: "Trained", 15: "Expert", 20: "Master"},
  "irA": "Go to Deck {d}", "tabla_copia": "First Latent Copy", "tabla_copia_txt": "Roll before play and note the result in the Absence Log.",
  "sorteo": "Replacement Draw", "pistola": "Service pistol", "filamento": "Filament", "membrana": "Membrane pressure",
  "musica": "EIDOLON · Music", "efectos": "EIDOLON · Effects (Warden)",
  "esc": {"portada": "EIDOLON", "vesperina": "Vesperine (V-17)", "cuarentena": "02 · Quarantine Vestibule", "laboratorio": "10 · HERMES Analytics",
          "nido": "09 · Nest Zero", "morgue": "12 · Morgue", "reactor": "14 · Reactor", "hangar": "16 · Ferryman Hangar", "pasillo": "15-B · Ducts"},
  "desc": "<p><b>EIDOLON</b> — a science-horror adventure for Mothership 1e (3–6 players, one 2-hour session). Full Warden’s Dossier, 10 table handouts, 6 pregenerated characters, 8 survivors, deck plans with walls and doors, and image scenes with music and effects for MR- Dirección.</p>",
 },
}

# Audio original de la casa (sintetizado para MR- Nádir, misma licencia): clave → (archivo Nádir, nombre es, nombre en[, icono])
MUSICA = {"estacion": ("exploracion", "Estación LIMEN-9", "LIMEN-9 Station"), "turno": ("turno", "Turno de noche", "Night Shift"),
          "control": ("control", "Control central", "Central Control"), "conductos": ("galerias", "Conductos", "Ducts"),
          "nido": ("cria", "Nido Cero", "Nest Zero"), "tension": ("refugio", "Tensión", "Tension"), "reactor": ("bomba", "Reactor", "Reactor"),
          "huida": ("contrarreloj", "Cuenta atrás", "Countdown"), "eva": ("superficie", "Paseo EVA", "EVA Walk"), "final": ("final", "Lo que queda", "What Remains"),
          # propias de EIDOLON (tools/audio.py): None = no se copian de Nádir
          "cumpleanos": (None, "Cumpleaños en el intercomunicador", "Birthday on the Intercom"), "dormitorios": (None, "Literas vacías", "Empty Bunks"),
          "enfermeria": (None, "Enfermería", "Medbay"), "senal": (None, "La señal", "The Signal"), "carga": (None, "Bodega", "Cargo Hold"),
          "laboratorio": (None, "Serie HERMES", "HERMES Series"), "reciclaje": (None, "Reciclaje hídrico", "Water Reclamation"),
          "morgue": (None, "Cápsula 12-C", "Capsule 12-C"), "archivo": (None, "Protocolo ORFEO", "ORPHEUS Protocol"), "hangar": (None, "Barquero", "Ferryman")}
SFX = {"zumbido": ("hum", "Zumbido eléctrico", "Electrical hum", "bolt"), "ventilacion": ("ventilador", "Ventilación", "Ventilation", "fan"),
       "goteo": ("goteo", "Goteo", "Dripping", "droplet"), "raspado": ("raspado", "Raspado en el metal", "Scraping metal", "hand-back-fist"),
       "latido": ("cria-latido", "Pulso del Nido", "Nest pulse", "heart-pulse"), "alarma": ("alarma-lenta", "Alarma", "Alarm", "triangle-exclamation"),
       "presion": ("alarma-presion", "Alarma de presión", "Pressure alarm", "gauge-high"), "compuerta": ("compuerta", "Compuerta", "Hatch", "door-open"),
       "terminal": ("terminal", "Terminal", "Terminal", "terminal"), "radio": ("radio-estatica", "Estática de radio", "Radio static", "tower-broadcast"),
       "fuga": ("siseo", "Fuga de gas", "Gas leak", "wind"), "golpe": ("golpe-metal", "Golpe metálico", "Metal clang", "hammer"),
       "casco": ("casco-respiracion", "Respiración en el casco", "Helmet breathing", "user-astronaut"), "respiraciones": ("respiraciones", "Respiraciones", "Breathing", "lungs"),
       "temblor": ("temblor", "Temblor", "Tremor", "house-crack")}
MOTIVOS = [("tension", "tension", "Tensión", "Tension", "eye"), ("horror", "nido", "Horror", "Horror", "skull"),
           ("huida", "huida", "Huida", "Escape", "person-running"), ("exploracion", "estacion", "Exploración", "Exploration", "compass"),
           ("final", "final", "Epílogo", "Epilogue", "moon")]

# Escenas de imagen 16:9 sin personajes, una por ubicación (img/escenas/sNN.png; mientras falte, la ilustración antigua si la hay).
# clave → (imagen de reserva, página de lectura, música, efectos de escena, reparto, ambiente)
IMAGENES = {"portada": ("i_portada", "lectura:0", "estacion", ["radio"], [], "dim"),
            "vesperina": ("i_vesperina", "cap:01", "tension", ["zumbido"], [], "light"),
            "s01": (None, "sala:01", "cumpleanos", ["radio", "casco"], [], "dim"),
            "s02": ("i_cuarentena", "lectura:1", "turno", ["ventilacion", "respiraciones"], ["dalia"], "light"),
            "s03": (None, "sala:03", "dormitorios", ["ventilacion", "goteo"], [], "dim"),
            "s04": (None, "sala:04", "cumpleanos", ["zumbido", "radio"], ["rafi"], "dim"),
            "s05": (None, "sala:05", "enfermeria", ["zumbido", "respiraciones"], ["mara"], "light"),
            "s06": (None, "sala:06", "control", ["terminal", "ventilacion"], [], "dim"),
            "s07": (None, "sala:07", "senal", ["radio", "terminal"], ["noemi"], "dim"),
            "s08": (None, "sala:08", "carga", ["zumbido", "raspado"], ["edda"], "dim"),
            "s09": ("i_nido", "lectura:2", "nido", ["latido", "goteo"], ["forma"], "dark"),
            "s10": ("i_laboratorio", "sala:10", "laboratorio", ["terminal", "zumbido"], [], "light"),
            "s11": (None, "sala:11", "reciclaje", ["goteo", "fuga"], ["yara"], "dim"),
            "s12": ("i_morgue", "sala:12", "morgue", ["zumbido", "goteo"], [], "dim"),
            "s13": (None, "sala:13", "archivo", ["terminal", "zumbido"], ["simon"], "dim"),
            "s14": ("i_reactor", "sala:14", "reactor", ["zumbido", "fuga"], ["ivo"], "dim"),
            "s15": ("i_pasillo", "sala:15", "conductos", ["raspado", "goteo"], ["forma"], "dark"),
            "s16": ("i_hangar", "sala:16", "hangar", ["presion", "casco"], [], "dim"),
            "s17": (None, "sala:17", "eva", ["casco", "radio"], [], "dark")}
SALAS_DECK = {k: d for d, C in mapas.CUBIERTAS.items() for k in list(C["salas"]) + ([C["exterior"][0]] if C["exterior"] else [])}
MAPA_MUSICA = {"A": ("estacion", ["ventilacion", "zumbido"]), "B": ("conductos", ["zumbido", "goteo"])}
# En qué escena de imagen se entrega cada documento de mesa (según su «entrega»)
ENTREGA = {"01": "portada", "02": "s08", "03": "portada", "04": "s10", "05": "s10", "06": "s02", "07": "s07", "08": "s12", "09": "s13", "10": "s10"}

# Supervivientes (su mecánica y biografía están en texto/<idioma>/supervivientes.json)
PNJ = ("mara", "ivo", "noemi", "simon", "edda", "dalia", "rafi", "yara")
ELEGIBLES = ("mara", "ivo", "noemi", "simon", "edda")
DISP = {"dalia": 0}
CAJA_ESCENA = {"A": (40, 380, 3270, 2120), "B": (300, 640, 3200, 2070)}
GRID = 52           # 2 unidades de plano
HALF = mapas.U / 2  # rejilla de muros: media unidad


# ------------------------------------------------------------------ recursos comunes
def recursos():
    raw = TRAB / "img" / "raw"
    for img in ("i_portada", "i_vesperina", "i_nido", "i_cuarentena", "i_morgue", "i_pasillo", "i_laboratorio", "i_reactor", "i_hangar"):
        webp(raw / f"{img}.png", A / "art" / f"{img}.webp", 1920, 82)
    for k in IMAGENES:
        src = fuente_escena(k)
        if src:
            im = Image.open(src).convert("RGB")
            alto = round(im.width * 9 / 16)
            if alto < im.height:   # recorte 16:9 que conserva el suelo (más abajo que arriba)
                y0 = round((im.height - alto) * 0.6); im = im.crop((0, y0, im.width, y0 + alto))
            else:
                ancho = round(im.height * 16 / 9); x0 = (im.width - ancho) // 2; im = im.crop((x0, 0, x0 + ancho, im.height))
            (A / "scenes").mkdir(parents=True, exist_ok=True); (A / "thumbs").mkdir(parents=True, exist_ok=True)
            im.resize((1920, 1080), Image.LANCZOS).save(A / "scenes" / f"{k}.webp", "WEBP", quality=84, method=6)
            im.resize((400, 225), Image.LANCZOS).save(A / "thumbs" / f"{k}.webp", "WEBP", quality=78, method=6)
    for f in sorted(raw.glob("r[0-9][0-9].png")):
        im = Image.open(f)
        m = 0.02 if f.stem != "r17" else 0
        webp(f, A / "rooms" / f"{f.stem}.webp", 640, 80, (int(im.width * m), int(im.height * m), int(im.width * (1 - m)), int(im.height * (1 - m))))
    for pid in PNJ:
        webp(raw / f"p_{pid}.png", A / "portraits" / f"{pid}.webp", 900, 84)
    for i in range(1, 7):
        webp(TRAB / "img" / "orig" / f"02_p{i:02d}_0.png", A / "portraits" / f"pj{i:02d}.webp", None, 88)
    webp(raw / "c_forma.png", A / "portraits" / "forma.webp", 900, 84)
    im = Image.open(raw / "r09.png")
    webp(raw / "r09.png", A / "portraits" / "matriz.webp", 900, 84, (int(im.width * .2), int(im.height * .2), int(im.width * .8), int(im.height * .8)))
    for f in sorted((A / "portraits").glob("*.webp")):
        k = f.stem
        color = (13, 102, 112) if k.startswith("pj") else (184, 56, 42) if k in ("forma", "matriz") else (150, 160, 162)
        token_redondo(f, A / "tokens" / f"{k}.webp", color, 0.0 if k == "matriz" else 0.06)
    for f in sorted((TRAB / "img" / "figuras").glob("*.png")):
        if "." in f.stem:
            continue
        figura(f, A / "figures" / f"{f.stem}.webp")
    for d, caja in CAJA_ESCENA.items():
        webp(TRAB / "img" / "mapas" / f"{d}.jpg", A / "maps" / f"{d}.webp", None, 86, caja)
        webp(TRAB / "img" / "mapas" / f"{d}.jpg", A / "thumbs" / f"deck-{d}.webp", 400, 78, caja)
    for clave, (src, *_r) in list(MUSICA.items()) + list(SFX.items()):
        if src is None:
            continue
        carpeta = "musica" if clave in MUSICA else "sfx"
        dst = A / "audio" / carpeta / f"{clave}.ogg"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(NADIR_AUDIO / carpeta / f"{src}.ogg", dst)


def token_redondo(src, dst, color, arriba=0.06):
    """Token circular: cuadrado del retrato (desde arriba, donde está la cara) con aro de color y fondo transparente."""
    from PIL import ImageDraw
    im = Image.open(src).convert("RGB")
    lado = min(im.width, im.height)
    y0 = min(int(im.height * arriba), im.height - lado)
    im = im.crop(((im.width - lado) // 2, y0, (im.width - lado) // 2 + lado, y0 + lado)).resize((400, 400), Image.LANCZOS)
    out = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    m = Image.new("L", (400, 400), 0); ImageDraw.Draw(m).ellipse([6, 6, 394, 394], fill=255)
    out.paste(im, (0, 0), m)
    d = ImageDraw.Draw(out)
    d.ellipse([6, 6, 394, 394], outline=(10, 14, 17, 255), width=22)
    d.ellipse([10, 10, 390, 390], outline=color, width=12)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst, "WEBP", quality=90, method=6)


def fuente_escena(k):
    """Imagen de la escena: la nueva 16:9 sin personajes si existe; si no, la ilustración de reserva."""
    nueva = TRAB / "img" / "escenas" / f"{k}.png"
    if nueva.exists():
        return nueva
    reserva = IMAGENES[k][0]
    return TRAB / "img" / "raw" / f"{reserva}.png" if reserva else None


def figura(src, dst, lado=1024, visible=0.885, pie=0.055):
    """Figura de cuerpo entero (PNG con alfa) → lienzo cuadrado transparente: alto = 88,5 %, pies a 5,5 % del borde (MR- Dirección)."""
    im = Image.open(src).convert("RGBA")
    im = im.crop(im.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox())
    alto = round(lado * visible); ancho = round(im.width * alto / im.height)
    if ancho > lado:
        ancho, alto = lado, round(im.height * lado / im.width)
    im = im.resize((ancho, alto), Image.LANCZOS)
    out = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    out.alpha_composite(im, ((lado - ancho) // 2, round(lado * (1 - pie)) - alto))
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst, "WEBP", quality=88, method=6)


def recursos_idioma(lang):
    """Planos rotulados y documentos de mesa, rasterizados de los PDF del idioma."""
    sal = TRAB / "salida" / lang
    D = json.loads((TRAB / "texto" / lang / "datos.json").read_text())
    doc = fitz.open(sal / f"{D['archivos']['planos']}.pdf")
    for i, (d, quien) in enumerate((("A", "crew"), ("B", "crew"), ("A", "gm"), ("B", "gm"))):
        dst = A / lang / "planos" / f"{d}-{quien}.webp"
        dst.parent.mkdir(parents=True, exist_ok=True)
        pix = doc[i].get_pixmap(dpi=150)
        Image.frombytes("RGB", (pix.width, pix.height), pix.samples).save(dst, "WEBP", quality=84, method=6)
    doc = fitz.open(sal / f"{D['archivos']['documentos']}.pdf")
    for i, p in enumerate(doc):
        dst = A / lang / "docs" / f"{i + 1:02d}.webp"
        dst.parent.mkdir(parents=True, exist_ok=True)
        pix = p.get_pixmap(dpi=130)
        Image.frombytes("RGB", (pix.width, pix.height), pix.samples).save(dst, "WEBP", quality=86, method=6)


# ------------------------------------------------------------------ geometría de muros
def muros(deck):
    """Muros y puertas desde las cajas de mapas.py: borde entre celdas de distinto recinto (rejilla de media unidad).
    Pasillos y conductos son el mismo recinto de tránsito; los conductos se ensanchan media unidad para tocar las salas."""
    C = mapas.CUBIERTAS[deck]
    zonas = [("t", r) for r in C["pasillos"]]
    zonas += [("t", (x0 - .5, y0, x1 + .5, y1) if x1 - x0 < y1 - y0 else (x0, y0 - .5, x1, y1)) for x0, y0, x1, y1 in C["conductos"]]
    zonas += [(k, v[1:]) for k, v in C["salas"].items()]
    cel = {}
    for etq, (x0, y0, x1, y1) in zonas:
        for i in range(round(x0 * 2), round(x1 * 2)):
            for j in range(round(y0 * 2), round(y1 * 2)):
                cel[(i, j)] = etq
    puertas = [(o, x * 2, (y - an / 2) * 2, (y + an / 2) * 2, t) if o == "v" else (o, y * 2, (x - an / 2) * 2, (x + an / 2) * 2, t)
               for x, y, o, an, t in C["puertas"]]

    def puerta(o, linea, a):
        return next((t for po, pl, p0, p1, t in puertas if po == o and pl == linea and p0 <= a < p1), None)
    segs = {}
    xs = [i for i, _ in cel]; ys = [j for _, j in cel]
    for i in range(min(xs) - 1, max(xs) + 2):
        for j in range(min(ys) - 1, max(ys) + 2):
            a, b, c = cel.get((i, j)), cel.get((i + 1, j)), cel.get((i, j + 1))
            if a != b:   # borde vertical en x = i+1
                segs.setdefault(("v", i + 1), []).append((j, puerta("v", i + 1, j)))
            if a != c:   # borde horizontal en y = j+1
                segs.setdefault(("h", j + 1), []).append((i, puerta("h", j + 1, i)))
    ox, oy = CAJA_ESCENA[deck][:2]
    out = []
    for (o, linea), lista in sorted(segs.items()):
        lista.sort()
        tramos = []
        for pos, tipo in lista:
            if tramos and tramos[-1][1] == pos and tramos[-1][2] == tipo:
                tramos[-1][1] = pos + 1
            else:
                tramos.append([pos, pos + 1, tipo])
        for p0, p1, tipo in tramos:
            if o == "v":
                c = [linea, p0, linea, p1]
            else:
                c = [p0, linea, p1, linea]
            c = [round(mapas.OX + c[0] * HALF - ox), round(mapas.OY + c[1] * HALF - oy), round(mapas.OX + c[2] * HALF - ox), round(mapas.OY + c[3] * HALF - oy)]
            out.append({"c": c, "door": 1 if tipo else 0, "ds": 2 if tipo == "c" else 0})
    return out


def a_escena(deck, x, y):
    """Unidades de plano → píxeles de la escena recortada."""
    px, py = mapas.px(x, y)
    return px - CAJA_ESCENA[deck][0], py - CAJA_ESCENA[deck][1]


# ------------------------------------------------------------------ construcción por idioma
class Aventura:
    def __init__(self, lang):
        self.lang, self.T = lang, L[lang]
        self.idx = 1 if lang == "es" else 2
        os.environ["EIDOLON_LANG"] = lang
        import build
        self.B = importlib.reload(build)
        self.D = self.B.D
        self.tx = TRAB / "texto" / lang
        self.folders, self.journal, self.actors, self.scenes, self.tables, self.macros, self.playlists = {}, [], [], [], [], [], []
        self.page_ref = {}       # "cap:01" | "sala:05" | "lectura:0" | "registro" → (diario, página)
        self.docs = {}

    def id(self, key):
        return fid(f"{self.lang}:{key}")

    def folder(self, tipo, clave, sort=0, color="#13202a"):
        k = tipo + clave
        if k not in self.folders:
            self.folders[k] = {"_id": self.id("folder:" + k), "name": self.T["carp"][clave], "type": tipo, "color": color, "sorting": "m", "sort": sort,
                               "folder": None, "description": "", "flags": {MODID: {"slug": "folder-" + clave}}}
        return self.folders[k]["_id"]

    def page(self, key, name, cont, sort, tipo="text", src=None, nivel=1):
        p = {"_id": self.id("page:" + key), "name": name, "type": tipo, "title": {"show": tipo == "text" and not key.startswith(("cap:", "sala:", "pantalla:", "registro")), "level": nivel}, "sort": sort,
             "ownership": {"default": -1}, "flags": {MODID: {"slug": key}}}
        if tipo == "text":
            p["text"] = {"format": 1, "content": f'<div class="mr-eidolon-j">{cont}</div>'}
        else:
            p["src"] = src
            p["image"] = {"caption": cont or ""}
        return p

    def entry(self, key, name, pages, folder, sort):
        j = {"_id": self.id("je:" + key), "name": name, "pages": pages, "folder": folder, "sort": sort, "categories": [],
             "ownership": {"default": 0}, "flags": {MODID: {"slug": key}}}
        self.journal.append(j)
        for pg in pages:
            self.page_ref[pg["flags"][MODID]["slug"]] = (j["_id"], pg["_id"])
        return j

    def uuid_pagina(self, clave):
        j, p = self.page_ref[clave]
        return f"JournalEntry.{j}.JournalEntryPage.{p}"

    # ---------------- manual
    def manual(self):
        fol = self.folder("JournalEntry", "manual", 100)
        lineas = (self.tx / "manual.md").read_text().split("\n") + ["@fin"]
        partes, actual, cap, buf, lecturas = [], None, None, [], []

        def flush():
            if buf and cap is not None:
                cap["html"].append(md("\n".join(buf)))
            buf.clear()
        i, pend = 0, None
        while i < len(lineas):
            l = lineas[i]
            if pend and (l.startswith("@") or l.startswith("## ") or l.startswith(":::")):
                tipo, datos, cuerpo = pend
                if tipo == "sala":
                    n, nombre = datos
                    img = f'<img class="mini" src="{MOD}/assets/rooms/r{n}.webp" alt="">' if (A / "rooms" / f"r{n}.webp").exists() else ""
                    actual["pages"].append({"key": f"sala:{n}", "name": f"{n} · {nombre}", "nivel": 2,
                                            "html": [f'<div class="sala"><div class="t"><b>{n}</b><span>{esc(nombre)}</span></div>{img}{self.botones_sala(n)}{md(chr(10).join(cuerpo))}</div>']})
                else:
                    pid, nombre, cargo, est = datos
                    cap["html"].append(f'<div class="pnj"><img src="{MOD}/assets/portraits/{pid}.webp" alt=""><div><h3>{esc(nombre)}</h3><div class="c">{esc(cargo)}</div>'
                                       f'<div class="e">{esc(est)}</div>{md(chr(10).join(cuerpo))}</div></div>')
                pend = None
            if pend:
                pend[2].append(l); i += 1; continue
            if l.startswith("::: "):
                flush()
                tipo, _, titulo = l[4:].partition(" ")
                j = i + 1; cuerpo = []
                while lineas[j].strip() != ":::":
                    cuerpo.append(lineas[j]); j += 1
                h = f'<div class="{tipo}"><h4>{esc(titulo)}</h4>{md(chr(10).join(cuerpo))}</div>'
                cap["html"].append(h)
                if tipo == "lectura":
                    lecturas.append((f"lectura:{len(lecturas)}", titulo, h))
                i = j + 1; continue
            if l.startswith("@parte "):
                flush()
                num, titulo = [x.strip() for x in l[7:].split("|")]
                actual = {"num": num, "titulo": titulo, "pages": []}; partes.append(actual)
            elif l.startswith("@cap "):
                flush()
                n, rot, tit, ent = [x.strip() for x in l[5:].split("|")]
                cap = {"key": f"cap:{n}", "name": f"{n} · {tit}", "nivel": 1,
                       "html": [f'<div class="cap"><div class="k"><b>{n}</b>{esc(rot)}</div><h1>{esc(tit)}</h1><div class="ent">{ilm(ent)}</div></div>']}
                actual["pages"].append(cap)
            elif l.startswith("@fig "):
                flush()
                nombre, pie, clase = [x.strip() for x in l[5:].split("|")]
                cap["html"].append(f'<figure class="{clase}"><img src="{MOD}/assets/art/{nombre}.webp" alt=""><figcaption>{ilm(pie)}</figcaption></figure>')
            elif l.startswith("@sala "):
                flush(); pend = ("sala", [x.strip() for x in l[6:].split("|")], [])
            elif l.startswith("@pnj "):
                flush(); pend = ("pnj", [x.strip() for x in l[5:].split("|")], [])
            elif l.startswith("@plano "):
                flush()
                d = l.split()[1]
                cap["html"].append(f'<figure class="plano"><img src="{MOD}/assets/{self.lang}/planos/{d}-gm.webp" alt=""><figcaption>{self.B.U.plano_pie.format(deck=d)}</figcaption></figure>')
            elif l.strip() in ("@pantalla", "@registro", "@fin"):
                flush()
            elif l.startswith("@"):
                flush(); cap["html"].append(self.B.bloque(l[1:].strip()))
            else:
                buf.append(l)
            i += 1
        flush()
        self.entry("lecturas", self.T["lecturas"], [self.page(k, t, h, n * 100) for n, (k, t, h) in enumerate(lecturas)], fol, 0)
        for si, p in enumerate(partes):
            pages = [self.page(pg["key"], pg["name"], "".join(pg["html"]), k * 100, nivel=pg["nivel"]) for k, pg in enumerate(p["pages"])]
            self.entry(f"parte-{p['num']}", f"{p['num']} · {p['titulo']}", pages, fol, 10 + si * 10)
        pages = []
        for k, (d, quien) in enumerate((("A", "crew"), ("B", "crew"), ("A", "gm"), ("B", "gm"))):
            nom = (self.T["plano_trip"] if quien == "crew" else self.T["plano_gm"]).format(d=d)
            pages.append(self.page(f"plano:{d}-{quien}", nom, "", k * 100, "image", f"{MOD}/assets/{self.lang}/planos/{d}-{quien}.webp"))
        self.entry("planos", self.T["planos"], pages, fol, 60)
        trozos = [t for t in re.split(r'(?=<div class="pant">)', (self.tx / "pantalla.html").read_text()) if t.strip()]
        pages = []
        for k, t in enumerate(trozos):
            sub = re.search(r"<small>(.*?)</small>", t, re.S)
            pages.append(self.page(f"pantalla:{k}", f"{self.T['pantalla']} · {sub.group(1).strip()}" if sub else self.T["pantalla"], t, k * 100))
        self.entry("pantalla", self.T["pantalla"], pages, fol, 70)
        self.entry("registro", self.T["registro"], [self.page("registro", self.T["registro"], self.B.registro(), 0)], fol, 80)

    def botones_sala(self, n):
        """Pistas de MR- Dirección en la página de la sala: ver o mostrar su escena a pantalla completa y volver al plano."""
        B = self.T["botones"]
        deck = SALAS_DECK.get(n, "B")
        out = []
        if fuente_escena(f"s{n}"):
            sid = self.id(f"scene:s{n}")
            out += [f"@Dir[view|{sid}]{{{B['ver']}}}", f"@Dir[activate|{sid}]{{{B['mostrar']}}}"]
        out.append(f"@Dir[activate|{self.id(f'scene:deck-{deck}')}]{{{B['volver'].format(d=deck)}}}")
        return f'<p class="botones">{" · ".join(out)}</p>'

    # ---------------- documentos de mesa
    def documentos(self):
        fol = self.folder("JournalEntry", "docs", 200, "#7a2b22")
        for i, a in enumerate(json.loads((self.tx / "ayudas.json").read_text())):
            n = f"{i + 1:02d}"
            filas = "".join(f"<tr><th>{esc(k)}</th><td>{esc(v).replace(chr(10), '<br>')}</td></tr>" for k, v in a["campos"])
            nota = f'<p class="manus">{esc(a["nota"])}</p>' if a.get("nota") else ""
            texto = (f'<p class="doc-meta"><b>{esc(a["cod"])}</b> · {esc(a["area"])} · {esc(a["acceso"])}</p><table class="doc">{filas}</table>{nota}'
                     f'<p class="gm"><b>{self.T["entrega"]}:</b> {esc(a["entrega"])}</p>')
            pages = [self.page(f"doc:{n}:img", f"{self.T['doc_imagen']} {n}", "", 0, "image", f"{MOD}/assets/{self.lang}/docs/{n}.webp"),
                     self.page(f"doc:{n}:txt", self.T["doc_texto"], texto, 100)]
            self.docs[n] = self.entry(f"doc-{n}", f"{n} · {a['titulo']}", pages, fol, i * 10)

    # ---------------- actores
    def token(self, nombre, img, disp, enlace, color):
        tok = img.replace("/portraits/", "/tokens/")
        return {"name": nombre, "displayName": 30, "actorLink": enlace, "disposition": disp, "texture": {"src": tok, "scaleX": 1, "scaleY": 1, "fit": "contain"},
                "width": 1, "height": 1, "lockRotation": True, "bar1": {"attribute": "health"}, "displayBars": 20,
                "sight": {"enabled": enlace, "range": 30}, "ring": {"enabled": False}}

    def fig(self, clave):
        return {"figura": f"{MOD}/assets/figures/{clave}.webp"} if (A / "figures" / f"{clave}.webp").exists() else {}

    def item(self, owner, n, nombre, tipo, system, img):
        return {"_id": self.id(f"item:{owner}:{n}"), "name": nombre, "type": tipo, "img": img, "system": system, "effects": [], "flags": {}, "sort": n * 10}

    def pregenerados(self):
        fol = self.folder("Actor", "tripu", 100)
        M = self.D["mesa"]; b = self.T["bio"]
        for i, p in enumerate(json.loads((self.tx / "pjs.json").read_text())):
            items, n = [], 0
            for h in p["habilidades"]:
                v = int(re.search(r"\+(\d+)", h).group(1))
                items.append(self.item(f"pj{i}", n, re.sub(r"\s*\(\+\d+\)", "", h), "skill",
                                       {"description": "", "rank": self.T["rango"][v], "bonus": v, "prerequisite_ids": []}, "icons/svg/book.svg")); n += 1
            for eq in [x.strip().rstrip(".") for x in re.split(r";\s*(?![^()]*\))", p["equipo"]) if x.strip()]:
                nombre = re.sub(r"\s*\(.*?\)", "", eq).strip(); nombre = nombre[0].upper() + nombre[1:]
                dano = re.search(r"(\d+d\d+)", eq); pa = re.search(r"(?:PA|AP)\s*(\d+)", eq)
                if pa:
                    items.append(self.item(f"pj{i}", n, nombre, "armor", {"description": eq, "armorPoints": int(pa.group(1)), "damageReduction": 0,
                                                                          "speed": "", "oxygenMax": 0, "oxygenCurrent": 0, "equipped": True}, "icons/svg/shield.svg"))
                elif dano:
                    items.append(self.item(f"pj{i}", n, nombre, "weapon", {"description": eq, "damage": dano.group(1), "settings": {"firstEdition": True}}, "icons/svg/sword.svg"))
                else:
                    items.append(self.item(f"pj{i}", n, nombre, "item", {"description": eq, "quantity": 1}, "icons/svg/item-bag.svg"))
                n += 1
            cred = re.search(re.escape(M["pref_cred"]) + r"\s*([\d.,]+)", p["creditos"]).group(1)
            trasto = p["creditos"].split(M["pref_trasto"])[1].strip()
            parche = p["parche"].replace(M["pref_parche"], "").strip()
            bio = (f'<div class="mr-eidolon-j"><p><b>{b["rol"]}:</b> {esc(p["rol"])} · <b>{b["edad"]}:</b> {esc(p["edad"])}</p>'
                   f'<p><b>{b["trasto"]}:</b> {esc(trasto)}<br><b>{b["parche"]}:</b> “{esc(parche)}”</p>'
                   f'<div class="confidencial"><h4>{b["conf"]}</h4><p><b>{b["vinculo"]}.</b> {esc(p["vinculo"])}</p>'
                   f'<p><b>{b["secreto"]}.</b> {esc(p["secreto"])}</p><p><b>{b["decision"]}.</b> {esc(p["decision"])}</p></div></div>')
            hp = int(p["salud"].split("/")[1]); hits = int(p["heridas"].split("/")[1])
            nombre = re.sub(r"\b(\w)(\w*)", lambda m: m.group(1) + m.group(2).lower(), p["nombre"]).replace("«", "“").replace("»", "”")
            stats = {k: {"value": p[c], "mod": 0, "min": 0, "max": 99} for k, c in (("strength", "fuerza"), ("speed", "velocidad"), ("intellect", "intelecto"),
                                                                                   ("combat", "combate"), ("sanity", "cordura"), ("fear", "miedo"), ("body", "cuerpo"))}
            stats["armor"] = {"value": 0, "mod": 0, "min": 0, "max": 99, "damageReduction": 0, "cover": "none"}
            img = f"{MOD}/assets/portraits/pj{i + 1:02d}.webp"
            self.actors.append({"_id": self.id(f"actor:pj{i + 1}"), "name": nombre, "type": "character", "img": img,
                                "system": {"biography": bio, "class": {"value": p["tipo"].title()}, "credits": {"value": cred}, "pronouns": {"value": ""},
                                           "health": {"value": hp, "min": 0, "max": hp}, "hits": {"value": 0, "min": 0, "max": hits},
                                           "other": {"stress": {"value": int(p["estres"]), "min": 2, "max": 20}, "stressdesc": {"value": p["trauma"]}}, "stats": stats},
                                "prototypeToken": self.token(nombre, img, 1, True, "#0d6670"), "items": items, "effects": [], "folder": fol, "sort": i * 10,
                                "ownership": {"default": 0}, "flags": {MODID: {"slug": f"pj{i + 1}", "tipo": "pj", **self.fig(f"pj{i + 1:02d}")}}})

    def criatura(self, slug, nombre, img, stats, bio, armas, fol, disp, color, sort):
        c, ins, hp, heridas, pa = stats
        items = [self.item(slug, n, a, "weapon", {"description": a, "damage": d, "settings": {"firstEdition": True}}, "icons/svg/sword.svg") for n, (a, d) in enumerate(armas)]
        self.actors.append({"_id": self.id(f"actor:{slug}"), "name": nombre, "type": "creature", "img": img,
                            "system": {"description": "", "biography": f'<div class="mr-eidolon-j">{bio}</div>', "health": {"value": hp, "min": 0, "max": hp},
                                       "hits": {"value": 0, "min": 0, "max": heridas},
                                       "stats": {"combat": {"value": c, "min": 0, "max": 99, "enabled": True}, "instinct": {"value": ins, "min": 0, "max": 99, "enabled": True},
                                                 "armor": {"value": pa, "mod": 0, "min": 0, "max": 99, "damageReduction": 0, "cover": "none", "enabled": pa > 0}}},
                            "prototypeToken": self.token(nombre, img, disp, False, color), "items": items, "effects": [], "folder": fol, "sort": sort,
                            "ownership": {"default": 0}, "flags": {MODID: {"slug": slug, "tipo": "pnj", **self.fig(slug)}}})

    def pnj(self):
        """Supervivientes como personajes completos: mecánica y biografía de texto/<idioma>/supervivientes.json + su entrada del manual."""
        fol = self.folder("Actor", "pnj", 200)
        texto = (self.tx / "manual.md").read_text().split("\n")
        S = json.loads((self.tx / "supervivientes.json").read_text())
        parches_es = json.loads((ROOT.parent / "mr-mothership-es" / "parches" / "parches.json").read_text())
        h = self.T["sup"]
        for k, l in enumerate(texto):
            if not l.startswith("@pnj "):
                continue
            pid, nombre, cargo, est = [x.strip() for x in l[5:].split("|")]
            cuerpo = []
            for x in texto[k + 1:]:
                if x.startswith("@") or x.startswith(":::") or x.startswith("## "):
                    break
                cuerpo.append(x)
            s = S[pid]
            parche = s["parche_texto"] or parches_es[int(s["parche"])]
            secc = "".join(f"<h4>{h[c]}</h4><p>{esc(s[c])}</p>" for c in ("donde", "voz", "relaciones", "pistas", "copia"))
            bio = (f'<div class="mr-eidolon-j"><p><b>{esc(cargo)}</b> · <i>{esc(est)}</i></p>{md(chr(10).join(cuerpo))}{secc}'
                   f'<p><b>{h["parche"]}:</b> {esc(parche)}</p></div>')
            items = [self.item(pid, n, nom, "skill", {"description": "", "rank": self.T["rango"][v], "bonus": v, "prerequisite_ids": []}, "icons/svg/book.svg")
                     for n, (nom, v) in enumerate(s["hab"])]
            for nom, dano, pa in s["equipo"]:
                n = len(items)
                if pa:
                    items.append(self.item(pid, n, nom, "armor", {"description": nom, "armorPoints": pa, "damageReduction": 0, "speed": "", "oxygenMax": 0, "oxygenCurrent": 0, "equipped": True}, "icons/svg/shield.svg"))
                elif dano:
                    items.append(self.item(pid, n, nom, "weapon", {"description": nom, "damage": dano, "settings": {"firstEdition": True}}, "icons/svg/sword.svg"))
                else:
                    items.append(self.item(pid, n, nom, "item", {"description": nom, "quantity": 1}, "icons/svg/item-bag.svg"))
            stats = {c: {"value": v, "mod": 0, "min": 0, "max": 99} for c, v in zip(("strength", "speed", "intellect", "combat", "sanity", "fear", "body"), s["st"] + s["sv"])}
            stats["armor"] = {"value": 0, "mod": 0, "min": 0, "max": 99, "damageReduction": 0, "cover": "none"}
            img = f"{MOD}/assets/portraits/{pid}.webp"
            self.actors.append({"_id": self.id(f"actor:{pid}"), "name": nombre, "type": "character", "img": img,
                                "system": {"biography": bio, "class": {"value": s["clase_nombre"]}, "rank": {"value": cargo.split("·")[0].strip()},
                                           "health": {"value": s["salud"], "min": 0, "max": s["salud"]}, "hits": {"value": 0, "min": 0, "max": s["heridas"]},
                                           "other": {"stress": {"value": s["estres"], "min": 2, "max": 20}, "stressdesc": {"value": s["trauma"]}}, "stats": stats},
                                "prototypeToken": self.token(nombre, img, DISP.get(pid, 1), False, "#5c8c8f"), "items": items, "effects": [], "folder": fol,
                                "sort": len(self.actors) * 10, "ownership": {"default": 0}, "flags": {MODID: {"slug": pid, "tipo": "pnj", **self.fig(pid)}}})
        fol = self.folder("Actor", "amenaza", 300, "#7a2b22")
        for n, (nombre, sub, (c, ins, her, pa), a, b) in enumerate(self.D["adversarios"]):
            slug = ("forma", "matriz")[n]
            self.criatura(slug, nombre, f"{MOD}/assets/portraits/{slug}.webp", (c, ins, 10 if n == 0 else 20, her, pa),
                          f"<p><i>{esc(sub)}</i></p><p>{a}</p><p>{b}</p>", [(self.T["filamento"] if n == 0 else self.T["membrana"], "2d10")],
                          fol, -1, "#b8382a", n * 10)

    # ---------------- escenas
    def nota(self, deck, k, x, y):
        eid, pid = self.page_ref[f"sala:{k}"]
        return {"_id": self.id(f"note:{deck}:{k}"), "entryId": eid, "pageId": pid, "x": x, "y": y, "elevation": 0, "sort": 0,
                "texture": {"src": "icons/svg/book.svg", "tint": "#e9c25a"}, "iconSize": 48, "text": k, "fontFamily": "Signika", "fontSize": 30,
                "textAnchor": 1, "textColor": "#ffffff", "global": False, "flags": {}}

    def escenas_mapa(self):
        fol = self.folder("Scene", "mapas", 100)
        sid = {d: self.id(f"scene:deck-{d}") for d in "AB"}
        pares = [((37.5, 29), (37.5, 29)), ((84, 30), (84, 30)), ((114, 46), (114, 61.5))]   # escalera y trampillas A ↔ B
        for n, d in enumerate("AB"):
            C = mapas.CUBIERTAS[d]
            ancho, alto = CAJA_ESCENA[d][2] - CAJA_ESCENA[d][0], CAJA_ESCENA[d][3] - CAJA_ESCENA[d][1]
            notes = [self.nota(d, k, *a_escena(d, (x0 + x1) / 2, (y0 + y1) / 2)) for k, (_n, x0, y0, x1, y1) in C["salas"].items()]
            if C["exterior"]:
                k, _n, x0, y0, x1, y1 = C["exterior"]
                notes.append(self.nota(d, k, *a_escena(d, (x0 + x1) / 2, (y0 + y1) / 2)))
            if d == "B":
                notes.append(self.nota(d, "15", *a_escena(d, 101, 61.5)))
            otro = "B" if d == "A" else "A"
            regions = []
            for m, par in enumerate(pares):
                cx, cy = a_escena(d, *par[n])
                regions.append({"_id": self.id(f"region:{d}:{m}"), "name": self.T["irA"].format(d=otro), "color": "#e9c25a",
                                "shapes": [{"type": "rectangle", "x": cx - 30, "y": cy - 30, "width": 60, "height": 60, "rotation": 0, "hole": False}],
                                "elevation": {"bottom": None, "top": None}, "visibility": 1, "locked": True, "flags": {},
                                "behaviors": [{"_id": self.id(f"beh:{d}:{m}"), "name": self.T["irA"].format(d=otro), "type": "teleportToken",
                                               "system": {"destination": f"Scene.{sid[otro]}.Region.{self.id(f'region:{otro}:{m}')}", "choice": True},
                                               "disabled": False, "flags": {}}]})
            ws = [{"_id": self.id(f"wall:{d}:{k}"), "c": w["c"], "move": 20, "sight": 20, "sound": 20, "light": 20, "door": w["door"], "ds": w["ds"],
                   "dir": 0, "flags": {}} for k, w in enumerate(muros(d))]
            self.scenes.append({
                "_id": sid[d], "name": self.T["escena_mapa"].format(d=d), "active": False, "navigation": True, "navOrder": n, "navName": self.T["escena_mapa"].format(d=d),
                "background": {"src": f"{MOD}/assets/maps/{d}.webp"}, "thumb": f"{MOD}/assets/thumbs/deck-{d}.webp",
                "width": ancho, "height": alto, "padding": 0, "initial": {"x": ancho // 2, "y": alto // 2, "scale": 0.45}, "backgroundColor": "#070b0e",
                "grid": {"type": 1, "size": GRID, "style": "solidLines", "thickness": 1, "color": "#000000", "alpha": 0.12, "distance": 1.5, "units": "m"},
                "tokenVision": True, "fog": {"exploration": True}, "environment": {"darknessLevel": 0.25, "globalLight": {"enabled": True, "darkness": {"max": 0.6}}},
                "walls": ws, "notes": notes, "tokens": [], "lights": [], "sounds": [], "tiles": [], "drawings": [], "templates": [], "regions": regions,
                "folder": fol, "sort": n * 10, "ownership": {"default": 0}, "flags": {MODID: {"slug": f"deck-{d}"}}})

    def nombre_escena(self, k):
        if k in ("portada", "vesperina"):
            return self.T["esc"][k]
        n = k[1:]
        return self.T["esc"]["pasillo"] if n == "15" else f"{n} · {self.D['salas'][n]}"

    def escenas_imagen(self):
        fol = self.folder("Scene", "imagen", 200)
        for n, k in enumerate(k for k in IMAGENES if fuente_escena(k)):
            self.scenes.append({
                "_id": self.id(f"scene:{k}"), "name": self.nombre_escena(k), "active": False, "navigation": False, "navOrder": 10 + n,
                "background": {"src": f"{MOD}/assets/scenes/{k}.webp"}, "thumb": f"{MOD}/assets/thumbs/{k}.webp", "width": 1920, "height": 1080, "padding": 0,
                "initial": None, "backgroundColor": "#000000", "grid": {"type": 0, "size": 100, "alpha": 0}, "tokenVision": False, "fog": {"exploration": False},
                "environment": {"darknessLevel": 0, "globalLight": {"enabled": True}}, "walls": [], "notes": [], "tokens": [], "lights": [], "sounds": [],
                "tiles": [], "drawings": [], "templates": [], "regions": [], "folder": fol, "sort": n * 10, "ownership": {"default": 0}, "flags": {MODID: {"slug": k, "imagen": True}}})

    # ---------------- sonido, tablas y macros
    def sonido(self):
        fol = self.folder("Playlist", "audio", 100)

        def snd(clave, carpeta, nombre, vol, rep):
            return {"_id": self.id(f"snd:{clave}"), "name": nombre, "path": f"{MOD}/assets/audio/{carpeta}/{clave}.ogg", "repeat": rep, "volume": vol,
                    "playing": False, "pausedTime": None, "fade": None, "sort": 0, "description": "", "channel": "music" if carpeta == "musica" else "environment",
                    "flags": {MODID: {"slug": clave}}}
        for k, (nom, carpeta, lista, vol, rep) in enumerate((("musica", "musica", MUSICA, 0.5, True), ("efectos", "sfx", SFX, 0.7, False))):
            self.playlists.append({"_id": self.id(f"pl:{carpeta}"), "name": self.T[nom], "mode": -1, "playing": False, "fade": None, "sorting": "m",
                                   "sounds": [snd(c, carpeta, v[self.idx], vol, rep) for c, v in lista.items()], "folder": fol, "sort": k * 10, "description": "",
                                   "channelVolumes": {}, "seed": 0, "ownership": {"default": 0}, "flags": {MODID: {"slug": f"pl-{carpeta}"}}})

    def tabla(self, slug, nombre, formula, filas, fol, desc=""):
        res = [{"_id": self.id(f"res:{slug}:{n}"), "type": "text", "name": "", "img": "icons/svg/d10-grey.svg", "description": f"<p>{ilm(t)}</p>",
                "weight": 1, "range": [n, n], "drawn": False, "flags": {}} for n, t in filas]
        return {"_id": self.id(f"table:{slug}"), "name": nombre, "formula": formula, "replacement": True, "displayRoll": True, "results": res, "folder": fol,
                "description": desc, "sort": len(self.tables) * 10, "ownership": {"default": 0}, "flags": {MODID: {"slug": slug}}}

    def tablas(self):
        fol = self.folder("RollTable", "tablas", 100)
        texto = (self.tx / "manual.md").read_text().split("\n")
        titulo = ""
        for i, l in enumerate(texto):
            if l.startswith("## "):
                titulo = l[3:].strip()
            if re.match(r"^\|\s*1d6\s*\|", l):
                filas = []
                for x in texto[i + 2:]:
                    if not x.startswith("|"):
                        break
                    c = [y.strip() for y in x.strip().strip("|").split("|")]
                    filas.append((int(c[0]), c[1]))
                self.tables.append(self.tabla(f"tabla-{len(self.tables)}", re.sub(r"\s*\(1d6\)", "", titulo), "1d6", filas, fol))
        eleg = {l[5:].split("|")[0].strip(): l.split("|")[1].strip() for l in texto if l.startswith("@pnj ")}
        self.tables.append(self.tabla("primera-copia", self.T["tabla_copia"], "1d5", [(n, eleg[p]) for n, p in enumerate(ELEGIBLES, 1)], fol, self.T["tabla_copia_txt"]))

    def macros_(self):
        fol = self.folder("Macro", "macros", 100)
        for k, (nom, cmd, img) in enumerate(((self.T["sorteo"], f'game.modules.get("{MODID}")?.api?.sorteo();', "icons/svg/daze.svg"),
                                              (self.T["registro"], f'game.modules.get("{MODID}")?.api?.registro();', "icons/svg/book.svg"))):
            self.macros.append({"_id": self.id(f"macro:{k}"), "name": nom, "type": "script", "scope": "global", "img": img, "command": cmd,
                                "author": "0000000000000000", "folder": fol, "sort": k * 10, "ownership": {"default": 0}, "flags": {MODID: {"slug": f"macro-{k}"}}})

    # ---------------- paquete de MR- Dirección
    def direccion(self):
        T, idx = self.T, self.idx
        f = lambda slug: {"flag": [MODID, "slug", slug]}
        cue = lambda c: {"label": SFX[c][idx], "icon": SFX[c][3], "sound": f(c)}
        mot = [{"id": i, "label": es if self.lang == "es" else en, "icon": ic, "music": f(m)} for i, m, es, en, ic in MOTIVOS]
        efectos = [{"id": k, "label": SFX[k][idx], "icon": SFX[k][3], "sound": f(k)} for k in ("alarma", "golpe", "compuerta", "temblor")]
        marcas = {"milestones": [{"id": f"nivel{n + 1}", "label": a} for n, (a, _b) in enumerate(self.D["niveles"])],
                  "clocks": [{"id": ("recirculacion", "noxum", "soporte")[n], "label": r[0], "segments": r[1]} for n, r in enumerate(self.D["relojes"])]}
        escenas = []
        for n, d in enumerate("AB"):
            musica, cues = MAPA_MUSICA[d]
            escenas.append({"ref": f(f"deck-{d}"), "order": n, "name": T["escena_mapa"].format(d=d), "reading": {"uuid": self.uuid_pagina("cap:07" if d == "A" else "cap:08")},
                            "music": f(musica), "motifs": None, "cues": [cue(c) for c in cues], "ambient": None, "figures": [],
                            "handouts": [{"ref": {"uuid": self.uuid_pagina(f"plano:{d}-crew")}, "label": T["plano_trip"].format(d=d)}],
                            "notes": "", "thumb": f"{MOD}/assets/thumbs/deck-{d}.webp"})
        for n, (k, (img, lect, musica, cues, figs, amb)) in enumerate((k, v) for k, v in IMAGENES.items() if fuente_escena(k)):
            escenas.append({"ref": f(k), "order": 10 + n, "name": self.nombre_escena(k), "reading": {"uuid": self.uuid_pagina(lect)},
                            "music": f(musica), "motifs": None, "cues": [cue(c) for c in cues], "ambient": amb,
                            "figures": [{"ref": f(p), "label": ""} for p in figs],
                            "handouts": [{"ref": f(f"doc-{dn}"), "label": self.docs[dn]["name"]} for dn, e in ENTREGA.items() if e == k],
                            "notes": "", "thumb": f"{MOD}/assets/thumbs/{k}.webp", "stage": {"eye": 0.45, "anchors": [[0.3, 0.86], [0.5, 0.9], [0.7, 0.86]]}})
        return {"schema": 1, "id": MODID, "title": T["titulo"], "version": json.loads((ROOT / "module.json").read_text())["version"], "author": "Manu Romera",
                "license": "CC BY-NC-SA 4.0", "settings": {"fade": 3.5, "motifs": mot, "effects": efectos, "markers": marcas}, "scenes": escenas}

    # ---------------- todo
    def construir(self):
        self.manual(); self.documentos(); self.pregenerados(); self.pnj(); self.escenas_mapa(); self.escenas_imagen()
        self.sonido(); self.tablas(); self.macros_()
        adv = {"_id": self.id("adventure"), "name": self.T["titulo"], "img": f"{MOD}/assets/art/i_portada.webp", "caption": f"<p>{self.T['lema']}</p>",
               "description": self.T["desc"], "actors": self.actors, "combats": [], "items": [], "journal": self.journal, "scenes": self.scenes,
               "tables": self.tables, "macros": self.macros, "cards": [], "playlists": self.playlists, "folders": list(self.folders.values()),
               "folder": None, "sort": 0, "flags": {MODID: {"lang": self.lang}}}
        (ROOT / "_data").mkdir(exist_ok=True)
        (ROOT / "_data" / f"aventura-{self.lang}.json").write_text(json.dumps([adv], ensure_ascii=False))
        (ROOT / "content").mkdir(exist_ok=True)
        (ROOT / "content" / f"direccion-{self.lang}.json").write_text(json.dumps(self.direccion(), ensure_ascii=False, indent=1))
        print(self.lang, "| diarios", len(self.journal), "| páginas", sum(len(j["pages"]) for j in self.journal), "| actores", len(self.actors),
              "| escenas", len(self.scenes), "| muros", sum(len(s["walls"]) for s in self.scenes), "| tablas", len(self.tables),
              "| sonidos", sum(len(p["sounds"]) for p in self.playlists))


if __name__ == "__main__":
    recursos()
    for lang in LANGS:
        recursos_idioma(lang)
        Aventura(lang).construir()
