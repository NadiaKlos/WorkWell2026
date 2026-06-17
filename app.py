import json
import random
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ═══════════════════════════════════════════════════════════════
#  ① CONFIGURATION FIXE
# ═══════════════════════════════════════════════════════════════
PARTICIPANTS: list[str] = [
    "Nadia",
    "Nassima",
    "Emma",
    "Guillaume",
    "Christophe",
    "Richard",
    "Abderrahmen",
]

GROUPS: dict[str, int] = {
    "La Crypte":  4,
    "L'Immortel": 3,
}

# Dégradés de couleur pour les segments de la roue (par groupe)
GROUP_SHADES: dict[str, list[str]] = {
    "La Crypte":  ["#5a64a8", "#6d78be", "#4a548f", "#7e89cb"],
    "L'Immortel": ["#b05a72", "#c06e84", "#934b60", "#cf859b"],
}

GROUP_CSS: dict[str, str] = {
    "La Crypte":  "group-crypte",
    "L'Immortel": "group-immortel",
}

DB_PATH = Path(__file__).with_name("tirage.db")


def _db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _db_init() -> None:
    with _db_connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assignments (
                participant TEXT PRIMARY KEY,
                group_name TEXT NOT NULL,
                assigned_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _db_load_assignments() -> list[dict[str, str]]:
    with _db_connect() as conn:
        rows = conn.execute(
            """
            SELECT participant, group_name
            FROM assignments
            ORDER BY assigned_at ASC
            """
        ).fetchall()

    # On filtre strictement pour rester cohérent avec la configuration figée.
    valid_participants = set(PARTICIPANTS)
    valid_groups = set(GROUPS.keys())
    cleaned: list[dict[str, str]] = []
    for row in rows:
        p = row["participant"]
        g = row["group_name"]
        if p in valid_participants and g in valid_groups:
            cleaned.append({"Participant": p, "Groupe": g})
    return cleaned


def _db_save_assignment(participant: str, group_name: str) -> None:
    with _db_connect() as conn:
        conn.execute(
            """
            INSERT INTO assignments (participant, group_name, assigned_at)
            VALUES (?, ?, ?)
            """,
            (participant, group_name, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()

# ═══════════════════════════════════════════════════════════════
#  ② PAGE CONFIG & CSS
# ═══════════════════════════════════════════════════════════════
st.set_page_config(page_title=" WorkWell 2026 - Tirage au Sort", page_icon="🎡", layout="wide")

st.markdown(
    """
    <style>
        .main-title {
            font-size: 2.7rem; font-weight: 900; text-align: center;
            background: linear-gradient(135deg, #5a64a8, #b05a72);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin-bottom: .1rem;
        }
        .sub-title {
            text-align: center; color: #888; font-size: 1rem; margin-bottom: 1.6rem;
        }
        .result-box {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border: 2px solid #5a64a8; border-radius: 16px;
            padding: 1.4rem 2rem; font-size: 1.65rem; text-align: center; color: #fff;
            box-shadow: 0 4px 20px rgba(90,100,168,.28); margin: .8rem 0;
        }
        .player-box {
            background: linear-gradient(135deg, #1e1a30, #28153a);
            border: 2px solid #b05a72; border-radius: 14px;
            padding: 1.1rem 1.6rem; font-size: 1.2rem;
            text-align: center; color: #fff;
            box-shadow: 0 4px 14px rgba(176,90,114,.24); margin: .6rem 0;
        }
        .group-card {
            border-radius: 12px; padding: .75rem 1.1rem; margin: .35rem 0;
            font-weight: 700; font-size: .95rem; color: #fff;
            display: flex; justify-content: space-between; align-items: center;
        }
        .group-crypte   { background: linear-gradient(90deg, #4a548f, #6d78be); }
        .group-immortel { background: linear-gradient(90deg, #934b60, #c06e84); }
        .pill {
            background: rgba(255,255,255,.25); border-radius: 99px;
            padding: .15rem .65rem; font-size: .82rem; font-weight: 700;
        }
        .badge {
            display: inline-block; border-radius: 8px; padding: .18rem .6rem;
            font-size: .82rem; font-weight: 700; color: #fff; margin: .12rem .1rem;
        }
        .badge-pending       { background: #3a3a4a; }
        .badge-done-crypte   { background: #5a64a8; }
        .badge-done-immortel { background: #a2586f; }
        .done-box {
            background: linear-gradient(135deg, #0f4c2a, #1a7a42);
            border: 2px solid #2ecc71; border-radius: 16px; padding: 1.6rem;
            text-align: center; font-size: 1.9rem; color: #fff; margin: 1rem 0;
        }
        div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
        .stButton>button {
            border-radius: 10px; font-weight: 700; font-size: 1rem;
            padding: .6rem 1.4rem; transition: transform .1s;
            background: #6f6f76 !important;
            border: 1px solid #5d5d63 !important;
            color: #ffffff !important;
        }
        .stButton>button:hover {
            background: #626269 !important;
            border-color: #525258 !important;
        }
        .stButton>button:disabled {
            background: #b7b7bd !important;
            border-color: #a9a9af !important;
            color: #efefef !important;
        }
        .stButton>button:active { transform: scale(.97); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════
#  ③ SESSION STATE
# ═══════════════════════════════════════════════════════════════
def _init() -> None:
    if "initialized" in st.session_state:
        return

    _db_init()
    saved_results = _db_load_assignments()

    used_per_group = {g: 0 for g in GROUPS}
    for r in saved_results:
        used_per_group[r["Groupe"]] += 1

    pool: list[str] = []
    for gname, gcap in GROUPS.items():
        remaining = max(0, gcap - used_per_group[gname])
        pool.extend([gname] * remaining)

    draw_count = len(saved_results)
    last_draw = None
    if saved_results:
        last = saved_results[-1]
        last_draw = (last["Participant"], last["Groupe"])

    st.session_state.initialized    = True
    st.session_state.pool           = pool          # places restantes à tirer
    st.session_state.results        = saved_results # [{"Participant": str, "Groupe": str}]
    st.session_state.assigned       = {r["Participant"] for r in saved_results}
    st.session_state.current_user   = None          # prénom saisi, en attente de tirage
    st.session_state.name_error     = None          # message d'erreur prénom
    st.session_state.pre_draw_pool  = None          # snapshot pool avant dernier tirage (roue)
    st.session_state.target_idx     = None          # index tiré dans pre_draw_pool
    st.session_state.last_draw      = last_draw     # (participant, groupe) dernier tirage
    st.session_state.draw_id        = draw_count    # compteur de tirages
    st.session_state.balloon_id     = draw_count    # évite ballons au rechargement
    st.session_state.auto_spin      = False         # déclenche l'auto-spin de la roue
    st.session_state.done           = len(pool) == 0
    st.session_state.clear_name_field = False       # reset du champ prénom au prochain run

_init()

# ═══════════════════════════════════════════════════════════════
#  ④ CONSTRUCTION DU HTML DE LA ROUE
# ═══════════════════════════════════════════════════════════════
def build_wheel_html(pool: list[str], auto_spin: bool, target_idx: int) -> str:
    """Génère le HTML/JS de la roue avec les segments correspondant au pool."""
    if not pool:
        return (
            "<div style='display:flex;align-items:center;justify-content:center;"
            "height:400px;font-size:2rem;color:#2ecc71;"
            "font-family:\"Segoe UI\",sans-serif;font-weight:800;text-align:center;'>"
            "✅ Tirage terminé !</div>"
        )

    # Couleurs des segments (teintes alternées pour segments du même groupe)
    counters: dict[str, int] = {}
    colors: list[str] = []
    for name in pool:
        i = counters.get(name, 0)
        shades = GROUP_SHADES.get(name, ["#888888"])
        colors.append(shades[i % len(shades)])
        counters[name] = i + 1

    names_json  = json.dumps(pool)
    colors_json = json.dumps(colors)
    auto_js     = "true" if auto_spin else "false"
    tidx_js     = str(int(target_idx))

    return f"""
<style>
  body,html{{margin:0;padding:0;background:transparent;overflow:hidden;}}
  #wc{{display:flex;flex-direction:column;align-items:center;
       font-family:'Segoe UI',sans-serif;padding:6px 0;}}
    #wheelCanvas{{border-radius:50%;
        box-shadow:0 0 28px rgba(90,100,168,.42),0 0 52px rgba(176,90,114,.18);}}
  #lbl{{margin-top:14px;font-size:1.3rem;font-weight:800;
        color:#f0f0f0;min-height:2rem;text-align:center;letter-spacing:.02em;}}
  #ptr{{width:0;height:0;
        border-left:14px solid transparent;border-right:14px solid transparent;
        border-top:40px solid #ffffff;position:relative;top:10px;
      filter:drop-shadow(0 2px 8px rgba(160,88,111,.8));}}
</style>
<div id="wc">
  <div id="ptr"></div>
  <canvas id="wheelCanvas" width="340" height="340"></canvas>
  <div id="lbl"></div>
</div>
<script>
(function(){{
  const names     = {names_json};
  const colors    = {colors_json};
  const autoSpin  = {auto_js};
  const targetIdx = {tidx_js};

  const canvas = document.getElementById('wheelCanvas');
  const ctx    = canvas.getContext('2d');
  const cx = canvas.width/2, cy = canvas.height/2, R = cx - 10;
  const N   = names.length;
  const arc = 2 * Math.PI / N;
  let angle = 0, spinning = false;

  function draw(a) {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let i = 0; i < N; i++) {{
      const s = a + i * arc, e = s + arc;
      ctx.beginPath(); ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, R, s, e); ctx.closePath();
      ctx.fillStyle = colors[i]; ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,.3)'; ctx.lineWidth = 1.5; ctx.stroke();

      ctx.save();
      ctx.translate(cx, cy); ctx.rotate(s + arc / 2);
      ctx.textAlign = 'right'; ctx.fillStyle = '#fff';
      const fs = Math.max(10, Math.min(15, Math.floor(240 / N)));
      ctx.font = `bold ${{fs}}px Segoe UI`;
      ctx.shadowColor = 'rgba(0,0,0,.75)'; ctx.shadowBlur = 5;
      ctx.fillText(names[i].slice(0, 16), R - 14, 5);
      ctx.restore();
    }}
    // Hub central
    ctx.beginPath(); ctx.arc(cx, cy, 26, 0, 2 * Math.PI);
    ctx.fillStyle = '#ffffff'; ctx.fill();
    ctx.strokeStyle = '#cccccc'; ctx.lineWidth = 2; ctx.stroke();
    ctx.beginPath(); ctx.arc(cx, cy, 10, 0, 2 * Math.PI);
        ctx.fillStyle = '#5a64a8'; ctx.fill();
  }}

  function easeOut(t) {{ return 1 - Math.pow(1 - t, 4); }}

  function getWinner(a) {{
    const norm = ((-(a + Math.PI / 2)) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI);
    return Math.floor(norm / arc) % N;
  }}

  function spin(forced) {{
    if (spinning) return;
    spinning = true;
    document.getElementById('lbl').textContent = '';
    const startA = angle, t0 = performance.now(), dur = 4200 + Math.random() * 900;
    let totalRot;

    if (forced !== undefined && forced !== null) {{
      // Atterrissage précis sur le segment targetIdx (centre du segment sous le pointeur)
      const normTarget = (forced + 0.5) * arc;
      let fa = -Math.PI / 2 - normTarget;
      const minA = startA + 5 * 2 * Math.PI;  // au moins 5 tours complets
      while (fa < minA) fa += 2 * Math.PI;
      totalRot = fa - startA;
    }} else {{
      totalRot = (Math.random() * 360 + 1440) * (Math.PI / 180);
    }}

    (function frame(now) {{
      const p = Math.min((now - t0) / dur, 1);
      angle = startA + totalRot * easeOut(p);
      draw(angle);
      if (p < 1) {{
        requestAnimationFrame(frame);
      }} else {{
        spinning = false;
        document.getElementById('lbl').textContent = '🎯 ' + names[getWinner(angle)];
      }}
    }})(t0);
  }}

  draw(angle);
  if (autoSpin) setTimeout(() => spin(targetIdx), 500);
}})();
</script>
"""

# ═══════════════════════════════════════════════════════════════
#  ⑤ HELPERS
# ═══════════════════════════════════════════════════════════════
def remaining_per_group() -> dict[str, int]:
    counts = {g: 0 for g in GROUPS}
    for g in st.session_state.pool:
        counts[g] += 1
    return counts


def build_alternating_wheel_pool(pool: list[str]) -> list[str]:
    """Construit un ordre de segments alterné entre les groupes autant que possible."""
    counts = {g: 0 for g in GROUPS}
    for g in pool:
        if g in counts:
            counts[g] += 1

    ordered_groups = list(GROUPS.keys())
    wheel_pool: list[str] = []
    while any(counts[g] > 0 for g in ordered_groups):
        for g in ordered_groups:
            if counts[g] > 0:
                wheel_pool.append(g)
                counts[g] -= 1
    return wheel_pool

def group_of(participant: str) -> str | None:
    for r in st.session_state.results:
        if r["Participant"] == participant:
            return r["Groupe"]
    return None

# ═══════════════════════════════════════════════════════════════
#  ⑥ TITRE
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="main-title"> WorkWell 2026 : Tirage au sort de l\'Escape Game</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title"></div>', unsafe_allow_html=True)
# ═══════════════════════════════════════════════════════════════
#  ⑦ LAYOUT : deux colonnes
# ═══════════════════════════════════════════════════════════════
col_left, col_right = st.columns([1, 1.5], gap="large")

# ══════════════════════════════════════════════
#  COLONNE GAUCHE — Infos + saisie du prénom
# ══════════════════════════════════════════════
with col_left:

    if st.session_state.clear_name_field:
        st.session_state.name_field = ""
        st.session_state.clear_name_field = False

    # ── Zone d'action (2-en-1) ───────────────
    st.subheader("Entrez votre prénom")
    name_input = st.text_input(
        "Entrez votre prénom :",
        key="name_field",
        placeholder="ex : Nadia",
    )

    if st.button(
        "🎲 Lancer",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.done,
    ):
        name_clean = (name_input or "").strip()
        match = next((p for p in PARTICIPANTS if p.lower() == name_clean.lower()), None)

        if not match:
            st.session_state.name_error = (
                f"❌ « {name_clean} » ne fait pas partie de la liste des participants."
            )
        elif match in st.session_state.assigned:
            st.session_state.name_error = f"⚠️ {match} a déjà été tiré·e au sort !"
        else:
            pool = st.session_state.pool
            if pool:
                pre_pool = build_alternating_wheel_pool(pool)
                idx = random.randrange(len(pre_pool))
                group = pre_pool[idx]

                try:
                    _db_save_assignment(match, group)
                except sqlite3.IntegrityError:
                    st.session_state.name_error = (
                        f"⚠️ {match} a déjà une affectation enregistrée."
                    )
                    st.rerun()

                pool.pop(pool.index(group))
                st.session_state.results.append({"Participant": match, "Groupe": group})
                st.session_state.assigned.add(match)
                st.session_state.pre_draw_pool = pre_pool
                st.session_state.target_idx = idx
                st.session_state.last_draw = (match, group)
                st.session_state.auto_spin = True
                st.session_state.draw_id += 1
                st.session_state.done = len(pool) == 0
                st.session_state.name_error = None
                st.session_state.clear_name_field = True
                st.rerun()

    if st.session_state.name_error:
        st.error(st.session_state.name_error)

    if st.session_state.done:
        st.markdown(
            '<div class="done-box">🏆 Tirage terminé !<br>'
            '<span style="font-size:1rem;opacity:.8;">Toutes les places ont été attribuées.</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Liste des participants ────────────────
    st.subheader("👥 Participants")
    html_badges = ""
    for p in PARTICIPANTS:
        grp = group_of(p)
        if grp:
            badge_css = "badge-done-crypte" if grp == "La Crypte" else "badge-done-immortel"
            html_badges += (
                f'<span class="badge {badge_css}">✓ {p}</span>'
                f'<span style="font-size:.75rem;color:#aaa;margin-right:.5rem;"> → {grp}</span>'
            )
        else:
            html_badges += f'<span class="badge badge-pending">⏳ {p}</span>'
    st.markdown(html_badges + "<br>", unsafe_allow_html=True)

    st.markdown("---")

    rpg = remaining_per_group()
    for gname, remaining in rpg.items():
        total = GROUPS[gname]
        taken = total - remaining
        css = GROUP_CSS.get(gname, "group-crypte")
        st.markdown(
            f'<div class="group-card {css}">'
            f'<span>{gname}</span>'
            f'<span class="pill">{remaining} / {total} place{"s" if remaining != 1 else ""}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.progress(taken / total if total else 0)

# ══════════════════════════════════════════════
#  COLONNE DROITE — Roue + résultats
# ══════════════════════════════════════════════
with col_right:

    # ── Roue de la fortune ───────────────────

    if st.session_state.auto_spin and st.session_state.pre_draw_pool:
        # Animation post-tirage : roue snapshot pré-tirage → atterrit sur le bon segment
        wheel_pool = st.session_state.pre_draw_pool
        do_spin    = True
        tidx       = st.session_state.target_idx or 0
    elif st.session_state.pool:
        # Affichage statique du pool courant
        wheel_pool = build_alternating_wheel_pool(st.session_state.pool)
        do_spin    = False
        tidx       = 0
    else:
        wheel_pool = []
        do_spin    = False
        tidx       = 0

    components.html(
        build_wheel_html(wheel_pool, do_spin, tidx),
        height=430,
        scrolling=False,
    )

    # ── Résultat du dernier tirage ───────────
    if st.session_state.last_draw:
        p, g = st.session_state.last_draw
        st.markdown(
            f'<div class="result-box">🎉 <b>{p}</b> rejoint <b>{g}</b> !</div>',
            unsafe_allow_html=True,
        )
        # Ballons : une seule fois par tirage
        if st.session_state.balloon_id < st.session_state.draw_id:
            st.balloons()
            st.session_state.balloon_id = st.session_state.draw_id

    # ── Tableau des attributions ─────────────
    if st.session_state.results:
        st.markdown("---")
        st.subheader("📋 Attributions en temps réel")

        df = pd.DataFrame(st.session_state.results)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Participant": st.column_config.TextColumn("👤 Participant"),
                "Groupe":      st.column_config.TextColumn("🏷️ Groupe"),
            },
        )

        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Télécharger les résultats (CSV)",
            data=csv_data,
            file_name="tirage_resultats.csv",
            mime="text/csv",
        )

    # ── Résumé final par groupe ──────────────
    if st.session_state.done and st.session_state.results:
        st.markdown("---")
        st.subheader("🏆 Résumé final par groupe")
        df_all = pd.DataFrame(st.session_state.results)
        for g, css in GROUP_CSS.items():
            members = df_all[df_all["Groupe"] == g]["Participant"].tolist()
            st.markdown(
                f'<div class="group-card {css}" style="margin-top:.5rem;">'
                f'<span>{g}</span>'
                f'<span class="pill">{len(members)} membre{"s" if len(members) > 1 else ""}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.write("  ·  ".join(members))
