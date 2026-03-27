import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import requests
import base64

# --- CONFIGURATION VISUELLE ---
st.set_page_config(page_title="LetaHost - Partenaires", layout="centered")

def set_bg_local(main_bg_img):
    try:
        with open(main_bg_img, "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        page_bg_img = f'''
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-attachment: fixed;
        }}
        /* Boutons Jaunes Épurés et Centrés */
        div.stButton > button {{
            background-color: #f1c40f !important;
            color: #000000 !important;
            border: none !important;
            font-weight: bold !important;
            padding: 10px 30px !important;
            border-radius: 5px !important;
            display: block;
            margin: 0 auto;
            width: 250px !important;
        }}
        /* Style des textes et inputs */
        h1, h2, h3, p, label, .stMarkdown {{ color: white !important; text-align: center !important; }}
        .stTextInput>div>div>input, .stTextArea>div>textarea, .stSelectbox>div>div {{ 
            background-color: rgba(255,255,255,0.1) !important; 
            color: white !important; 
            border: 1px solid rgba(255,255,255,0.2) !important;
        }}
        /* Centrage des widgets */
        div.row-widget.stRadio > div {{ display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; }}
        div.stSelectbox {{ max-width: 500px; margin: 0 auto; }}
        </style>
        '''
        st.markdown(page_bg_img, unsafe_allow_html=True)
    except:
        st.warning("⚠️ Image 'fond.png' non trouvée.")

set_bg_local("fond.png")

# --- INITIALISATION DE L'ÉTAT ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'villes_trouvees' not in st.session_state: st.session_state['villes_trouvees'] = []
if 'villes_finales' not in st.session_state: st.session_state['villes_finales'] = []

def change_step(direction):
    st.session_state.step += direction

# --- CHARGEMENT DES DONNÉES ---
@st.cache_data
def load_data():
    df = pd.read_csv("villes_france.csv", usecols=['nom', 'latitude', 'longitude', 'code_postal'])
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df = df.dropna(subset=['latitude', 'longitude'])
    df['cp_clean'] = df['code_postal'].astype(str).apply(lambda x: x.split('.')[0].strip().zfill(5))
    df['affichage'] = df['nom'] + " (" + df['cp_clean'] + ")"
    return df

df_v = load_data()

# --- FORMULAIRE PAR ÉTAPES ---

# ÉTAPE 1 : IDENTITÉ
if st.session_state.step == 1:
    st.header("1. Vos informations personnelles")
    st.session_state['nom'] = st.text_input("NOM *", value=st.session_state.get('nom', ''))
    st.session_state['prenom'] = st.text_input("Prénom *", value=st.session_state.get('prenom', ''))
    st.session_state['siret'] = st.text_input("Numéro SIRET *", value=st.session_state.get('siret', ''))
    
    if st.button("Continuer"):
        if st.session_state['nom'] and st.session_state['prenom'] and st.session_state['siret']:
            change_step(1)
        else:
            st.error("Nom, Prénom et SIRET sont obligatoires.")

# ÉTAPE 2 : SOCIÉTÉ & CONTACT (AVEC SECONDAIRES)
elif st.session_state.step == 2:
    st.header("2. Coordonnées & Structure")
    st.session_state['societe'] = st.text_input("Nom de société (si applicable)", value=st.session_state.get('societe', ''))
    st.session_state['statut'] = st.selectbox("Statut de votre société *", ["Auto/Micro-Entrepreneur (EI)", "EURL", "SARL", "SA", "SAS", "SASU", "Autre"])
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state['tel1'] = st.text_input("Téléphone principal *", value=st.session_state.get('tel1', ''))
        st.session_state['tel2'] = st.text_input("Téléphone secondaire", value=st.session_state.get('tel2', ''))
    with col2:
        st.session_state['email1'] = st.text_input("Email principal *", value=st.session_state.get('email1', ''))
        st.session_state['email2'] = st.text_input("Email secondaire", value=st.session_state.get('email2', ''))
    
    c1, c2 = st.columns(2)
    with c1: st.button("Retour", on_click=change_step, args=(-1,))
    with c2: 
        if st.button("Suivant"):
            if st.session_state['tel1'] and st.session_state['email1']: change_step(1)
            else: st.error("Le téléphone et l'email principaux sont obligatoires.")

# ÉTAPE 3 : ATTESTATION VIGILANCE
elif st.session_state.step == 3:
    st.header("3. Attestation de vigilance")
    st.markdown("""
    Pour récupérer votre attestation de vigilance, rendez-vous sur le site officiel : 
    **[urssaf.fr](https://www.urssaf.fr)**
    1. Cliquer sur **« Mon compte »** et se connecter (SIRET + mot de passe).
    2. Aller dans **Mes attestations** → **Attestation de vigilance**.
    3. Téléchargez le PDF.
    """)
    st.session_state['file_vigilance'] = st.file_uploader("Téléchargez votre attestation *", type=["pdf"])
    
    c1, c2 = st.columns(2)
    with c1: st.button("Retour", on_click=change_step, args=(-1,))
    with c2:
        if st.button("Suivant"):
            if st.session_state.get('file_vigilance'): change_step(1)
            else: st.error("L'attestation est obligatoire.")

# ÉTAPE 4 : ORGANISATION
elif st.session_state.step == 4:
    st.header("4. Organisation")
    org = st.radio("Travaillez-vous seul ou à plusieurs ? *", ["Seul, sans remplaçant même ponctuel", "Seul, avec un remplaçant ponctuel", "Avec 1 ou 2 collaborateurs", "En équipe", "Autre"])
    st.session_state['org'] = org
    
    if "collaborateurs" in org or "remplaçant" in org:
        st.session_state['noms_collab'] = st.text_input("Nom(s) du/des collaborateur(s) :", value=st.session_state.get('noms_collab', ''))
    elif org == "En équipe":
        st.session_state['nb_equipe'] = st.number_input("Nombre de personnes :", min_value=1, value=st.session_state.get('nb_equipe', 1))
    elif org == "Autre":
        st.session_state['situation_particuliere'] = st.text_area("Précisez votre situation :", value=st.session_state.get('situation_particuliere', ''))

    if org != "Seul, sans remplaçant même ponctuel":
        st.subheader("Coordonnées du/des remplaçant(s)")
        st.session_state['tels_remp'] = st.text_area("Téléphones remplaçants :", value=st.session_state.get('tels_remp', ''))
        st.session_state['emails_remp'] = st.text_area("Emails remplaçants :", value=st.session_state.get('emails_remp', ''))

    c1, c2 = st.columns(2)
    with c1: st.button("Retour", on_click=change_step, args=(-1,))
    with c2: st.button("Suivant", on_click=change_step, args=(1,))

# ÉTAPE 5 : DISPOS & TARIFS
elif st.session_state.step == 5:
    st.header("5. Disponibilités & Tarifs")
    st.session_state['dispos'] = st.text_area("Vos jours et plages horaires de disponibilité ? *", value=st.session_state.get('dispos', ''))
    
    col_dim, col_ferie = st.columns(2)
    with col_dim:
        maj_dim = st.radio("Majoration Dimanche ?", ["Non", "Oui"], key="rd_dim")
        st.session_state['maj_dim'] = maj_dim
        if maj_dim == "Oui":
            st.session_state['montant_dim'] = st.text_input("Montant Dimanche :", value=st.session_state.get('montant_dim', '0'))
            
    with col_ferie:
        maj_ferie = st.radio("Majoration Jours Fériés ?", ["Non", "Oui"], key="rd_fer")
        st.session_state['maj_ferie'] = maj_ferie
        if maj_ferie == "Oui":
            st.session_state['lesquels_ferie'] = st.text_input("Quels jours ?", value=st.session_state.get('lesquels_ferie', ''))
            st.session_state['montant_ferie'] = st.text_input("Montant Fériés :", value=st.session_state.get('montant_ferie', '0'))

    c1, c2 = st.columns(2)
    with c1: st.button("Retour", on_click=change_step, args=(-1,))
    with c2: 
        if st.button("Suivant"):
            if st.session_state['dispos']: change_step(1)
            else: st.error("Les disponibilités sont obligatoires.")

# ÉTAPE 6 : SECTEUR
elif st.session_state.step == 6:
    st.header("6. Secteur d'intervention")
    v_base = st.selectbox("Ville de départ *", sorted(df_v['affichage'].unique()))
    st.session_state['ville_base'] = v_base
    rayon = st.slider("Rayon (km) *", 0, 200, 20)
    st.session_state['rayon'] = rayon
    
    if st.button("Calculer les villes"):
        v_sel = df_v[df_v['affichage'] == v_base].iloc[0]
        lat_d, lon_d = float(v_sel['latitude']), float(v_sel['longitude'])
        def dist(r): return geodesic((lat_d, lon_d), (r['latitude'], r['longitude'])).km
        df_v['d'] = df_v.apply(dist, axis=1)
        res = df_v[df_v['d'] <= rayon].sort_values('d')
        st.session_state['villes_trouvees'] = res['affichage'].head(100).tolist()
    
    if st.session_state.get('villes_trouvees'):
        selection = []
        for v in st.session_state['villes_trouvees']:
            if st.checkbox(v, value=True, key=v): selection.append(v)
        st.session_state['villes_finales']