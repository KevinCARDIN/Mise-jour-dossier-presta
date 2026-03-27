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
            background-image: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.75)), url("data:image/png;base64,{bin_str}");
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
            width: 200px !important;
        }}
        /* Suppression des encadrés et style des textes */
        h1, h2, h3, p, label {{ color: white !important; text-align: center !important; }}
        .stTextInput>div>div>input, .stTextArea>div>textarea {{ 
            background-color: rgba(255,255,255,0.1) !important; 
            color: white !important; 
            border: 1px solid rgba(255,255,255,0.2) !important;
        }}
        /* Centrage des radio et selectbox */
        div.row-widget.stRadio > div, div.row-widget.stSelectbox > div {{
            display: flex; justify-content: center;
        }}
        </style>
        '''
        st.markdown(page_bg_img, unsafe_allow_html=True)
    except:
        st.warning("⚠️ Image 'fond.jpg' non trouvée.")

set_bg_local("fond.jpg")

# --- INITIALISATION DE L'ÉTAT ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'villes_trouvees' not in st.session_state:
    st.session_state['villes_trouvees'] = []

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

# ÉTAPE 1 : IDENTITÉ (OBLIGATOIRE)
if st.session_state.step == 1:
    st.header("1. Vos informations personnelles")
    st.session_state['nom'] = st.text_input("NOM *", value=st.session_state.get('nom', ''))
    st.session_state['prenom'] = st.text_input("Prénom *", value=st.session_state.get('prenom', ''))
    st.session_state['siret'] = st.text_input("Numéro SIRET *", value=st.session_state.get('siret', ''))
    
    if st.button("Continuer"):
        if st.session_state['nom'] and st.session_state['prenom'] and st.session_state['siret']:
            change_step(1)
        else:
            st.error("Veuillez remplir tous les champs marqués d'une *")

# ÉTAPE 2 : SOCIÉTÉ & CONTACT (TÉL OBLIGATOIRE)
elif st.session_state.step == 2:
    st.header("2. Coordonnées & Structure")
    st.session_state['societe'] = st.text_input("Nom de société (si applicable)", value=st.session_state.get('societe', ''))
    st.session_state['statut'] = st.selectbox("Statut de votre société *", ["Auto/Micro-Entrepreneur (EI)", "EURL", "SARL", "SA", "SAS", "SASU", "Autre"])
    st.session_state['tel1'] = st.text_input("Téléphone principal *", value=st.session_state.get('tel1', ''))
    st.session_state['email1'] = st.text_input("Email principal *", value=st.session_state.get('email1', ''))
    
    c1, c2 = st.columns(2)
    with c1: st.button("Retour", on_click=change_step, args=(-1,))
    with c2: 
        if st.button("Suivant"):
            if st.session_state['tel1'] and st.session_state['email1']: change_step(1)
            else: st.error("Le téléphone et l'email sont obligatoires.")

# ÉTAPE 3 : ATTESTATION VIGILANCE (DÉTAILS COMPLETS)
elif st.session_state.step == 3:
    st.header("3. Attestation de vigilance")
    st.markdown("""
    Pour récupérer votre attestation de vigilance, rendez-vous sur le site officiel : 
    **[urssaf.fr](https://www.urssaf.fr)** (ou autoentrepreneur.urssaf.fr).
    1. Cliquer sur **« Mon compte »** et se connecter (SIRET + mot de passe).
    2. Aller dans **Mes attestations** → **Attestation de vigilance**.
    3. Téléchargez le PDF.
    *(Si créé il y a < 90 jours, téléchargez l'attestation provisoire)*
    """)
    st.session_state['file_vigilance'] = st.file_uploader("Quel est votre attestation de vigilance ? *", type=["pdf"])
    
    c1, c2 = st.columns(2)
    with c1: st.button("Retour", on_click=change_step, args=(-1,))
    with c2:
        if st.button("Suivant"):
            if st.session_state['file_vigilance']: change_step(1)
            else: st.error("L'attestation est obligatoire.")

# ÉTAPE 4 : ORGANISATION (LOGIQUE CONDITIONNELLE)
elif st.session_state.step == 4:
    st.header("4. Organisation")
    org = st.radio("Travaillez-vous seul ou à plusieurs ? *", ["Seul, sans remplaçant", "Seul, avec un remplaçant ponctuel", "Avec 1 ou 2 collaborateurs", "En équipe", "Autre"])
    st.session_state['org'] = org
    
    if org == "Seul, avec un remplaçant ponctuel" or org == "Avec 1 ou 2 collaborateurs":
        st.session_state['collab'] = st.text_input("Précisez le(s) nom(s) :")
    elif org == "En équipe":
        st.session_state['nb_equipe'] = st.number_input("Nombre de personnes :", min_value=1)
    
    if org != "Seul, sans remplaçant":
        st.session_state['tels_remp'] = st.text_area("Téléphones remplaçants :")
        st.session_state['emails_remp'] = st.text_area("Emails remplaçants :")

    c1, c2 = st.columns(2)
    with c1: st.button("Retour", on_click=change_step, args=(-1,))
    with c2: st.button("Suivant", on_click=change_step, args=(1,))

# ÉTAPE 5 : DISPOS & TARIFS
elif st.session_state.step == 5:
    st.header("5. Disponibilités & Tarifs")
    st.session_state['dispos'] = st.text_area("Vos jours et plages horaires ? *")
    maj_dim = st.radio("Majoration Dimanche ?", ["Non", "Oui"])
    if maj_dim == "Oui": st.session_state['montant_dim'] = st.text_input("Montant dimanche :")
    
    c1, c2 = st.columns(2)
    with c1: st.button("Retour", on_click=change_step, args=(-1,))
    with c2: 
        if st.session_state['dispos']: change_step(1)
        else: st.error("Veuillez remplir vos disponibilités.")

# ÉTAPE 6 : SECTEUR (CALCUL & VILLES SUP)
elif st.session_state.step == 6:
    st.header("6. Secteur d'intervention")
    ville_base = st.selectbox("Ville de départ *", sorted(df_v['affichage'].unique()))
    rayon = st.slider("Rayon (km) *", 0, 200, 20)
    
    if st.button("Calculer les villes"):
        v_sel = df_v[df_v['affichage'] == ville_base].iloc[0]
        lat_d, lon_d = float(v_sel['latitude']), float(v_sel['longitude'])
        def dist(r): return geodesic((lat_d, lon_d), (r['latitude'], r['longitude'])).km
        df_v['d'] = df_v.apply(dist, axis=1)
        res = df_v[df_v['d'] <= rayon].sort_values('d')
        st.session_state['villes_trouvees'] = res['affichage'].head(100).tolist()
    
    if st.session_state.get('villes_trouvees'):
        selection = []
        for v in st.session_state['villes_trouvees']:
            if st.checkbox(v, value=True, key=v): selection.append(v)
        st.session_state['villes_finales'] = selection

    st.session_state['villes_sup'] = st.text_area("Villes supplémentaires :")

    c1, c2 = st.columns(2)
    with c1: st.button("Retour", on_click=change_step, args=(-1,))
    with c2: 
        if st.session_state.get('villes_finales'): change_step(1)
        else: st.error("Veuillez calculer et choisir vos villes.")

# ÉTAPE 7 : NOTES & ENVOI
elif st.session_state.step == 7:
    st.header("7. Finalisation")
    st.session_state['info_libre'] = st.text_area("Avez-vous d'autres éléments à nous communiquer ?")
    
    c1, c2 = st.columns(2)
    with c1: st.button("Retour", on_click=change_step, args=(-1,))
    with c2:
        if st.button("FINALISER"):
            # Encodage fichier
            content = base64.b64encode(st.session_state['file_vigilance'].read()).decode()
            payload = {
                "nom": st.session_state['nom'], "prenom": st.session_state['prenom'], "siret": st.session_state['siret'],
                "contact": {"email": st.session_state['email1'], "tel": st.session_state['tel1']},
                "secteur": {"base": ville_base, "selection": st.session_state['villes_finales'], "sup": st.session_state['villes_sup']},
                "attestation": content, "notes": st.session_state['info_libre']
            }
            # Appel Webhook (ajouter ton URL ici)
            st.balloons()
            st.success("Dossier envoyé !")