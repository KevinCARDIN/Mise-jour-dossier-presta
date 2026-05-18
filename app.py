import os
import re
import json
import base64
import pandas as pd
import requests
import streamlit as st
from geopy.distance import geodesic

# --- CONFIGURATION ---
BOARD_ID = 1281234391
MONDAY_API = "https://api.monday.com/v2"
MONDAY_FILE_API = "https://api.monday.com/v2/file"
MONDAY_ITEM_URL = "https://invest-malin.monday.com/boards/1281234391/pulls/{}"

# Colonnes reelles du board "Fees / Genies du Logis" (jamais les colonnes "OLD")
COL = {
    "nom": "text_mm12q8b1",
    "prenom": "text_mm12jeyz",
    "societe": "text_mm12chdd",
    "statut": "color_mm122c1y",
    "siret": "chiffres__1",
    "cp": "text_mkp8h1g0",
    "villes": "long_text_mm12h8t8",
    "attestation": "file_mm3a586k",
    "dispos": "long_text_mm127h7b",
    "tel": "t_l_phone",
    "email": "e_mail",
    "infos": "texte85",
}

STATUTS = ["Auto/Micro-Entrepreneur (EI)", "EURL", "SARL", "SA", "SAS", "SASU", "Autre"]
ORG_VIDE = "— Non renseigné —"
ORG_OPTIONS = [
    ORG_VIDE,
    "Seul, sans remplaçant même ponctuel",
    "Seul, avec un remplaçant ponctuel",
    "Avec 1 ou 2 collaborateurs",
    "En équipe",
    "Autre",
]

st.set_page_config(page_title="LetaHost - Questionnaire prestataire", layout="centered")


# --- DESIGN PREMIUM & FIX MODE SOMBRE ---
def set_design():
    try:
        with open("fond.png", "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        st.markdown(f'''
        <style>
        .stApp {{ background-image: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("data:image/png;base64,{bin_str}"); background-size: cover; background-attachment: fixed; }}

        input, textarea {{ color: black !important; -webkit-text-fill-color: black !important; }}
        .stTextInput>div>div>input, .stTextArea>div>textarea, .stNumberInput>div>div>input {{
            background-color: #ffffff !important; color: #000000 !important;
            font-size: 17px !important; border-radius: 8px !important;
        }}
        div[data-baseweb="select"] > div {{ background-color: #ffffff !important; color: #000000 !important; border-radius: 8px !important; }}
        div[data-baseweb="select"] span, div[data-baseweb="select"] div {{ color: #000000 !important; }}
        ul[role="listbox"], div[role="listbox"] {{ background-color: #ffffff !important; }}
        li[role="option"] {{ background-color: #ffffff !important; color: #000000 !important; }}
        li[role="option"]:hover {{ background-color: #f1c40f !important; }}

        h2 {{ font-size: 2.6rem !important; font-weight: 800 !important; color: white !important; text-align: center !important; line-height: 1.15 !important; margin-bottom: 10px !important; }}
        h3 {{ font-size: 1.5rem !important; font-weight: 700 !important; color: #f1c40f !important; margin-top: 10px !important; }}

        div.stButton > button {{
            background-color: #f1c40f !important; color: black !important; font-weight: bold !important;
            border-radius: 8px !important; text-transform: uppercase !important; border: none !important;
            height: 52px !important; font-size: 15px !important;
        }}

        p, label, li, .stMarkdown {{ color: white !important; font-size: 1.05rem !important; }}

        .city-scroll {{ max-height: 320px; overflow-y: auto; background: rgba(255,255,255,0.05);
            padding: 15px; border-radius: 10px; }}
        .guide-box {{ background-color: rgba(255,255,255,0.1); padding: 22px; border-radius: 15px;
            margin-bottom: 15px; border: 1px solid rgba(255,255,255,0.2); }}
        .guide-box li {{ margin-bottom: 8px; font-size: 1rem !important; }}
        .presta-tag {{ background: rgba(241,196,15,0.15); border: 1px solid #f1c40f; border-radius: 10px;
            padding: 12px 18px; text-align: center; margin-bottom: 18px; }}
        </style>
        ''', unsafe_allow_html=True)
    except Exception:
        pass


def render_header(title):
    try:
        with open("letahost_logo.png", "rb") as f:
            logo = base64.b64encode(f.read()).decode()
        st.markdown(f'''
            <div style="display:flex;flex-direction:column;align-items:center;margin-bottom:15px;">
                <img src="data:image/png;base64,{logo}" width="130">
                <h2>{title}</h2>
            </div>
        ''', unsafe_allow_html=True)
    except Exception:
        st.header(title)


set_design()


# --- DONNEES VILLES ---
@st.cache_data
def load_villes():
    try:
        df = pd.read_csv("villes_france.csv", usecols=['nom', 'latitude', 'longitude', 'code_postal'])
        df['cp_clean'] = df['code_postal'].astype(str).str.split('.').str[0].str.zfill(5)
        df['affichage'] = df['nom'] + " (" + df['cp_clean'] + ")"
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        return df.dropna(subset=['latitude', 'longitude', 'affichage'])
    except Exception:
        return pd.DataFrame()


df_v = load_villes()


# --- API MONDAY ---
def get_token():
    tok = os.environ.get("MONDAY_API_TOKEN")
    if not tok:
        try:
            tok = st.secrets["MONDAY_API_TOKEN"]
        except Exception:
            tok = None
    return tok


def monday_query(query, variables=None):
    tok = get_token()
    if not tok:
        raise RuntimeError("Token Monday absent (variable MONDAY_API_TOKEN).")
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    r = requests.post(MONDAY_API, json=payload,
                      headers={"Authorization": tok, "API-Version": "2024-10"}, timeout=30)
    data = r.json()
    if data.get("errors"):
        raise RuntimeError(str(data["errors"]))
    return data["data"]


def fetch_item(item_id):
    q = """query ($id: [ID!]) {
        items (ids: $id) { id name column_values { id text } }
    }"""
    data = monday_query(q, {"id": [str(item_id)]})
    items = data.get("items") or []
    return items[0] if items else None


def prefill_from_item(item):
    cv = {c["id"]: (c.get("text") or "") for c in item["column_values"]}
    return {k: cv.get(cid, "") for k, cid in COL.items()}


def parse_nom_from_title(title):
    """Déduit prénom / nom / société depuis le titre de ligne Monday
    ("Prénom NOM - Société", éventuellement "Prénom NOM / autre personne")."""
    raw = (title or "").strip()
    societe = ""
    if " - " in raw:
        name_part, societe = raw.split(" - ", 1)
    else:
        name_part = raw
    name_part = name_part.strip()
    societe = societe.strip()
    if "/" in name_part:
        name_part = name_part.split("/")[0].strip()
    words = name_part.split()
    n_caps = 0
    for w in reversed(words):
        if w.isupper() and any(c.isalpha() for c in w):
            n_caps += 1
        else:
            break
    if 0 < n_caps < len(words):
        prenom = " ".join(words[:len(words) - n_caps])
        nom = " ".join(words[len(words) - n_caps:])
    elif words:
        prenom, nom = words[0], " ".join(words[1:])
    else:
        prenom, nom = "", ""
    return prenom, nom, societe


def write_item(item_id, vals):
    q = """mutation ($board: ID!, $item: ID!, $vals: JSON!) {
        change_multiple_column_values (board_id: $board, item_id: $item, column_values: $vals) { id }
    }"""
    monday_query(q, {"board": str(BOARD_ID), "item": str(item_id), "vals": json.dumps(vals)})


def upload_attestation(item_id, filename, file_bytes):
    tok = get_token()
    q = ('mutation ($file: File!) { add_file_to_column '
         '(item_id: %s, column_id: "%s", file: $file) { id } }') % (item_id, COL["attestation"])
    operations = json.dumps({"query": q, "variables": {"file": None}})
    files = {"variables.file": (filename, file_bytes, "application/pdf")}
    data = {"operations": operations, "map": json.dumps({"variables.file": ["variables.file"]})}
    r = requests.post(MONDAY_FILE_API, data=data, files=files,
                      headers={"Authorization": tok}, timeout=90)
    res = r.json()
    if res.get("errors"):
        raise RuntimeError(str(res["errors"]))


# --- IDENTIFICATION DU PRESTATAIRE ---
render_header("Questionnaire prestataire")

item_id = st.query_params.get("item")
if not item_id:
    st.warning("Ouvrez ce questionnaire depuis le bouton sur la ligne du prestataire dans Monday.")
    manual = st.text_input("...ou saisissez manuellement l'ID de l'item Monday")
    if manual.strip().isdigit():
        item_id = manual.strip()
    else:
        st.stop()

if st.session_state.get("loaded_item") != str(item_id):
    try:
        item = fetch_item(item_id)
    except Exception as e:
        st.error(f"Impossible de charger le prestataire : {e}")
        st.stop()
    if not item:
        st.error("Aucun prestataire trouvé pour cet identifiant.")
        st.stop()
    pre = prefill_from_item(item)
    t_prenom, t_nom, t_societe = parse_nom_from_title(item["name"])
    st.session_state["f_nom"] = pre["nom"] or t_nom
    st.session_state["f_prenom"] = pre["prenom"] or t_prenom
    st.session_state["f_societe"] = pre["societe"] or t_societe
    st.session_state["f_statut"] = pre["statut"] if pre["statut"] in STATUTS else ""
    st.session_state["f_siret"] = pre["siret"]
    st.session_state["f_tel"] = pre["tel"]
    st.session_state["f_email"] = pre["email"]
    st.session_state["f_dispos"] = pre["dispos"]
    st.session_state["f_villes_sup"] = ""
    st.session_state["f_org"] = ORG_VIDE
    st.session_state["f_org_intervenants"] = ""
    st.session_state["f_org_tels"] = ""
    st.session_state["f_org_emails"] = ""
    st.session_state["f_notes"] = pre["infos"]
    st.session_state["cur_cp"] = pre["cp"]
    st.session_state["cur_villes"] = pre["villes"]
    st.session_state["item_name"] = item["name"]
    st.session_state["villes_trouvees"] = []
    st.session_state["loaded_item"] = str(item_id)

st.markdown(
    f'<div class="presta-tag">Prestataire : <b>{st.session_state.get("item_name", "")}</b><br>'
    f'<a href="{MONDAY_ITEM_URL.format(item_id)}" target="_blank" style="color:#f1c40f;">Voir la ligne dans Monday</a></div>',
    unsafe_allow_html=True)
st.caption("Tous les champs sont optionnels : enregistrez même si une information manque.")

# --- 1. INFORMATIONS ---
st.markdown("### 1. Informations")
c1, c2 = st.columns(2)
with c1:
    st.text_input("NOM", key="f_nom")
with c2:
    st.text_input("Prénom", key="f_prenom")
st.text_input("Nom de société", key="f_societe")
st.selectbox("Statut juridique", [""] + STATUTS, key="f_statut")
st.text_input("Numéro SIRET", key="f_siret")
c3, c4 = st.columns(2)
with c3:
    st.text_input("Téléphone", key="f_tel")
with c4:
    st.text_input("E-mail", key="f_email")

# --- 2. ATTESTATION DE VIGILANCE ---
st.markdown("### 2. Attestation de vigilance")
st.markdown('''
<div class="guide-box">
    <p style="font-weight:bold;color:#f1c40f;margin-bottom:8px;">Demander l'attestation de vigilance.</p>
    <ul>
        <li>1. Se connecter sur l'espace <b>urssaf.fr</b></li>
        <li>2. Rubrique <b>« Mes documents »</b></li>
        <li>3. Cliquer sur <b>« Demander une attestation »</b></li>
        <li>4. Choisir <b>« Attestation de vigilance »</b> et télécharger le PDF</li>
    </ul>
</div>
''', unsafe_allow_html=True)
attestation = st.file_uploader("Joindre le PDF (optionnel)", type=["pdf"])

# --- 3. ORGANISATION ---
st.markdown("### 3. Organisation")
st.radio("Structure de travail", ORG_OPTIONS, key="f_org")
st.text_input("Noms des intervenants", key="f_org_intervenants")
st.text_input("Téléphone(s) de contact", key="f_org_tels")
st.text_input("E-mail(s) de contact", key="f_org_emails")

# --- 4. DISPONIBILITES ---
st.markdown("### 4. Disponibilités")
st.text_area("Jours et plages horaires de disponibilité", key="f_dispos")

# --- 5. SECTEUR (recherche dynamique de villes) ---
st.markdown("### 5. Secteur d'intervention")
if st.session_state.get("cur_villes"):
    st.caption(f"Villes actuellement dans Monday : {st.session_state['cur_villes']}")
if st.session_state.get("cur_cp"):
    st.caption(f"Codes postaux actuellement dans Monday : {st.session_state['cur_cp']}")
st.caption("Laissez le secteur vide pour conserver les valeurs actuelles ; calculez pour les remplacer.")

if not df_v.empty:
    v_base = st.selectbox("Ville de départ", sorted(df_v['affichage'].unique()))
    rayon = st.slider("Rayon (km)", 0, 150, 30)
    if st.button("CALCULER LES VILLES"):
        sel = df_v[df_v['affichage'] == v_base].iloc[0]
        lat1, lon1 = float(sel['latitude']), float(sel['longitude'])
        d = df_v.copy()
        d['dist'] = d.apply(lambda r: geodesic((lat1, lon1), (r['latitude'], r['longitude'])).km, axis=1)
        st.session_state["villes_trouvees"] = d[d['dist'] <= rayon].sort_values('dist')['affichage'].tolist()

    if st.session_state.get("villes_trouvees"):
        st.write("Décochez les villes où le prestataire n'intervient pas :")
        st.markdown('<div class="city-scroll">', unsafe_allow_html=True)
        for v in st.session_state["villes_trouvees"]:
            st.checkbox(v, value=True, key=f"v_{v}")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("Base de villes indisponible.")

st.text_area("Autres villes (saisie manuelle, séparées par des virgules)", key="f_villes_sup")

# --- 6. NOTES ---
st.markdown("### 6. Autres informations")
st.text_area("Notes / informations complémentaires", key="f_notes")


# --- ENREGISTREMENT ---
def split_affichage(a):
    m = re.match(r"^(.*) \((\d{5})\)$", a)
    if m:
        return m.group(1).strip(), m.group(2)
    return a.strip(), ""


def collect_and_save():
    s = st.session_state
    vals = {}

    nom = s.get("f_nom", "").strip()
    prenom = s.get("f_prenom", "").strip()
    societe = s.get("f_societe", "").strip()
    statut = s.get("f_statut", "").strip()
    siret = re.sub(r"\D", "", s.get("f_siret", ""))
    email = s.get("f_email", "").strip()
    dispos = s.get("f_dispos", "").strip()

    # Telephone : on garde le 1er numero saisi (la colonne Monday est de type strict)
    mt = re.search(r"\+?\d[\d .]{7,}\d", s.get("f_tel", ""))
    tel = re.sub(r"[^\d+]", "", mt.group(0)) if mt else ""

    if nom:
        vals[COL["nom"]] = nom
    if prenom:
        vals[COL["prenom"]] = prenom
    if societe:
        vals[COL["societe"]] = societe
    if statut:
        vals[COL["statut"]] = {"label": statut}
    if siret:
        vals[COL["siret"]] = siret
    if tel:
        vals[COL["tel"]] = {"phone": tel, "countryShortName": "FR"}
    if email:
        # Colonne Monday de type "email" : 1er email valide dans le champ email,
        # saisie complete (1 ou 2 emails) dans le texte affiche.
        me = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", email)
        vals[COL["email"]] = {"email": me.group(0) if me else "", "text": email}
    if dispos:
        vals[COL["dispos"]] = {"text": dispos}

    # Secteur : villes calculees + villes manuelles
    noms, cps = [], []
    for v in s.get("villes_trouvees", []):
        if s.get(f"v_{v}", True):
            n, cp = split_affichage(v)
            noms.append(n)
            if cp:
                cps.append(cp)
    for v in re.split(r"[,;\n]+", s.get("f_villes_sup", "")):
        v = v.strip()
        if v:
            noms.append(v)
    if noms:
        vals[COL["villes"]] = {"text": ", ".join(dict.fromkeys(noms))}
    if cps:
        vals[COL["cp"]] = ", ".join(dict.fromkeys(cps))

    # Organisation + Notes -> colonne "Informations" (ligne unique)
    infos = []
    org = s.get("f_org", ORG_VIDE)
    org_bits = []
    if org and org != ORG_VIDE:
        org_bits.append(f"Structure : {org}")
    if s.get("f_org_intervenants", "").strip():
        org_bits.append(f"Intervenants : {s['f_org_intervenants'].strip()}")
    if s.get("f_org_tels", "").strip():
        org_bits.append(f"Tel contacts : {s['f_org_tels'].strip()}")
    if s.get("f_org_emails", "").strip():
        org_bits.append(f"Emails contacts : {s['f_org_emails'].strip()}")
    if org_bits:
        infos.append("ORGANISATION — " + " | ".join(org_bits))
    if s.get("f_notes", "").strip():
        infos.append(s["f_notes"].strip())
    if infos:
        vals[COL["infos"]] = "  ||  ".join(infos)

    if vals:
        write_item(item_id, vals)
    if attestation is not None:
        upload_attestation(item_id, attestation.name, attestation.getvalue())
    return len(vals), attestation is not None


st.divider()
if st.button("ENREGISTRER DANS MONDAY", use_container_width=True):
    try:
        n_cols, has_file = collect_and_save()
        msg = f"Fiche mise à jour dans Monday ({n_cols} champ(s)"
        msg += " + attestation)." if has_file else ")."
        st.success(msg)
        st.balloons()
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement : {e}")
