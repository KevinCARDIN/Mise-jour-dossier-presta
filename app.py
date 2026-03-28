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
        /* VISIBILITÉ : Texte noir sur fond blanc dans les champs */
        .stTextInput>div>div>input, .stTextArea>div>textarea, .stSelectbox>div>div, .stNumberInput>div>div>input {{ 
            background-color: white !important; 
            color: black !important; 
            font-size: 16px !important;
            border-radius: 5px !important;
        }}
        /* BOUTONS JAUNES CENTRÉS : Forçage du centrage */
        div.stButton > button {{
            background-color: #f1c40f !important;
            color: #000000 !important;
            border: none !important;
            font-weight: bold !important;
            padding: 12px 30px !important;
            border-radius: 8px !important;
            display: block;
            margin: 0 auto !important; /* Centrage horizontal */
            width: 250px !important;
            text-transform: uppercase;
        }}
        /* Centrage global des textes */
        h1, h2, h3, p, label, .stMarkdown {{ color: white !important; text-align: center !important; }}
        
        /* Centrage des boutons radio */
        div.row-widget.stRadio > div {{ display: flex; justify-content: center; flex-wrap: wrap; gap: 15px; color: white !important; }}
        
        /* Ajustement pour les colonnes de boutons (Retour/Suivant) */
        [data-testid="column"] {{
            display: flex;
            justify-content: center;
        }}
        </style>
        '''
        st.markdown(page_bg_img, unsafe_allow_html=True)
    except:
        st.warning("⚠️ Image 'fond.png' non trouvée.")

set_bg_local("fond.png")

# --- INITIALISATION ---
fields = {
    'step': 0, 'nom': '', 'prenom': '', 'siret': '', 'societe': '', 'statut': 'Auto/Micro-Entrepreneur (EI)',
    'tel1': '', 'tel2': '', 'email1': '', 'email2': '', 'org_type': 'Seul, sans remplaçant même ponctuel',
    'details_org': '', 'tels_remp': 'N/A', 'emails_remp': 'N/A', 'dispos': '', 'maj_dim': 'Non',
    'montant_dim': '0', 'maj_ferie': 'Non', 'lesquels_ferie': '', 'montant_ferie': '0',
    'ville_base': 'Aast', 'rayon': 20, 'villes_trouvees': [], 'villes_finales_list': [],
    'villes_sup': '', 'info_libre': ''
}
for key, val in fields.items():
    if key not in st.session_state: st.session_state[key] = val

def change_step(direction):
    st.session_state.step += direction

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

# --- AFFICHAGE DU LOGO CENTRÉ ---
col_logo_1, col_logo_2, col_logo_3 = st.columns([1, 2, 1])
with col_logo_2:
    try:
        st.image("letahost_logo.png", use_container_width=True)
    except:
        st.title("LETAHOST")

# --- ÉTAPES ---

# ÉTAPE 0 : ACCUEIL
if st.session_state.step == 0:
    st.header("Mise à jour Dossier Prestataire")
    st.write("Bienvenue sur votre espace de mise à jour Letahost.")
    st.write("Ce questionnaire rapide (7 étapes) nous permet de réactualiser vos informations.")
    st.button("Commencer le questionnaire", on_click=change_step, args=(1,))

# ÉTAPE 1 : IDENTITÉ
elif st.session_state.step == 1:
    st.header("1. Vos informations personnelles")
    st.session_state.nom = st.text_input("NOM *", value=st.session_state.nom)
    st.session_state.prenom = st.text_input("Prénom *", value=st.session_state.prenom)
    st.session_state.siret = st.text_input("Numéro SIRET *", value=st.session_state.siret)
    if st.button("Continuer"):
        if st.session_state.nom and st.session_state.prenom and st.session_state.siret: change_step(1)
        else: st.error("Champs obligatoires (*)")

# ÉTAPE 2 : CONTACTS & STATUT
elif st.session_state.step == 2:
    st.header("2. Coordonnées & Structure")
    st.session_state.societe = st.text_input("Nom de société (si applicable)", value=st.session_state.societe)
    st.session_state.statut = st.selectbox("Statut de votre société *", ["Auto/Micro-Entrepreneur (EI)", "EURL", "SARL", "SA", "SAS", "SASU", "Autre"], index=0)
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.session_state.tel1 = st.text_input("Téléphone principal *", value=st.session_state.tel1)
        st.session_state.tel2 = st.text_input("Téléphone secondaire", value=st.session_state.tel2)
    with col_c2:
        st.session_state.email1 = st.text_input("Email principal *", value=st.session_state.email1)
        st.session_state.email2 = st.text_input("Email secondaire", value=st.session_state.email2)
    
    col_b1, col_b2 = st.columns(2)
    with col_b1: st.button("Retour", on_click=change_step, args=(-1,))
    with col_b2:
        if st.button("Suivant"):
            if st.session_state.tel1 and st.session_state.email1: change_step(1)
            else: st.error("Tél et Email obligatoires.")

# ÉTAPE 3 : ATTESTATION
elif st.session_state.step == 3:
    st.header("3. Attestation de vigilance")
    st.markdown("Récupérez votre attestation sur **urssaf.fr**.")
    file = st.file_uploader("Téléchargez le PDF *", type=["pdf"])
    if file: st.session_state['file_bytes'] = file.read()
    col_b1, col_b2 = st.columns(2)
    with col_b1: st.button("Retour", on_click=change_step, args=(-1,))
    with col_b2:
        if st.button("Suivant"):
            if 'file_bytes' in st.session_state: change_step(1)
            else: st.error("L'attestation est obligatoire.")

# ÉTAPE 4 : ORGANISATION
elif st.session_state.step == 4:
    st.header("4. Organisation")
    st.session_state.org_type = st.radio("Travaillez-vous seul ou à plusieurs ? *", ["Seul, sans remplaçant même ponctuel", "Seul, avec un remplaçant ponctuel", "Avec 1 ou 2 collaborateurs", "En équipe", "Autre"], index=0)
    if "collaborateurs" in st.session_state.org_type or "remplaçant" in st.session_state.org_type:
        st.session_state.details_org = st.text_input("Nom(s) du/des collaborateur(s) :", value=st.session_state.details_org)
    elif st.session_state.org_type == "En équipe":
        st.session_state.details_org = st.number_input("Nombre de personnes :", min_value=1, value=int(st.session_state.details_org) if st.session_state.details_org else 1)
    
    if st.session_state.org_type != "Seul, sans remplaçant même ponctuel":
        st.session_state.tels_remp = st.text_area("Téléphones remplaçants :", value=st.session_state.tels_remp)
        st.session_state.emails_remp = st.text_area("Emails remplaçants :", value=st.session_state.emails_remp)
    
    col_b1, col_b2 = st.columns(2)
    with col_b1: st.button("Retour", on_click=change_step, args=(-1,))
    with col_b2: st.button("Suivant", on_click=change_step, args=(1,))

# ÉTAPE 5 : DISPOS & TARIFS
elif st.session_state.step == 5:
    st.header("5. Disponibilités & Tarifs")
    st.session_state.dispos = st.text_area("Quels sont vos jours et plages horaires de disponibilité ? *", value=st.session_state.dispos)
    col_a, col_b = st.columns(2)
    with col_a:
        st.session_state.maj_dim = st.radio("Majoration Dimanche ?", ["Non", "Oui"], index=0)
        if st.session_state.maj_dim == "Oui":
            st.session_state.montant_dim = st.text_input("Montant Dimanche :", value=st.session_state.montant_dim)
    with col_b:
        st.session_state.maj_ferie = st.radio("Majoration Jours Fériés ?", ["Non", "Oui"], index=0)
        if st.session_state.maj_ferie == "Oui":
            st.session_state.lesquels_ferie = st.text_input("Quels jours ?", value=st.session_state.lesquels_ferie)
            st.session_state.montant_ferie = st.text_input("Montant Fériés :", value=st.session_state.montant_ferie)
    
    col_b1, col_b2 = st.columns(2)
    with col_b1: st.button("Retour", on_click=change_step, args=(-1,))
    with col_b2:
        if st.button("Suivant"):
            if st.session_state.dispos: change_step(1)
            else: st.error("Disponibilités obligatoires.")

# ÉTAPE 6 : SECTEUR
elif st.session_state.step == 6:
    st.header("6. Secteur d'intervention")
    st.session_state.ville_base = st.selectbox("Ville de départ *", sorted(df_v['affichage'].unique()))
    st.session_state.rayon = st.slider("Rayon (km) *", 0, 200, value=int(st.session_state.rayon))
    if st.button("Calculer les villes"):
        v_sel = df_v[df_v['affichage'] == st.session_state.ville_base].iloc[0]
        def dist(r): return geodesic((v_sel['latitude'], v_sel['longitude']), (r['latitude'], r['longitude'])).km
        df_v['d'] = df_v.apply(dist, axis=1)
        st.session_state.villes_trouvees = df_v[df_v['d'] <= st.session_state.rayon].sort_values('d')['affichage'].head(100).tolist()
    if st.session_state.villes_trouvees:
        v_l = []
        for v in st.session_state.villes_trouvees:
            if st.checkbox(v, value=True, key=f"v_{v}"): v_l.append(v)
        st.session_state.villes_finales_list = v_l
    st.session_state.villes_sup = st.text_area("Villes supplémentaires :", value=st.session_state.villes_sup)
    col_b1, col_b2 = st.columns(2)
    with col_b1: st.button("Retour", on_click=change_step, args=(-1,))
    with col_b2:
        if st.button("Dernière étape"):
            if st.session_state.villes_finales_list: change_step(1)
            else: st.error("Sélectionnez au moins une ville.")

# ÉTAPE 7 : FINALISATION
elif st.session_state.step == 7:
    st.header("7. Finalisation")
    st.session_state.info_libre = st.text_area("Autres éléments :", value=st.session_state.info_libre)
    col_b1, col_b2 = st.columns(2)
    with col_b1: st.button("Retour", on_click=change_step, args=(-1,))
    with col_b2:
        if st.button("TRANSMETTRE MON DOSSIER"):
            content = base64.b64encode(st.session_state.file_bytes).decode() if 'file_bytes' in st.session_state else ""
            payload = {
                "identite": {"nom": st.session_state.nom, "prenom": st.session_state.prenom, "siret": st.session_state.siret, "societe": st.session_state.societe, "statut": st.session_state.statut},
                "contact": {"tel1": st.session_state.tel1, "tel2": st.session_state.tel2, "email1": st.session_state.email1, "email2": st.session_state.email2},
                "disponibilites": st.session_state.dispos,
                "organisation": {"type": st.session_state.org_type, "details": st.session_state.details_org},
                "tarifs": {"maj_dim": st.session_state.maj_dim, "montant_dim": st.session_state.montant_dim, "maj_fer": st.session_state.maj_ferie, "montant_fer": st.session_state.montant_ferie},
                "secteur": {"base": st.session_state.ville_base, "villes": st.session_state.villes_finales_list, "sup": st.session_state.villes_sup},
                "attestation": content, "notes": st.session_state.info_libre
            }
            try:
                r = requests.post("https://hub.cardin.cloud/webhook/Miseàjourdossierpresta", json=payload)
                if r.status_code == 200: st.balloons(); st.success("Dossier envoyé !")
                else: st.error("Erreur d'envoi.")
            except: st.error("Erreur connexion.")