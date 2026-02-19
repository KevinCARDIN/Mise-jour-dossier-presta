import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import requests

# Configuration du style
st.set_page_config(page_title="Mise à jour Dossier Prestataire", layout="wide")

st.title("Mise à jour dossier prestataire et tableau des codes postaux")
st.write("Merci de bien vouloir nous transmettre les informations suivantes :")

# --- SECTION 1 : INFORMATIONS GÉNÉRALES ---
st.header("1. Informations Générales")

col_id1, col_id2 = st.columns(2)
with col_id1:
    nom = st.text_input("NOM")
    prenom = st.text_input("Prénom")
with col_id2:
    nom_societe = st.text_input("Nom de société (si applicable)")
    statut = st.selectbox("Quel est le statut de votre société ?", 
        ["Auto/Micro-Entrepreneur (EI)", "EURL", "SARL", "SA", "SAS", "SASU", "Autre"])
    if statut == "Autre":
        statut_autre = st.text_input("Précisez votre statut :")

col_contact1, col_contact2 = st.columns(2)
with col_contact1:
    tel1 = st.text_input("Téléphone principal", placeholder="+33...")
    email1 = st.text_input("Email principal")
with col_contact2:
    email2 = st.text_input("Email secondaire (si applicable)")

# --- SECTION 2 : ORGANISATION ET REMPLAÇANT ---
st.header("2. Organisation et Remplaçant")

org = st.radio("Organisation : Travaillez-vous seul ou à plusieurs ?", 
    ["Seul, sans remplaçant même ponctuel", 
     "Seul, avec un remplaçant ponctuel", 
     "Avec 1 ou 2 collaborateurs", 
     "En équipe", 
     "Autre"], index=0)

noms_collab = ""
nb_equipe = 0
situation_particuliere = ""

if org == "Seul, avec un remplaçant ponctuel":
    noms_collab = st.text_input("Précisez le nom de votre collaborateur :")
elif org == "Avec 1 ou 2 collaborateurs":
    noms_collab = st.text_input("Précisez le(s) nom(s) de votre/vos collaborateur(s) :")
elif org == "En équipe":
    nb_equipe = st.number_input("Précisez le nombre de personnes dans votre équipe :", min_value=1)
elif org == "Autre":
    situation_particuliere = st.text_area("Précisez votre situation :")

if org != "Seul, sans remplaçant même ponctuel":
    st.subheader("Coordonnées du/des remplaçant(s)")
    col_remp1, col_remp2 = st.columns(2)
    with col_remp1:
        tels_remp = st.text_area("Numéros de téléphone (un par ligne)")
    with col_remp2:
        emails_remp = st.text_area("Adresses email (une par ligne)")
else:
    st.info("Vous avez indiqué ne pas travailler avec un remplaçant.")

# --- SECTION 3 : DISPONIBILITÉS ---
st.header("3. Disponibilités")
dispos = st.text_area("Quels sont vos jours et plages horaires de disponibilité ?")

col_maj1, col_maj2 = st.columns(2)
with col_maj1:
    maj_dim = st.radio("Appliquez-vous une majoration sur les dimanches ?", ["Non", "Oui"])
    montant_dim = st.text_input("Précisez le montant (dimanche) :") if maj_dim == "Oui" else "0"
with col_maj2:
    maj_ferie = st.radio("Appliquez-vous une majoration sur les jours fériés ?", ["Non", "Oui"])
    if maj_ferie == "Oui":
        lesquels_ferie = st.text_input("Précisez quels jours fériés :")
        montant_ferie = st.text_input("Précisez le montant (fériés) :")

# --- SECTION 4 : SECTEUR D'INTERVENTION ---
st.header("4. Secteur d'intervention")

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
    lat_dep, lon_dep = float(ville_selectionnee['latitude']), float(ville_selectionnee['longitude'])

    rayon = st.slider("Dans quel rayon intervenez-vous (en kilomètres) ?", 0, 200, 20)

    def calc_dist(row):
        return geodesic((lat_dep, lon_dep), (row['latitude'], row['longitude'])).km

    if st.button("Calculer les villes dans le secteur"):
        with st.spinner('Recherche en cours...'):
            df['distance'] = df.apply(calc_dist, axis=1)
            villes_proches = df[df['distance'] <= rayon].sort_values('distance')
            st.session_state['villes_trouvees'] = villes_proches['nom'].head(100).tolist()

    if st.session_state['villes_trouvees']:
        st.success(f"✅ {len(st.session_state['villes_trouvees'])} villes trouvées. Confirmez votre intervention :")
        selection_utilisateur = []
        for v in st.session_state['villes_trouvees']:
            if st.checkbox(v, value=True, key=f"cb_{v}"):
                selection_utilisateur.append(v)
        st.session_state['villes_finales'] = selection_utilisateur

    infos_sup_check = st.radio("Avez-vous d'autres villes sur lesquelles vous intervenez ?", ["Non", "Oui"])
    infos_sup = st.text_area("Précisez les villes supplémentaires :") if infos_sup_check == "Oui" else ""

except Exception as e:
    st.error(f"Erreur technique : {e}")

# --- SECTION 5 : INFORMATIONS COMPLÉMENTAIRES ---
st.header("5. Informations complémentaires")
info_libre = st.text_area("Avez-vous d'autres éléments à nous communiquer sur votre activité ?")

# --- SOUMISSION ---
if st.button("Soumettre la mise à jour du dossier"):
    detail_org = org
    if org == "Autre": detail_org = f"Autre : {situation_particuliere}"
    elif nb_equipe > 0: detail_org = f"Équipe de {nb_equipe} personnes"
    elif noms_collab: detail_org = f"{org} ({noms_collab})"

    payload = {
        "identite": {"nom": nom, "prenom": prenom, "societe": nom_societe},
        "statut": statut if statut != "Autre" else statut_autre,
        "organisation": detail_org,
        "contact_principal": {"email": email1, "tel": tel1, "email_sec": email2},
        "contacts_remplacants": {
            "telephones": tels_remp if 'tels_remp' in locals() else "N/A",
            "emails": emails_remp if 'emails_remp' in locals() else "N/A"
        },
        "disponibilites": dispos,
        "majorations": {
            "dimanche": {"active": maj_dim, "montant": montant_dim},
            "feries": {"active": maj_ferie, "jours": lesquels_ferie if maj_ferie == "Oui" else "", "montant": montant_ferie if maj_ferie == "Oui" else "0"}
        },
        "secteur": {
            "ville_depart": ville_base,
            "rayon": rayon,
            "villes_selectionnees": st.session_state.get('villes_finales', []),
            "villes_sup": infos_sup
        },
        "notes": info_libre
    }
    
    webhook_url = "https://hub.cardin.cloud/webhook/Miseàjourdossierpresta"
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            st.balloons()
            st.success("Dossier envoyé avec succès !")
        else:
            st.error(f"Erreur {response.status_code} lors de l'envoi.")
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")