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
            background-image: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-attachment: fixed;
        }}
        div.stButton > button {{
            background-color: #f1c40f !important;
            color: #000000 !important;
            border: none !important;
            font-weight: bold !important;
            padding: 10px 30px !important;
            border-radius: 5px !important;
            display: block;
            margin: 20px auto;
            width: 250px !important;
        }}
        h1, h2, h3, p, label, .stMarkdown {{ color: white !important; text-align: center !important; }}
        .stTextInput>div>div>input, .stTextArea>div>textarea, .stSelectbox>div>div {{ 
            background-color: rgba(255,255,255,0.1) !important; 
            color: white !important; 
            border: 1px solid rgba(255,255,255,0.2) !important;
        }}
        div.row-widget.stRadio > div {{ display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; }}
        </style>
        '''
        st.markdown(page_bg_img, unsafe_allow_html=True)
    except:
        st.warning("⚠️ Image 'fond.png' non trouvée.")

set_bg_local("fond.png")

# --- INITIALISATION ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'villes_trouvees' not in st.session_state: st.session_state.villes_trouvees = []

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

# --- ÉTAPES ---

# 1. IDENTITÉ
if st.session_state.step == 1:
    st.header("1. Vos informations personnelles")
    st.text_input("NOM *", key="nom")
    st.text_input("Prénom *", key="prenom")
    st.text_input("Numéro SIRET *", key="siret")
    if st.button("Continuer"):
        if st.session_state.nom and st.session_state.prenom and st.session_state.siret: change_step(1)
        else: st.error("Champs obligatoires manquants.")

# 2. CONTACTS & STATUT
elif st.session_state.step == 2:
    st.header("2. Coordonnées & Structure")
    st.text_input("Nom de société (si applicable)", key="societe")
    st.selectbox("Statut de votre société *", ["Auto/Micro-Entrepreneur (EI)", "EURL", "SARL", "SA", "SAS", "SASU", "Autre"], key="statut")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Téléphone principal *", key="tel1")
        st.text_input("Téléphone secondaire", key="tel2")
    with col2:
        st.text_input("Email principal *", key="email1")
        st.text_input("Email secondaire", key="email2")
    
    c1, c2 = st.columns(2)
    with c1: st.button("Retour", on_click=change_step, args=(-1,))
    with c2:
        if st.button("Suivant"):
            if st.session_state.tel1 and st.session_state.email1: change_step(1)
            else: st.error("Téléphone et Email obligatoires.")

# 3. ATTESTATION (Persistance du fichier)
elif st.session_state.step == 3:
    st.header("3. Attestation de vigilance")
    st.markdown("Allez sur **urssaf.fr** → Mon compte → Mes attestations → Attestation de vigilance.")
    file = st.file_uploader("Téléchargez le PDF *", type=["pdf"])
    if file:
        st.session_state['file_bytes'] = file.read()
        st.session_state['file_name'] = file.name
    
    c1, c2 = st.columns(2)
    with c1: st.button("Retour", on_click=change_step, args=(-1,))
    with c2:
        if st.button("Suivant"):
            if 'file_bytes' in st.session_state: change_step(1)
            else: st.error("L'attestation est obligatoire.")

# 4. ORGANISATION
elif st.session_state.step == 4:
    st.header("4. Organisation")
    st.radio("Travaillez-vous seul ou à plusieurs ? *", ["Seul, sans remplaçant même ponctuel", "Seul, avec un remplaçant ponctuel", "Avec 1 ou 2 collaborateurs", "En équipe", "Autre"], key="org_type")
    
    if "collaborateurs" in st.session_state.org_type or "remplaçant" in st.session_state.org_type:
        st.text_input("Nom(s) du/des collaborateur(s) :", key="details_org")
    elif st.session_state.org_type == "En équipe":
        st.number_input("Nombre de personnes :", min_value=1, key="details_org")
    elif st.session_state.org_type == "Autre":
        st.text_area("Précisez votre situation :", key="details_org")

    if st.session_state.org_type != "Seul, sans remplaçant même ponctuel":
        st.text_area("Téléphones remplaçants :", key="tels_remp")
        st.text_area("Emails remplaçants :", key="emails_remp")
    
    c1, c2 = st.columns(2)
    with c1: st.button("Retour", on_click=change_step, args=(-1,))
    with c2: st.button("Suivant", on_click=change_step, args=(1,))

# 5. DISPOS & TARIFS
elif st.session_state.step == 5:
    st.header("5. Disponibilités & Tarifs")
    st.text_area("Quels sont vos jours et plages horaires de disponibilité ? *", key="dispos") # LE CHAMP DISPO
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.radio("Majoration Dimanche ?", ["Non", "Oui"], key="maj_dim")
        if st.session_state.maj_dim == "Oui":
            st.text_input("Montant Dimanche :", key="montant_dim")
    with col_b:
        st.radio("Majoration Jours Fériés ?", ["Non", "Oui"], key="maj_ferie")
        if st.session_state.maj_ferie == "Oui":
            st.text_input("Quels jours ?", key="lesquels_ferie")
            st.text_input("Montant Fériés :", key="montant_ferie")
    
    c1, c2 = st.columns(2)
    with c1: st.button("Retour", on_click=change_step, args=(-1,))
    with c2:
        if st.button("Suivant"):
            if st.session_state.dispos: change_step(1)
            else: st.error("Les disponibilités sont obligatoires.")

# 6. SECTEUR
elif st.session_state.step == 6:
    st.header("6. Secteur d'intervention")
    v_base = st.selectbox("Ville de départ *", sorted(df_v['affichage'].unique()), key="ville_base")
    rayon = st.slider("Rayon (km) *", 0, 200, 20, key="rayon")

    if st.button("Calculer les villes"):
        v_sel = df_v[df_v['affichage'] == v_base].iloc[0]
        def dist(r): return geodesic((v_sel['latitude'], v_sel['longitude']), (r['latitude'], r['longitude'])).km
        df_v['d'] = df_v.apply(dist, axis=1)
        st.session_state.villes_trouvees = df_v[df_v['d'] <= rayon].sort_values('d')['affichage'].head(100).tolist()

    if st.session_state.villes_trouvees:
        st.write("Sélectionnez vos villes :")
        villes_finales = []
        for v in st.session_state.villes_trouvees:
            if st.checkbox(v, value=True, key=f"v_{v}"):
                villes_finales.append(v)
        st.session_state['villes_finales_list'] = villes_finales

    st.text_area("Villes supplémentaires (à la main) :", key="villes_sup")

    c1, c2 = st.columns(2)
    with c1: st.button("Retour", on_click=change_step, args=(-1,))
    with c2:
        if st.button("Dernière étape"):
            if st.session_state.get('villes_finales_list'): change_step(1)
            else: st.error("Calculez et sélectionnez au moins une ville.")

# 7. ENVOI FINAL
elif st.session_state.step == 7:
    st.header("7. Finalisation")
    st.text_area("Notes libres / Questions :", key="info_libre")
    
    c1, c2 = st.columns(2)
    with c1: st.button("Retour", on_click=change_step, args=(-1,))
    with c2:
        if st.button("TRANSMETTRE MON DOSSIER"):
            with st.spinner('Envoi en cours...'):
                # Encodage du fichier sauvegardé
                content = base64.b64encode(st.session_state.file_bytes).decode() if 'file_bytes' in st.session_state else ""
                
                # PAYLOAD INTÉGRAL (Dispos et Statut inclus)
                payload = {
                    "identite": {
                        "nom": st.session_state.nom, "prenom": st.session_state.prenom, 
                        "siret": st.session_state.siret, "societe": st.session_state.societe,
                        "statut": st.session_state.statut
                    },
                    "contact": {
                        "tel1": st.session_state.tel1, "tel2": st.session_state.tel2, 
                        "email1": st.session_state.email1, "email2": st.session_state.email2
                    },
                    "disponibilites": st.session_state.dispos, # BIEN PRÉSENT ICI
                    "organisation": {
                        "type": st.session_state.org_type,
                        "details": st.session_state.get('details_org'),
                        "tels_remp": st.session_state.get('tels_remp'),
                        "emails_remp": st.session_state.get('emails_remp')
                    },
                    "tarifs": {
                        "maj_dim": {"active": st.session_state.maj_dim, "montant": st.session_state.get('montant_dim', '0')},
                        "maj_fer": {"active": st.session_state.maj_ferie, "jours": st.session_state.get('lesquels_ferie', ''), "montant": st.session_state.get('montant_ferie', '0')}
                    },
                    "secteur": {
                        "base": st.session_state.ville_base, "rayon": st.session_state.rayon,
                        "villes": st.session_state.get('villes_finales_list', []),
                        "villes_sup": st.session_state.villes_sup
                    },
                    "attestation": content,
                    "notes": st.session_state.info_libre
                }
                
                try:
                    r = requests.post("https://hub.cardin.cloud/webhook/Miseàjourdossierpresta", json=payload)
                    if r.status_code == 200:
                        st.balloons()
                        st.success("Dossier complet envoyé !")
                    else: st.error("Erreur d'envoi.")
                except: st.error("Erreur de connexion.")