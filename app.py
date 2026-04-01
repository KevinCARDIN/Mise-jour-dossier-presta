import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import requests
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="LetaHost - Partenaires", layout="centered")

# --- DESIGN "BOUTON AU CENTRE" (CRITÈRE N°1) ---
def set_design():
    try:
        with open("fond.png", "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        st.markdown(f'''
        <style>
        .stApp {{ background-image: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("data:image/png;base64,{bin_str}"); background-size: cover; background-attachment: fixed; }}
        
        /* 1. VISIBILITÉ : Texte Noir sur Blanc pour les saisies */
        input {{ color: black !important; }}
        .stTextInput>div>div>input, .stTextArea>div>textarea, .stSelectbox [data-baseweb="select"], .stNumberInput>div>div>input {{ 
            background-color: white !important; color: black !important; font-size: 18px !important; border-radius: 8px !important;
        }}
        div[data-baseweb="select"] input {{ color: black !important; }}

        /* 2. TITRES IMPOSANTS */
        h2 {{ font-size: 3.2rem !important; font-weight: 800 !important; color: white !important; text-align: center !important; line-height: 1.1 !important; margin-bottom: 25px !important; }}
        
        /* 3. LE FIX FINAL POUR LE CENTRAGE (CRITÈRE N°1) */
        /* On force le conteneur du bouton à être un bloc de centrage absolu */
        .stButton {{
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
            margin: 20px 0 !important;
        }}

        .stButton > button {{
            background-color: #f1c40f !important;
            color: #000000 !important;
            font-weight: bold !important;
            padding: 15px 40px !important;
            border-radius: 8px !important;
            width: 280px !important; /* Largeur fixe pour l'alignement */
            text-transform: uppercase !important;
            border: none !important;
        }}
        
        /* Force le centrage même dans les colonnes */
        [data-testid="column"] .stButton {{
            justify-content: center !important;
        }}

        /* Centrage des messages d'erreur et textes */
        .stAlert {{ max-width: 500px !important; margin: 10px auto !important; }}
        p, label, li, .stMarkdown {{ color: white !important; text-align: center !important; font-size: 1.1rem !important; }}
        
        /* Zone scrollable pour les villes */
        .city-scroll {{
            max-height: 300px;
            overflow-y: auto;
            background: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 10px;
            text-align: left !important;
        }}
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

# --- INITIALISATION ÉTATS ---
if 'step' not in st.session_state: st.session_state.step = 0

# --- CHARGEMENT DONNÉES ---
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
def go_to(idx): st.session_state.step = idx

# --- ÉTAPES ---

# 0. ACCUEIL
if st.session_state.step == 0:
    render_header("Mise à jour Dossier")
    st.write("Bienvenue sur votre portail partenaire LetaHost.")
    st.write("Ce questionnaire permet de réactualiser vos informations de prestataire.")
    if st.button("DÉMARRER"): go_to(1); st.rerun()

# 1. IDENTITÉ
elif st.session_state.step == 1:
    render_header("1. Vos informations")
    nom = st.text_input("NOM *", value=st.session_state.get('nom', ''))
    prenom = st.text_input("Prénom *", value=st.session_state.get('prenom', ''))
    
    if st.button("CONTINUER"):
        if nom.strip() and prenom.strip():
            st.session_state.nom, st.session_state.prenom = nom, prenom
            go_to(2); st.rerun()
        else: st.error("Le Nom et le Prénom sont obligatoires.")

# 2. STRUCTURE & SIRET
elif st.session_state.step == 2:
    render_header("2. Coordonnées & Structure")
    societe = st.text_input("Nom de la société", value=st.session_state.get('societe', ''))
    siret = st.text_input("Numéro SIRET *", value=st.session_state.get('siret', ''))
    statut = st.selectbox("Statut juridique *", ["Auto/Micro-Entrepreneur (EI)", "EURL", "SARL", "SAS", "Autre"])
    c1, c2 = st.columns(2)
    with c1: tel = st.text_input("Téléphone *", value=st.session_state.get('tel1', ''))
    with c2: mail = st.text_input("Email *", value=st.session_state.get('email1', ''))
    
    col_b, col_n = st.columns(2)
    with col_b: 
        if st.button("RETOUR", key="back2"): go_to(1); st.rerun()
    with col_n: 
        if st.button("SUIVANT", key="next2"):
            if siret.strip() and tel.strip() and mail.strip():
                st.session_state.update({"societe":societe, "siret":siret, "statut":statut, "tel1":tel, "email1":mail})
                go_to(3); st.rerun()
            else: st.error("Veuillez remplir les champs obligatoires (*).")

# 3. ATTESTATION
elif st.session_state.step == 3:
    render_header("3. Attestation de vigilance")
    st.markdown('''<div style="background:rgba(255,255,255,0.1); padding:15px; border-radius:10px; text-align:left;">
    <b>👉 Procédure pour récupérer votre document :</b><br>
    1. Connectez-vous sur <b>urssaf.fr</b> / 2. Rubrique <b>« Mes documents »</b><br>
    3. Cliquez sur <b>« Demander une attestation »</b> / 4. Téléchargez le PDF.</div>''', unsafe_allow_html=True)
    file = st.file_uploader("Joindre le PDF *", type=["pdf"])
    if file: st.session_state.file_bytes = file.read()
    
    col_b, col_n = st.columns(2)
    with col_b: 
        if st.button("RETOUR", key="back3"): go_to(2); st.rerun()
    with col_n: 
        if st.button("SUIVANT", key="next3"):
            if 'file_bytes' in st.session_state: go_to(4); st.rerun()
            else: st.error("L'attestation PDF est obligatoire.")

# 4. ORGANISATION
elif st.session_state.step == 4:
    render_header("4. Organisation")
    options = ["Seul, sans remplaçant même ponctuel", "Seul, avec un remplaçant ponctuel", "Avec 1 ou 2 collaborateurs", "En équipe", "Autre"]
    org_type = st.radio("Structure de travail *", options)
    st.session_state.org_type = org_type
    if "Seul, sans" not in org_type:
        st.session_state.details_org = st.text_input("Nom(s) des intervenants :", value=st.session_state.get('details_org', ''))
        st.session_state.tels_remp = st.text_area("Téléphones :", value=st.session_state.get('tels_remp', ''))
    
    col_b, col_n = st.columns(2)
    with col_b: 
        if st.button("RETOUR", key="back4"): go_to(3); st.rerun()
    with col_n: 
        if st.button("SUIVANT", key="next4"): go_to(5); st.rerun()

# 5. DISPOS & TARIFS
elif st.session_state.step == 5:
    render_header("5. Disponibilités & Tarifs")
    dispos = st.text_area("Vos jours et plages horaires ?", value=st.session_state.get('dispos', ''))
    st.markdown("---")
    c_dim, c_fer = st.columns(2)
    with c_dim:
        maj_dim = st.radio("Majoration Dimanche ?", ["Non", "Oui"])
        st.session_state.maj_dim = maj_dim
        if maj_dim == "Oui":
            st.session_state.montant_dim = st.text_input("Montant Dimanche :", value=st.session_state.get('montant_dim', '0'))
    with c_fer:
        maj_ferie = st.radio("Majoration Jours Fériés ?", ["Non", "Oui"])
        st.session_state.maj_ferie = maj_ferie
        if maj_ferie == "Oui":
            st.session_state.lesquels_ferie = st.text_input("Quels jours ?", value=st.session_state.get('lesquels_ferie', ''))
            st.session_state.montant_ferie = st.text_input("Montant Fériés :", value=st.session_state.get('montant_ferie', '0'))
    
    col_b, col_n = st.columns(2)
    with col_b: 
        if st.button("RETOUR", key="back5"): go_to(4); st.rerun()
    with col_n: 
        if st.button("SUIVANT", key="next5"):
            if dispos.strip():
                st.session_state.dispos = dispos
                go_to(6); st.rerun()
            else: st.error("Veuillez renseigner vos disponibilités.")

# 6. SECTEUR
elif st.session_state.step == 6:
    render_header("6. Secteur")
    v_base = st.selectbox("Ville de départ", sorted(df_v['affichage'].unique()) if not df_v.empty else [])
    rayon = st.slider("Rayon d'action (km)", 0, 150, 30)
    
    if st.button("CALCULER LES VILLES"):
        sel = df_v[df_v['affichage'] == v_base].iloc[0]
        lat1, lon1 = float(sel['latitude']), float(sel['longitude'])
        df_v['d'] = df_v.apply(lambda r: geodesic((lat1, lon1), (r['latitude'], r['longitude'])).km, axis=1)
        st.session_state.villes_trouvees = df_v[df_v['d'] <= rayon]['affichage'].tolist()

    if st.session_state.get('villes_trouvees'):
        st.write("Décochez les villes où vous n'intervenez pas :")
        v_finales = []
        st.markdown('<div class="city-scroll">', unsafe_allow_html=True)
        for v in st.session_state.villes_trouvees:
            if st.checkbox(v, value=True, key=f"v_{v}"): v_finales.append(v)
        st.markdown('</div>', unsafe_allow_html=True)
        st.session_state.villes_finales_list = v_finales

    st.session_state.villes_sup = st.text_area("Villes manuelles :", value=st.session_state.get('villes_sup', ''))
    
    col_b, col_n = st.columns(2)
    with col_b: 
        if st.button("RETOUR", key="back6"): go_to(5); st.rerun()
    with col_n: 
        if st.button("FINALISER", key="next6"):
            if st.session_state.get('villes_finales_list'): go_to(7); st.rerun()
            else: st.error("Sélectionnez au moins une ville.")

# 7. FINALISATION
elif st.session_state.step == 7:
    render_header("7. Finalisation")
    notes = st.text_area("Avez-vous d'autres informations à nous communiquer ?", value=st.session_state.get('notes', ''))
    
    def submit():
        f = st.session_state.get('file_bytes')
        content = base64.b64encode(f).decode() if f else ""
        payload = {
            "identite": {"nom": st.session_state.get('nom'), "prenom": st.session_state.get('prenom'), "siret": st.session_state.get('siret'), "statut": st.session_state.get('statut')},
            "contact": {"tel": st.session_state.get('tel1'), "email": st.session_state.get('email1')},
            "disponibilites": st.session_state.get('dispos'),
            "secteur": {"villes_selectionnees": st.session_state.get('villes_finales_list', []), "villes_sup": st.session_state.get('villes_sup')},
            "notes": notes, "attestation": content
        }
        try:
            r = requests.post("https://hub.cardin.cloud/webhook/Miseàjourdossierpresta", json=payload)
            if r.status_code == 200: go_to(8); st.rerun()
        except: st.error("Erreur de transmission.")

    col_b, col_n = st.columns(2)
    with col_b: 
        if st.button("RETOUR", key="back7"): go_to(6); st.rerun()
    with col_n: 
        if st.button("TRANSMETTRE", key="next7"): submit()

# 8. MERCI
elif st.session_state.step == 8:
    render_header("Merci !")
    st.balloons()
    st.write("Votre dossier a été transmis avec succès.")
    if st.button("RETOUR À L'ACCUEIL"): st.session_state.clear(); st.rerun()