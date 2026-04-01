import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import requests
import base64

# --- CONFIGURATION & PERFORMANCE ---
st.set_page_config(page_title="LetaHost - Partenaires", layout="centered")

# --- DESIGN PREMIUM & TEXTES LISIBLES ---
def set_design():
    try:
        with open("fond.png", "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        st.markdown(f'''
        <style>
        .stApp {{ background-image: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("data:image/png;base64,{bin_str}"); background-size: cover; background-attachment: fixed; }}
        
        /* TEXTE PLUS GROS POUR LES INPUTS (Feedback vidéo) */
        .stTextInput>div>div>input, .stTextArea>div>textarea, .stSelectbox>div>div, .stNumberInput>div>div>input {{ 
            background-color: white !important; color: black !important; font-size: 18px !important; border-radius: 8px !important;
        }}
        
        /* TITRES TRÈS IMPOSANTS */
        h2 {{ font-size: 3.5rem !important; font-weight: 800 !important; color: white !important; text-align: center !important; line-height: 1.1 !important; margin-bottom: 30px !important; }}
        
        /* BOUTONS JAUNES CENTRÉS */
        div.stButton > button {{ 
            background-color: #f1c40f !important; color: black !important; font-weight: bold !important; 
            border-radius: 8px !important; text-transform: uppercase !important; border: none !important;
            height: 55px !important; font-size: 16px !important;
        }}
        
        p, label, li, .stMarkdown {{ color: white !important; text-align: center !important; font-size: 1.1rem !important; }}
        [data-testid="column"] {{ display: flex !important; justify-content: center !important; align-items: center !important; }}
        
        /* Centrage spécifique pour les listes à puces (Guide Step 3) */
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

# --- CHARGEMENT SÉCURISÉ DU CSV (Fix AttributeError & TypeError) ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("villes_france.csv", usecols=['nom', 'latitude', 'longitude', 'code_postal'])
        # Nettoyage robuste des codes postaux (Fix float split error)
        df['cp_clean'] = df['code_postal'].astype(str).str.split('.').str[0].str.zfill(5)
        df['affichage'] = df['nom'] + " (" + df['cp_clean'] + ")"
        # Conversion numérique pour le calcul de distance (Fix TypeError step 6)
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        return df.dropna(subset=['latitude', 'longitude', 'affichage'])
    except:
        return pd.DataFrame(columns=['nom', 'latitude', 'longitude', 'affichage'])

df_v = load_data()

# --- NAVIGATION SANS DOUBLE-CLIC ---
if 'step' not in st.session_state: st.session_state.step = 0
def go_to(idx): st.session_state.step = idx

# --- ÉTAPES ---

# 0. ACCUEIL
if st.session_state.step == 0:
    render_header("Mise à jour Dossier")
    st.write("Bienvenue sur votre portail partenaire LetaHost.")
    st.write("Ce questionnaire permet de réactualiser vos informations et secteurs d'intervention.")
    _, col_btn, _ = st.columns([1, 1.5, 1])
    with col_btn: st.button("COMMENCER", on_click=go_to, args=(1,), use_container_width=True)

# 1. IDENTITÉ
elif st.session_state.step == 1:
    render_header("1. Vos informations")
    st.session_state.nom = st.text_input("NOM *", value=st.session_state.get('nom', ''))
    st.session_state.prenom = st.text_input("Prénom *", value=st.session_state.get('prenom', ''))
    if st.session_state.nom and st.session_state.prenom:
        _, col_btn, _ = st.columns([1, 1.5, 1])
        with col_btn: st.button("CONTINUER", on_click=go_to, args=(2,), use_container_width=True)

# 2. STRUCTURE (SIRET ICI)
elif st.session_state.step == 2:
    render_header("2. Coordonnées & Structure")
    st.session_state.societe = st.text_input("Nom de la société", value=st.session_state.get('societe', ''))
    st.session_state.siret = st.text_input("Numéro SIRET *", value=st.session_state.get('siret', ''))
    st.session_state.statut = st.selectbox("Statut juridique *", ["Auto/Micro-Entrepreneur (EI)", "EURL", "SARL", "SA", "SAS", "SASU", "Autre"])
    c1, c2 = st.columns(2)
    with c1: st.session_state.tel1 = st.text_input("Téléphone *", value=st.session_state.get('tel1', ''))
    with c2: st.session_state.email1 = st.text_input("Email *", value=st.session_state.get('email1', ''))
    
    cb1, cb2 = st.columns(2)
    with cb1: st.button("RETOUR", on_click=go_to, args=(1,), use_container_width=True)
    with cb2: st.button("SUIVANT", on_click=go_to, args=(3,), use_container_width=True)

# 3. ATTESTATION (GUIDE DESCRIPTIF COMPLET)
elif st.session_state.step == 3:
    render_header("3. Attestation de vigilance")
    st.markdown('''
    <div class="guide-box">
        <p style="font-weight: bold; color: #f1c40f; margin-bottom:10px;">👉 Comment récupérer votre attestation :</p>
        <ul>
            <li>1. Connectez-vous sur votre espace <b>urssaf.fr</b></li>
            <li>2. Allez dans la rubrique <b>« Mes documents »</b></li>
            <li>3. Cliquez sur <b>« Demander une attestation »</b></li>
            <li>4. Choisissez <b>« Attestation de vigilance »</b> et téléchargez le PDF</li>
        </ul>
    </div>
    ''', unsafe_allow_html=True)
    file = st.file_uploader("Joindre le PDF *", type=["pdf"])
    if file: st.session_state.file_bytes = file.read()
    
    cb1, cb2 = st.columns(2)
    with cb1: st.button("RETOUR", on_click=go_to, args=(2,), use_container_width=True)
    with cb2: st.button("SUIVANT", on_click=go_to, args=(4,), use_container_width=True)

# 4. ORGANISATION (TOUS LES CHOIX RESTAURÉS)
elif st.session_state.step == 4:
    render_header("4. Organisation")
    options_org = ["Seul, sans remplaçant même ponctuel", "Seul, avec un remplaçant ponctuel", "Avec 1 ou 2 collaborateurs", "En équipe", "Autre"]
    st.session_state.org_type = st.radio("Travaillez-vous seul ou à plusieurs ? *", options_org)
    
    if "Seul, sans" not in st.session_state.org_type:
        st.session_state.details_org = st.text_input("Noms des collaborateurs :", value=st.session_state.get('details_org', ''))
        st.session_state.tels_remp = st.text_area("Téléphones :", value=st.session_state.get('tels_remp', ''))
    
    cb1, cb2 = st.columns(2)
    with cb1: st.button("RETOUR", on_click=go_to, args=(3,), use_container_width=True)
    with cb2: st.button("SUIVANT", on_click=go_to, args=(5,), use_container_width=True)

# 5. DISPOS & TARIFS (RESTAURATION DIMANCHES / FÉRIÉS)
elif st.session_state.step == 5:
    render_header("5. Disponibilités & Tarifs")
    st.session_state.dispos = st.text_area("Vos jours et plages horaires ?", value=st.session_state.get('dispos', ''))
    
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
    with cb2: st.button("SUIVANT", on_click=go_to, args=(6,), use_container_width=True)

# 6. SECTEUR (FIX TYPEERROR & LENTEUR)
elif st.session_state.step == 6:
    render_header("6. Secteur")
    if df_v.empty:
        st.error("Données des villes indisponibles.")
    else:
        v_base = st.selectbox("Ville de départ", sorted(df_v['affichage'].unique()))
        rayon = st.slider("Rayon (km)", 0, 150, st.session_state.get('rayon', 30))
        
        if st.button("CALCULER LES VILLES", use_container_width=True):
            sel = df_v[df_v['affichage'] == v_base].iloc[0]
            lat1, lon1 = float(sel['latitude']), float(sel['longitude'])
            def fast_dist(row): return geodesic((lat1, lon1), (row['latitude'], row['longitude'])).km
            df_v['d'] = df_v.apply(fast_dist, axis=1)
            st.session_state.villes_trouvees = df_v[df_v['d'] <= rayon]['affichage'].tolist()
        
        if st.session_state.get('villes_trouvees'):
            st.session_state.villes_finales = st.multiselect("Villes validées", st.session_state.villes_trouvees, default=st.session_state.villes_trouvees)

    cb1, cb2 = st.columns(2)
    with cb1: st.button("RETOUR", on_click=go_to, args=(5,), use_container_width=True)
    with cb2: st.button("FINALISER", on_click=go_to, args=(7,), use_container_width=True)

# 7. FINALISATION
elif st.session_state.step == 7:
    render_header("7. Finalisation")
    st.session_state.notes = st.text_area("Autres notes :", value=st.session_state.get('notes', ''))
    
    def submit():
        f = st.session_state.get('file_bytes')
        content = base64.b64encode(f).decode() if f else ""
        payload = {
            "identite": {"nom": st.session_state.nom, "prenom": st.session_state.prenom, "siret": st.session_state.siret, "statut": st.session_state.statut},
            "tarifs": {"maj_dim": st.session_state.get('maj_dim'), "montant_dim": st.session_state.get('montant_dim'), "maj_ferie": st.session_state.get('maj_ferie')},
            "secteur": {"villes_selectionnees": st.session_state.get('villes_finales', [])},
            "notes": st.session_state.notes, "attestation": content
        }
        try:
            r = requests.post("https://hub.cardin.cloud/webhook/Miseàjourdossierpresta", json=payload)
            if r.status_code == 200: st.session_state.step = 8
        except: st.error("Erreur de transmission.")

    cb1, cb2 = st.columns(2)
    with cb1: st.button("RETOUR", on_click=go_to, args=(6,), use_container_width=True)
    with cb2: st.button("TRANSMETTRE", on_click=submit, use_container_width=True)

# 8. MERCI
elif st.session_state.step == 8:
    render_header("Merci !")
    st.balloons()
    st.write("Votre dossier a été transmis avec succès.")
    st.button("NOUVEL ENVOI", on_click=lambda: st.session_state.clear(), use_container_width=True)