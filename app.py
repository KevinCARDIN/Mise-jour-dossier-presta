import streamlit as st
import pandas as pd
from geopy.distance import geodesic

# Configuration du style
st.set_page_config(page_title="Mise à jour Dossier Prestataire", layout="wide")

st.title("Mise à jour dossier prestataire et tableau des codes postaux")
st.write("Merci de bien vouloir nous transmettre les informations suivantes :")

# --- SECTION 1 : INFORMATIONS GÉNÉRALES ---
st.header("1. Informations Générales")

statut = st.selectbox("Quel est le statut de votre société ?", 
    ["Auto/Micro-Entrepreneur (EI)", "EURL", "SARL", "SA", "SAS", "SASU", "Autre"])
if statut == "Autre":
    statut_autre = st.text_input("Précisez votre statut :")

org = st.radio("Travaillez-vous seul ou à plusieurs ?", 
    ["Seul, sans remplaçant même ponctuel", "Seul, avec un remplaçant ponctuel", "Avec 1 ou 2 collaborateurs", "En équipe", "Autre"])

if "remplaçant" in org or "collaborateur" in org:
    noms_collab = st.text_input("Précisez le(s) nom(s) de votre/vos collaborateur(s) :")
elif org == "En équipe":
    nb_equipe = st.number_input("Précisez le nombre de personnes dans votre équipe :", min_value=1)

col1, col2 = st.columns(2)
with col1:
    tel1 = st.text_input("Numéro de téléphone principal :", placeholder="+33...")
    email1 = st.text_input("Adresse email principale :")
with col2:
    tel2 = st.text_input("Numéro de téléphone supplémentaire (optionnel) :")
    email2 = st.text_input("Email supplémentaire (optionnel) :")

# --- SECTION 2 : DISPONIBILITÉS ---
st.header("2. Disponibilités")
dispos = st.text_area("Quels sont vos jours et plages horaires de disponibilité ?")

col_maj1, col_maj2 = st.columns(2)
with col_maj1:
    maj_dim = st.radio("Appliquez-vous une majoration sur les dimanches ?", ["Non", "Oui"])
    if maj_dim == "Oui":
        montant_dim = st.text_input("Précisez le montant (dimanche) :")
with col_maj2:
    maj_ferie = st.radio("Appliquez-vous une majoration sur les jours fériés ?", ["Non", "Oui"])
    if maj_ferie == "Oui":
        lesquels_ferie = st.text_input("Précisez quels jours fériés :")
        montant_ferie = st.text_input("Précisez le montant (fériés) :")

# --- SECTION 3 : SECTEUR D'INTERVENTION ---
st.header("3. Secteur d'intervention")

# Initialisation du session_state pour stocker les villes trouvées
if 'villes_trouvees' not in st.session_state:
    st.session_state['villes_trouvees'] = []

@st.cache_data
def load_data():
    df = pd.read_csv("villes_france.csv", usecols=['nom', 'latitude', 'longitude'])
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    return df.dropna(subset=['latitude', 'longitude'])

try:
    df = load_data()
    villes_disponibles = sorted(df['nom'].unique())
    ville_base = st.selectbox("Quel est votre ville de départ ?", villes_disponibles)
    
    ville_selectionnee = df[df['nom'] == ville_base].iloc[0]
    lat_dep = float(ville_selectionnee['latitude'])
    lon_dep = float(ville_selectionnee['longitude'])

    rayon = st.slider("Dans un rayon de (en kilomètres) :", 0, 200, 20)

    def calc_dist(row):
        return geodesic((lat_dep, lon_dep), (row['latitude'], row['longitude'])).km

    # Bouton de calcul
    if st.button("Calculer les villes dans le secteur"):
        with st.spinner('Recherche en cours...'):
            df['distance'] = df.apply(calc_dist, axis=1)
            villes_proches = df[df['distance'] <= rayon].sort_values('distance')
            # On stocke les noms dans le session_state pour qu'ils persistent
            st.session_state['villes_trouvees'] = villes_proches['nom'].head(100).tolist()

    # Affichage de la liste SI elle existe en mémoire (session_state)
    if st.session_state['villes_trouvees']:
        st.success(f"✅ {len(st.session_state['villes_trouvees'])} villes trouvées dans votre secteur, veuillez retirer les villes dans lesquelles vous n'intervenez pas")
        
        selection_utilisateur = []
        for v in st.session_state['villes_trouvees']:
            # On utilise une clé unique pour chaque checkbox basée sur le nom de la ville
            if st.checkbox(v, value=True, key=f"cb_{v}"):
                selection_utilisateur.append(v)
        
        # On met à jour la liste finale qui sera envoyée par le webhook
        st.session_state['villes_finales'] = selection_utilisateur

    infos_sup = st.text_area("Avez-vous d'autres villes à nous communiquer?")

except Exception as e:
    st.error(f"Détail technique de l'erreur : {e}")

import requests # Ajoutez cette ligne tout en haut du fichier

# ... (reste du code) ...

if st.button("Soumettre la mise à jour du dossier"):
    # On prépare le paquet de données
    payload = {
        "statut": statut,
        "organisation": org,
        "email": email1,
        "telephone": tel1,
        "villes_selectionnees": st.session_state.get('villes_finales', [])
    }
    
    # URL de votre Webhook n8n (à remplacer par la vôtre)
    webhook_url = "https://hub.cardin.cloud/webhook/Miseàjourdossierpresta"
    
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            st.balloons()
            st.success("Dossier envoyé avec succès ! Merci de votre collaboration.")
        else:
            st.error("Erreur lors de l'envoi. Veuillez réessayer.")
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")