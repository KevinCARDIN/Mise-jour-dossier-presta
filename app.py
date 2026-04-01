import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import requests
import base64
import urllib.parse

# --- CONFIGURATION & PERFORMANCE ---
st.set_page_config(page_title="LetaHost - Partenaires", layout="centered")

# --- DESIGN PREMIUM & TEXTES LISIBLES (STRICTEMENT INCHANGÉ) ---
def set_design():
    try:
        with open("fond.png", "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        st.markdown(f'''
        <style>
        .stApp {{ background-image: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("data:image/png;base64,{bin_str}"); background-size: cover; background-attachment: fixed; }}
        
        input {{ color: black !important; }}
        div[data-baseweb="select"] input {{ color: black !important; }}
        div[role="listbox"] {{ color: black !important; }}

        .stTextInput>div>div>input, .stTextArea>div>textarea, .stSelectbox>div>div, .stNumberInput>div>div>input {{ 
            background-color: white !important; color: black !important; font-size: 18px !important; border-radius: 8px !important;
        }}
        
        h2 {{ font-size: 3.5rem !important; font-weight: 800 !important; color: white !important; text-align: center !important; line-height: 1.1 !important; margin-bottom: 30px !important; }}
        
        div.stButton > button {{ 
            background-color: #f1c40f !important; color: black !important; font-weight: bold !important; 
            border-radius: 8px !important; text-transform: uppercase !important; border: none !important;
            height: 55px !important; font-size: 16px !important;
        }}
        
        p, label, li, .stMarkdown {{ color: white !important; text-align: center !important; font-size: 1.1rem !important; }}
        [data-testid="column"] {{ display: flex !important; justify-content: center !important; align-items: center !important; }}
        
        .city-scroll {{
            max-height: 350px;
            overflow-y: auto;
            background: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 10px;
            text-align: left !important;
        }}

        .guide-box {{ text-align: left !important; background-color: rgba(255,255,255,0.1); padding: 25px; border-radius: 15px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.2); }}
        .guide-box li {{ text-align: left !important; margin-bottom: 10px; font-size: 1rem !important; }}
        </style>
        ''', unsafe_allow_html=True)
    except: pass

def render_header(title):
    try:
        with open("letahost_logo.png", "rb") as f:
            logo_encoded = base64.b64encode(f.read()).decode()
        st.markdown(f'''
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 20px;">
                <img src="data:image/png;base64,{logo_encoded}" width="140">
                <h2>{title}</h2>
            </div>
        ''', unsafe_allow_html=True)
    except: st.header(title)

set_design()

# --- CHARGEMENT ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("villes_france.csv", usecols=['nom', 'latitude', 'longitude', 'code_postal'])
        df['cp_clean'] = df['code_postal'].astype(str).str.split('.').str[0].str.zfill(5)
        df['affichage'] = df['nom'] + " (" + df['cp_clean'] + ")"
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        return df.dropna(subset=['latitude', 'longitude', 'affichage'])
    except: return pd.DataFrame()

df_v = load_data()

# --- NAVIGATION ---
if 'step' not in st.session_state: st.session_state.step = 0
def go_to(idx): st.session_state.step = idx

# --- ÉTAPES ---

if st.session_state.step == 0:
    render_header("Mise à jour Dossier")
    st.write("Bienvenue sur votre portail partenaire LetaHost.")
    st.write("Ce questionnaire permet de réactualiser vos informations et secteurs d'intervention.")
    _, col_btn, _ = st.columns([1, 1.5, 1])
    with col_btn: st.button("COMMENCER", on_click=go_to, args=(1,), use_container_width=True)

elif st.session_state.step == 1:
    render_header("1. Vos informations")
    nom = st.text_input("NOM *", value=st.session_state.get('nom', ''))
    prenom = st.text_input("Prénom *", value=st.session_state.get('prenom', ''))
    _, col_btn, _ = st.columns([1, 1.5, 1])
    with col_btn:
        if st.button("CONTINUER", use_container_width=True):
            if nom.strip() and prenom.strip():
                st.session_state.nom, st.session_state.prenom = nom, prenom
                go_to(2); st.rerun()
            else: st.error("Nom et Prénom sont obligatoires.")

elif st.session_state.step == 2:
    render_header("2. Coordonnées & Structure")
    societe = st.text_input("Nom de la société", value=st.session_state.get('societe', ''))
    siret = st.text_input("Numéro SIRET *", value=st.session_state.get('siret', ''))
    statut = st.selectbox("Statut juridique *", ["Auto/Micro-Entrepreneur (EI)", "EURL", "SARL", "SA", "SAS", "SASU", "Autre"])
    c1, c2 = st.columns(2)
    with c1: tel1 = st.text_input("Téléphone *", value=st.session_state.get('tel1', ''))
    with c2: email1 = st.text_input("Email *", value=st.session_state.get('email1', ''))
    cb1, cb2 = st.columns(2)
    with cb1: st.button("RETOUR", on_click=go_to, args=(1,), use_container_width=True)
    with cb2: 
        if st.button("SUIVANT", use_container_width=True):
            if siret.strip() and tel1.strip() and email1.strip():
                st.session_state.update({"societe":societe, "siret":siret, "statut":statut, "tel1":tel1, "email1":email1})
                go_to(3); st.rerun()
            else: st.error("Veuillez remplir les champs obligatoires (*).")

elif st.session_state.step == 3:
    render_header("3. Attestation de vigilance")
    st.markdown('<div class="guide-box"><b>👉 Comment récupérer votre attestation :</b><ul><li>1. Connectez-vous sur votre espace <b>urssaf.fr</b></li><li>2. Rubrique <b>« Mes documents »</b></li><li>3. Cliquez sur <b>« Demander une attestation »</b></li><li>4. Sélectionnez <b>« Attestation de vigilance »</b> et téléchargez le PDF</li></ul></div>', unsafe_allow_html=True)
    file = st.file_uploader("Joindre le PDF *", type=["pdf"])
    if file: st.session_state.file_bytes = file.read()
    cb1, cb2 = st.columns(2)
    with cb1: st.button("RETOUR", on_click=go_to, args=(2,), use_container_width=True)
    with cb2: 
        if st.button("SUIVANT", use_container_width=True):
            if 'file_bytes' in st.session_state: go_to(4); st.rerun()
            else: st.error("L'attestation PDF est obligatoire.")

elif st.session_state.step == 4:
    render_header("4. Organisation")
    options_org = ["Seul, sans remplaçant même ponctuel", "Seul, avec un remplaçant ponctuel", "Avec 1 ou 2 collaborateurs", "En équipe", "Autre"]
    org_type = st.radio("Structure de travail *", options_org)
    st.session_state.org_type = org_type
    if "Seul, sans" not in org_type:
        st.session_state.details_org = st.text_input("Noms des intervenants :", value=st.session_state.get('details_org', ''))
        st.session_state.tels_remp = st.text_area("Téléphones :", value=st.session_state.get('tels_remp', ''))
    cb1, cb2 = st.columns(2)
    with cb1: st.button("RETOUR", on_click=go_to, args=(3,), use_container_width=True)
    with cb2: st.button("SUIVANT", on_click=go_to, args=(5,), use_container_width=True)

elif st.session_state.step == 5:
    render_header("5. Disponibilités & Tarifs")
    dispos = st.text_area("Vos jours et plages horaires ?", value=st.session_state.get('dispos', ''))
    st.markdown("---")
    c_dim, c_fer = st.columns(2)
    with c_dim:
        st.session_state.maj_dim = st.radio("Majoration Dimanche ?", ["Non", "Oui"])
        if st.session_state.maj_dim == "Oui":
            st.session_state.montant_dim = st.text_input("Montant Dimanche :", value=st.session_state.get('montant_dim', '0'))
    with c_fer:
        st.session_state.maj_ferie = st.radio("Majoration Jours Fériés ?", ["Non", "Oui"])
        if st.session_state.maj_ferie == "Oui":
            st.session_state.lesquels_ferie = st.text_input("Quels jours ?", value=st.session_state.get('lesquels_ferie', ''))
            st.session_state.montant_ferie = st.text_input("Montant Fériés :", value=st.session_state.get('montant_ferie', '0'))
    cb1, cb2 = st.columns(2)
    with cb1: st.button("RETOUR", on_click=go_to, args=(4,), use_container_width=True)
    with cb2: 
        if st.button("SUIVANT", use_container_width=True):
            if dispos.strip():
                st.session_state.dispos = dispos
                go_to(6); st.rerun()
            else: st.error("Veuillez renseigner vos disponibilités.")

elif st.session_state.step == 6:
    render_header("6. Secteur")
    v_base = st.selectbox("Ville de départ", sorted(df_v['affichage'].unique()) if not df_v.empty else [])
    rayon = st.slider("Rayon (km)", 0, 150, st.session_state.get('rayon', 30))
    _, col_calc, _ = st.columns([1, 1.5, 1])
    with col_calc:
        if st.button("CALCULER LES VILLES", use_container_width=True):
            sel = df_v[df_v['affichage'] == v_base].iloc[0]
            def dist(row): return geodesic((float(sel['latitude']), float(sel['longitude'])), (row['latitude'], row['longitude'])).km
            df_v['d'] = df_v.apply(dist, axis=1)
            st.session_state.villes_trouvees = df_v[df_v['d'] <= rayon]['affichage'].tolist()
            st.session_state.rayon = rayon

    if st.session_state.get('villes_trouvees'):
        st.write("Décochez les villes où vous n'intervenez pas :")
        v_finales = []
        st.markdown('<div class="city-scroll">', unsafe_allow_html=True)
        for v in st.session_state.villes_trouvees:
            if st.checkbox(v, value=True, key=f"v_{v}"): v_finales.append(v)
        st.markdown('</div>', unsafe_allow_html=True)
        st.session_state.villes_finales_list = v_finales

    st.session_state.villes_sup = st.text_area("Autres villes (manuelles) :", value=st.session_state.get('villes_sup', ''))
    cb1, cb2 = st.columns(2)
    with cb1: st.button("RETOUR", on_click=go_to, args=(5,), use_container_width=True)
    with cb2: 
        if st.button("FINALISER", use_container_width=True):
            if st.session_state.get('villes_finales_list'): go_to(7); st.rerun()
            else: st.error("Sélectionnez au moins une ville.")

elif st.session_state.step == 7:
    render_header("7. Finalisation")
    st.session_state.notes = st.text_area("Avez-vous d'autres informations à nous communiquer ?", value=st.session_state.get('notes', ''))
    
    def submit():
        # FIX : Encodage sécurisé de l'URL pour gérer l'accent "à"
        raw_url = "https://hub.cardin.cloud/webhook/Miseàjourdossierpresta"
        url_parts = list(urllib.parse.urlparse(raw_url))
        url_parts[2] = urllib.parse.quote(url_parts[2])
        safe_url = urllib.parse.urlunparse(url_parts)
        
        f = st.session_state.get('file_bytes')
        content = base64.b64encode(f).decode() if f else ""
        payload = {
            "identite": {"nom": st.session_state.get('nom'), "prenom": st.session_state.get('prenom'), "siret": st.session_state.get('siret'), "statut": st.session_state.get('statut')},
            "contact": {"tel": st.session_state.get('tel1'), "email": st.session_state.get('email1')},
            "disponibilites": st.session_state.get('dispos'),
            "tarifs": {"dimanche": st.session_state.get('montant_dim'), "feries": st.session_state.get('montant_ferie')},
            "secteur": {"villes_selectionnees": st.session_state.get('villes_finales_list', []), "villes_sup": st.session_state.get('villes_sup')},
            "notes": st.session_state.notes, 
            "attestation": content
        }
        try:
            # Ajout d'un timeout de 15s pour éviter que ça bloque sans raison
            r = requests.post(safe_url, json=payload, timeout=15)
            if r.status_code in [200, 201]: 
                go_to(8); st.rerun()
            else:
                st.error(f"Erreur de transmission (Code: {r.status_code}). Veuillez réessayer.")
        except Exception as e:
            st.error(f"Erreur de connexion : {str(e)}")

    cb1, cb2 = st.columns(2)
    with cb1: st.button("RETOUR", on_click=go_to, args=(6,), use_container_width=True)
    with cb2: 
        if st.button("TRANSMETTRE", use_container_width=True): submit()

elif st.session_state.step == 8:
    render_header("Merci !")
    st.balloons()
    st.write("Votre dossier a été transmis avec succès.")
    _, col_btn, _ = st.columns([1, 1.5, 1])
    with col_btn: st.button("RETOUR À L'ACCUEIL", on_click=lambda: st.session_state.clear(), use_container_width=True)