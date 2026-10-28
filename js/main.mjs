// MR- EIDOLON · Importa la aventura en el idioma del mundo, registra su paquete en MR- Dirección
// y lleva el Registro de Ausencias (Huella de cada persona y sorteo imparcial de sustitución, cap. 03).
const MOD = "mr-eidolon";
const { DialogV2 } = foundry.applications.api;
const t = (k, d) => game.i18n.format(`MREIDOLON.${k}`, d ?? {});
const esc = s => foundry.utils.escapeHTML(String(s ?? ""));

Hooks.once("init", () => {
  game.settings.register(MOD, "idioma", {
    name: "MREIDOLON.Setting.Lang", hint: "MREIDOLON.Setting.LangHint", scope: "world", config: true, type: String, default: "auto",
    choices: { auto: "MREIDOLON.Setting.Auto", es: "Español", en: "English" }
  });
  game.settings.register(MOD, "importada", { scope: "world", config: false, type: String, default: "" });   // idioma importado
  game.settings.register(MOD, "version", { scope: "world", config: false, type: String, default: "" });
});

/** Idioma de la aventura: el elegido en ajustes, o el de Foundry (castellano si es «es», si no inglés). */
export function idioma() {
  const s = game.settings.get(MOD, "idioma");
  if (s !== "auto") return s;
  return game.settings.get(MOD, "importada") || (game.i18n.lang?.startsWith("es") ? "es" : "en");
}

/* ---------- Importación ---------- */
function mundoVacio() {
  const sin = ["actors", "journal", "playlists", "macros", "tables", "cards", "items"].every(c => !game[c]?.size);
  return sin && game.scenes.contents.every(s => (s.background?.src ?? "").startsWith("nue/") && !s.tokens.size);
}

export async function importarAventura({ lang = idioma(), confirmar = false } = {}) {
  if (!game.user.isGM) return ui.notifications.warn(t("OnlyGM"));
  const pack = game.packs.get(`${MOD}.aventura-${lang}`);
  if (!pack) return ui.notifications.error(t("NoPack"));
  if (confirmar && !mundoVacio()) {
    const ok = await DialogV2.confirm({
      window: { title: t("Import"), icon: "fa-solid fa-file-import" }, content: `<p>${t("ImportOverwrite")}</p>`,
      yes: { label: t("Import"), icon: "fa-solid fa-file-import" }, no: { label: t("Cancel") }, rejectClose: false
    });
    if (!ok) return;
  }
  ui.notifications.info(t("Importing"));
  const adv = (await pack.getDocuments())[0];
  // Lo que los jugadores ya llevan (pregenerados) no se pisa al reimportar.
  const respetarPJ = data => {
    if (data.toUpdate.Actor) data.toUpdate.Actor = data.toUpdate.Actor.filter(d => d.flags?.[MOD]?.tipo !== "pj");
  };
  await adv.import({ dialog: false, preImport: [respetarPJ] });
  await game.settings.set(MOD, "importada", lang);
  await game.settings.set(MOD, "version", game.modules.get(MOD).version);
  await registrarDireccion(game.modules.get("mr-direccion")?.api, true);
  await game.scenes.find(s => s.flags?.[MOD]?.slug === "portada")?.activate();
  ui.notifications.info(t("Imported"));
}

async function ofrecerActualizacion() {
  const ahora = game.modules.get(MOD).version, antes = game.settings.get(MOD, "version");
  if (!antes || !foundry.utils.isNewerVersion(ahora, antes)) return;
  const ok = await DialogV2.confirm({
    window: { title: t("Updated"), icon: "fa-solid fa-dna" }, content: `<p>${t("UpdatedText", { antes: esc(antes), ahora: esc(ahora) })}</p>`,
    yes: { label: t("Reimport"), icon: "fa-solid fa-file-import" }, no: { label: t("Later") }, rejectClose: false
  });
  if (ok) await importarAventura();
  else await game.settings.set(MOD, "version", ahora);
}

/* ---------- MR- Dirección ---------- */
let registrado = null;
async function registrarDireccion(api, forzar = false) {
  if (!api?.registerPack || (registrado && !forzar)) return;
  const lang = idioma();
  if (registrado === lang) return;
  try {
    const pack = await (await fetch(`modules/${MOD}/content/direccion-${lang}.json`)).json();
    api.registerPack(pack); registrado = lang;
  } catch (e) { console.error(`${MOD} | no se pudo registrar el paquete de dirección`, e); }
}
Hooks.on("mrDireccion.ready", api => registrarDireccion(api));

/* ---------- Registro de Ausencias ---------- */
const personas = () => game.actors.filter(a => ["pj", "pnj"].includes(a.flags?.[MOD]?.tipo) && !["forma", "matriz"].includes(a.flags[MOD].slug))
  .sort((a, b) => (a.flags[MOD].tipo === "pj" ? 0 : 1) - (b.flags[MOD].tipo === "pj" ? 0 : 1) || a.name.localeCompare(b.name));
const huella = a => Number(a.flags?.[MOD]?.huella ?? 0);
const esCopia = a => !!a.flags?.[MOD]?.copia;

async function guardar(form) {
  const cambios = personas().map(a => ({
    _id: a.id, [`flags.${MOD}.huella`]: Number(form.elements[`h-${a.id}`]?.value ?? 0), [`flags.${MOD}.copia`]: !!form.elements[`c-${a.id}`]?.checked
  }));
  await Actor.updateDocuments(cambios);
}

/** Papeletas: una por persona con Huella 2, dos con Huella 3; las copias no entran. Máximo tres copias activas. */
export function papeletas(lista) {
  return lista.filter(p => !p.copia).flatMap(p => p.huella >= 3 ? [p, p] : p.huella === 2 ? [p] : []);
}

export async function sorteo() {
  if (!game.user.isGM) return ui.notifications.warn(t("OnlyGM"));
  const gente = personas();
  if (!gente.length) return ui.notifications.warn(t("NoPeople"));
  const filas = gente.map(a => `<tr><td><img src="${esc(a.img)}" alt=""> ${esc(a.name)}</td>
    <td><select name="h-${a.id}">${[0, 1, 2, 3].map(n => `<option value="${n}" ${huella(a) === n ? "selected" : ""}>${n}</option>`).join("")}</select></td>
    <td><input type="checkbox" name="c-${a.id}" ${esCopia(a) ? "checked" : ""}></td></tr>`).join("");
  const conds = [1, 2, 3, 4].map(n => `<li><label><input type="checkbox" name="cond${n}"> ${t(`Cond${n}`)}</label></li>`).join("");
  const accion = await DialogV2.wait({
    window: { title: t("LogTitle"), icon: "fa-solid fa-dna" }, position: { width: 520 }, classes: ["mr-eidolon-registro"],
    content: `<p class="hint">${t("LogHint")}</p><div class="tabla"><table><tr><th>${t("Person")}</th><th>${t("Imprint")}</th><th>${t("Copy")}</th></tr>${filas}</table></div>
      <h4>${t("CondTitle")}</h4><ul class="conds">${conds}</ul>`,
    buttons: [
      { action: "guardar", label: t("Save"), icon: "fa-solid fa-floppy-disk", callback: (ev, b) => guardar(b.form).then(() => "guardar") },
      { action: "sortear", label: t("Draw"), icon: "fa-solid fa-ticket", default: true,
        callback: async (ev, b) => { const f = b.form; await guardar(f); return [1, 2, 3, 4].every(n => f.elements[`cond${n}`].checked) ? "sortear" : "faltan"; } }
    ], rejectClose: false
  });
  if (accion === "faltan") return ChatMessage.create({ content: `<div class="mr-eidolon-chat"><p>${t("NoReplacement")}</p></div>`, whisper: ChatMessage.getWhisperRecipients("GM") });
  if (accion !== "sortear") return;
  const lista = personas().map(a => ({ a, huella: huella(a), copia: esCopia(a) }));
  if (lista.filter(p => p.copia).length >= 3) return ChatMessage.create({ content: `<div class="mr-eidolon-chat"><p>${t("Limit")}</p></div>`, whisper: ChatMessage.getWhisperRecipients("GM") });
  const urna = papeletas(lista);
  if (!urna.length) return ChatMessage.create({ content: `<div class="mr-eidolon-chat"><p>${t("NoEligible")}</p></div>`, whisper: ChatMessage.getWhisperRecipients("GM") });
  const tirada = await new Roll(`1d${urna.length}`).evaluate();
  const elegido = urna[tirada.total - 1].a;
  await elegido.update({ [`flags.${MOD}.copia`]: true });
  ChatMessage.create({
    whisper: ChatMessage.getWhisperRecipients("GM"), rolls: [tirada],
    content: `<div class="mr-eidolon-chat"><h3>${t("LogTitle")}</h3><img src="${esc(elegido.img)}" alt=""><p><b>${esc(elegido.name)}</b> — ${t("Replaced", { n: urna.length })}</p><p class="hint">${t("WriteDown")}</p></div>`
  });
}

export function registro() {
  const j = game.journal.find(x => x.flags?.[MOD]?.slug === "registro");
  if (!j) return ui.notifications.warn(t("ImportFirst"));
  j.sheet.render(true);
}

/* ---------- Configuración ---------- */
Hooks.on("renderSettings", (app, html) => {
  if (!game.user.isGM) return;
  const raiz = html instanceof HTMLElement ? html : html[0];
  const sitio = raiz?.querySelector("section.settings");
  if (!sitio || raiz.querySelector(".mr-eidolon-ajustes")) return;
  const sec = document.createElement("section");
  sec.className = "mr-eidolon-ajustes flexcol";
  sec.innerHTML = `<h4 class="divider">MR- EIDOLON</h4>
    <button type="button" data-eidolon="importar"><i class="fa-solid fa-file-import" inert></i> ${t("Import")}</button>
    <button type="button" data-eidolon="sorteo"><i class="fa-solid fa-dna" inert></i> ${t("LogTitle")}</button>`;
  sec.addEventListener("click", ev => {
    const a = ev.target.closest("button[data-eidolon]")?.dataset.eidolon;
    if (a === "importar") importarAventura({ confirmar: true });
    else if (a === "sorteo") sorteo();
  });
  sitio.after(sec);
});

Hooks.once("ready", async () => {
  game.modules.get(MOD).api = { importarAventura, sorteo, registro, idioma };
  if (!game.user.isGM) return;
  await registrarDireccion(game.modules.get("mr-direccion")?.api);
  if (!game.modules.get("mr-direccion")?.active) ui.notifications.warn(t("NeedDireccion"), { permanent: true });
  // En `ready` activeGM puede no estar resuelto: solo se descarta si ya hay otro GM activo.
  const otroGM = game.users.activeGM && game.users.activeGM !== game.user;
  if (otroGM) return;
  if (!game.settings.get(MOD, "importada") && mundoVacio()) {
    try { await importarAventura(); } catch (e) { console.error(`${MOD} | importación automática fallida`, e); }
  } else if (game.settings.get(MOD, "importada")) ofrecerActualizacion();
});
