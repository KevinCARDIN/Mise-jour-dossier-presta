import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import requests
import base64

# --- CONFIGURATION VISUELLE ---
st.set_page_config(page_title="LetaHost - Partenaires", layout="centered")

# Fonction pour encoder ton image locale en fond d'écran
def set_bg_local(main_bg_img):
    try:
        with open(main_bg_img, "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        page_bg_img = f'''
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-attachment: fixed;
        }}
        /* Style de la carte centrale blanche/transparente */
        [data-testid="stVerticalBlock"] > div:has(div.stButton) {{
            background-color: rgba(255, 255, 255, 0.08);
            padding: 50px;
            border-radius: 20px;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
        }}
        /* Boutons Dorés LetaHost */
        .stButton>button {{
            width: 100%;
            background-color: #D4AF37 !important;
            color: black !important;
            font-weight: bold;
            border: none;
            padding: 0.6rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        /* Textes en blanc */
        h1, h2, h3, p, label {{ color: white !important; }}
        .stTextInput>div>div>input {{ background-color: rgba(255,255,255,0.1); color: white; }}
        </style>
        '''
        st.markdown(page_bg_img, unsafe_allow_html=True)
    except:
        st.warning("⚠️ Image 'fond.png' non trouvée. Place-la dans le dossier du script.")

# REMPLACE "fond.png" par le nom exact de ton fichier image
set_bg_local("fond.png")

# --- GESTION DES ÉTAPES ---
if 'step' not in st.session_state:
    st.session_state.step = 1

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

df_villes = load_data()

# --- RENDU PAR QUESTION ---

# ÉTAPE 1 : IDENTITÉ
if st.session_state.step == 1:
    st.title("Questionnaire Partenaire")
    st.subheader("1. Qui êtes-vous ?")
    st.session_state['nom'] = st.text_input("NOM *", value=st.session_state.get('nom', ''))
    st.session_state['prenom'] = st.text_input("Prénom *", value=st.session_state.get('prenom', ''))
    st.session_state['siret'] = st.text_input("Numéro SIRET *", value=st.session_state.get('siret', ''))
    if st.button("Suivant →"): change_step(1)

# ÉTAPE 2 : STATUT ET SOCIÉTÉ
elif st.session_state.step == 2:
    st.subheader("Votre Structure")
    st.session_state['societe'] = st.text_input("Nom de société (si applicable)", value=st.session_state.get('societe', ''))
    st.session_state['statut'] = st.selectbox("Statut de votre société *", 
        ["Auto/Micro-Entrepreneur (EI)", "EURL", "SARL", "SA", "SAS", "SASU", "Autre"])
    col1, col2 = st.columns(2)
    with col1: st.button("← Retour", on_click=change_step, args=(-1,))
    with col2: st.button("Suivant →", on_click=change_step, args=(1,))

# ÉTAPE 3 : ATTESTATION VIGILANCE
elif st.session_state.step == 3:
    st.subheader("Attestation de Vigilance")
    st.markdown("""
    Pour récupérer votre attestation :
    1. Rendez-vous sur **urssaf.fr**.
    2. Allez dans **Mes attestations** → **Attestation de vigilance**.
    """)
    st.session_state['file_vigilance'] = st.file_uploader("Téléchargez le document PDF *", type=["pdf"])
    col1, col2 = st.columns(2)
    with col1: st.button("← Retour", on_click=change_step, args=(-1,))
    with col2: st.button("Suivant →", on_click=change_step, args=(1,))

# ÉTAPE 4 : CONTACTS
elif st.session_state.step == 4:
    st.subheader("Vos Coordonnées")
    st.session_state['email'] = st.text_input("Email principal *", value=st.session_state.get('email', ''))
    st.session_state['tel'] = st.text_input("Téléphone principal *", value=st.session_state.get('tel', ''))
    col1, col2 = st.columns(2)
    with col1: st.button("← Retour", on_click=change_step, args=(-1,))
    with col2: st.button("Suivant →", on_click=change_step, args=(1,))

# ÉTAPE 5 : DISPONIBILITÉS
elif st.session_state.step == 5:
    st.subheader("Vos Disponibilités")
    st.session_state['dispos'] = st.text_area("Quels sont vos jours et plages horaires ?", value=st.session_state.get('dispos', ''))
    col1, col2 = st.columns(2)
    with col1: st.button("← Retour", on_click=change_step, args=(-1,))
    with col2: st.button("Suivant →", on_click=change_step, args=(1,))

# ÉTAPE 6 : SECTEUR D'INTERVENTION
elif st.session_state.step == 6:
    st.subheader("Secteur d'intervention")
    villes_dispo = sorted(df_villes['affichage'].unique())
    ville_base = st.selectbox("Ville de départ *", villes_dispo)
    rayon = st.slider("Rayon (km) *", 0, 200, 20)
    
    if st.button("Calculer le secteur"):
        ville_sel = df_villes[df_villes['affichage'] == ville_base].iloc[0]
        lat_dep, lon_dep = float(ville_sel['latitude']), float(ville_sel['longitude'])
        def calc_dist(row):
            return geodesic((lat_dep, lon_dep), (row['latitude'], row['longitude'])).km
        df_villes['distance'] = df_villes.apply(calc_dist, axis=1)
        villes_proches = df_villes[df_villes['distance'] <= rayon].sort_values('distance')
        st.session_state['villes_trouvees'] = villes_proches['affichage'].head(50).tolist()
    
    if st.session_state.get('villes_trouvees'):
        st.write("Cochez vos villes :")
        selection = []
        for v in st.session_state['villes_trouvees']:
            if st.checkbox(v, value=True, key=f"v_{v}"):
                selection.append(v)
        st.session_state['villes_finales'] = selection

    col1, col2 = st.columns(2)
    with col1: st.button("← Retour", on_click=change_step, args=(-1,))
    with col2: st.button("Finaliser →", on_click=change_step, args=(1,))

# ÉTAPE 7 : SOUMISSION
elif st.session_state.step == 7:
    st.subheader("Soumission finale")
    st.write("Vérifiez vos informations avant l'envoi.")
    if st.button("ENVOYER MON DOSSIER"):
        # Logique requests.post ici avec toutes les données de st.session_state
        st.balloons()
        st.success("Dossier envoyé avec succès !")
    st.button("← Retour", on_click=change_step, args=(-1,))