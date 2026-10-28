#!/usr/bin/env python3
"""Música propia de EIDOLON: reutiliza el sintetizador de MR- Nádir (tools/audio.py, misma licencia) como biblioteca
y añade recetas y texturas para cada ubicación de LIMEN-9. Bucles de 96 s sin costura, Ogg Opus.
Uso: python3 tools/audio.py [clave ...]   → assets/audio/musica/<clave>.ogg"""
import os, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.environ.get("NADIR_TOOLS", str(ROOT.parent / "mr-nadir" / "tools")))
import audio as A  # noqa: E402  (sintetizador de Nádir)

SR, D1 = A.SR, A.D1
NUEVAS = {
    # clave: (raíz Hz, brillo, bpm del pulso o 0, pings/min, textura, tensión)
    "cumpleanos": (D1, 0.3, 0, 1, "vacio", 0.5),
    "dormitorios": (D1 * 1.5, 0.2, 0, 1, "respiracion", 0.35),
    "enfermeria": (D1, 0.35, 0, 2, "monitor", 0.45),
    "senal": (D1, 0.4, 0, 3, "radio", 0.5),
    "carga": (D1 * 0.75, 0.3, 52, 1, "metal", 0.4),
    "laboratorio": (D1, 0.5, 0, 4, "electrico", 0.35),
    "reciclaje": (D1 * 0.75, 0.3, 0, 2, "agua", 0.5),
    "morgue": (D1 * 0.75, 0.15, 0, 1, "frio", 0.7),
    "archivo": (D1, 0.25, 0, 2, "cinta", 0.6),
    "hangar": (D1, 0.45, 72, 2, "motor", 0.6),
}
_textura = A.textura


def textura(kind, n, rng, t):
    if kind == "monitor":   # monitor cardíaco lejano, ~68 lpm
        y = np.zeros(n)
        for k in range(int(n / SR / 0.88)):
            tt = A.t_axis(0.11)
            A.place(y, np.sin(2 * np.pi * 988 * tt) * A.adsr(len(tt), 0.005, 0.05), k * 0.88 * SR)
        return A.normal(y) * 0.35 + A.normal(A.band(A.noise(n, rng, "pink"), 200, 900)) * 0.2
    if kind == "radio":     # estática de banda estrecha con ráfagas de señal
        st = A.band(rng.standard_normal(n), 300, 3400) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t) ** 2)
        tonos = np.zeros(n)
        for _ in range(int(n / SR * 0.6)):
            ln = int(rng.uniform(0.06, 0.25) * SR)
            tt = A.t_axis(ln / SR)
            A.place(tonos, np.sin(2 * np.pi * 740 * tt) * A.adsr(len(tt), 0.005, 0.02), rng.integers(0, n))
        return A.normal(st) * 0.45 + A.normal(tonos) * 0.25
    if kind == "agua":      # circulación de agua y goteo
        flujo = A.band(A.noise(n, rng, "pink"), 150, 1200) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t))
        return A.normal(flujo) * 0.5 + A.normal(A.drip_layer(n, rng, 0.8)) * 0.4
    if kind == "frio":      # brillo helado y muy escaso
        y = np.zeros(n)
        for _ in range(int(n / SR * 0.15)):
            A.place(y, A.ping(rng.choice([1760.0, 2349.3, 2637.0]), 6, 2.5), rng.integers(0, n))
        return A.normal(A.band(A.noise(n, rng, "pink"), 2000, 8000)) * 0.12 + A.normal(y) * 0.3
    if kind == "cinta":     # siseo de cinta y ecos de voz sin palabras
        siseo = A.band(rng.standard_normal(n), 3000, 9000) * 0.3
        voz = np.zeros(n)
        for _ in range(int(n / SR * 0.12)):
            ln = int(rng.uniform(1.0, 2.2) * SR)
            g = A.adsr(ln, 0.3, 0.6)
            v = (A.reso(rng.standard_normal(ln), rng.uniform(500, 800), 12) + A.reso(rng.standard_normal(ln), rng.uniform(1100, 1600), 14)) * g
            A.place(voz, v[::-1], rng.integers(0, n))   # al revés: suena a voz pero no se entiende
        return A.normal(siseo) * 0.4 + A.normal(voz) * 0.5
    if kind == "motor":     # motores en ralentí de la lanzadera
        motor = sum(np.sin(2 * np.pi * 37 * k * t + k) / k ** 1.2 for k in range(1, 9)) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.2 * t))
        return A.normal(motor) * 0.45 + A.normal(A.band(A.noise(n, rng, "pink"), 80, 700)) * 0.35
    return _textura(kind, n, rng, t)


A.textura = textura
A.MUSICA.update(NUEVAS)

# «Cumpleaños feliz» (dominio público) en caja de música desafinada: notas en semitonos sobre re5 y duración en tiempos
TEMA = [(-5, .75), (-5, .25), (-3, 1), (-5, 1), (0, 1), (-1, 2), (-5, .75), (-5, .25), (-3, 1), (-5, 1), (2, 1), (0, 2),
        (-5, .75), (-5, .25), (7, 1), (4, 1), (0, 1), (-1, 1), (-3, 2), (5, .75), (5, .25), (4, 1), (0, 1), (2, 1), (0, 2)]


def caja_de_musica(rng, L, fade):
    n = int((L + fade + 6) * SR)
    y = np.zeros(n)
    for inicio, tempo, desafino in ((6, 54, 0.008), (52, 46, 0.02)):
        pos = inicio
        for semi, dur in TEMA:
            if rng.random() > 0.08:   # alguna nota no suena: el mecanismo está gastado
                f = 587.33 * 2 ** (semi / 12) * (1 + rng.uniform(-desafino, desafino))
                A.place(y, A.bell(f, 3.0, rng, partials=(1, 3.01, 6.2), decay=1.4) * 0.6, pos * SR)
            pos += dur * 60 / tempo
    st = A.reverb(y, rng, 3.0, 0.45, 5000)
    return A.loopify(st, int(L * SR), fade)


def pista(clave):
    st = A.musica(clave)
    if clave == "cumpleanos":
        caja = caja_de_musica(A.rng_for(clave + "-caja"), 96, 6)
        st = A.master(st[: len(caja)] + caja * 0.9, -21)
    return st


if __name__ == "__main__":
    out = ROOT / "assets" / "audio" / "musica"
    out.mkdir(parents=True, exist_ok=True)
    for k in (sys.argv[1:] or NUEVAS):
        A.save(pista(k), str(out / f"{k}.ogg"))
        print("música", k, flush=True)
