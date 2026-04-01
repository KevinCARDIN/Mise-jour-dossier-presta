import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import requests
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="LetaHost - Partenaires", layout="centered")

# --- DESIGN CHIRURGICAL (FORCE LE CENTRAGE) ---
def set_design():
    try:
        with open("fond.png", "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        st.markdown(f'''
        <style>
        .stApp {{ background-image: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("data:image/png;base64,{bin_str}"); background-size: cover; background-attachment: fixed; }}
        
        /* 1. VISIBILITÉ TOTALE (Texte Noir sur Blanc) */
        input {{ color: black !important; }}
        .stTextInput>div>div>input, .stTextArea>div>textarea, .stSelectbox [data-baseweb="select"], .stNumberInput>div>div>input {{ 
            background-color: white !important; color: black !important; font-size: 18px !important; 
        }}
        /* Fix pour la barre de recherche des villes */
        div[data-baseweb="select"] input {{ color: black !important; }}
        div[role="listbox"] {{ color: black !important; }}

        /* 2. TITRES IMPOSANTS */
        h2 {{ font-size: 3.5rem !important; font-weight: 800 !important; color: white !important; text-align: center !important; line-height: 1.1 !important; margin-bottom: 30px !important; }}
        
        /* 3. LE FIX DU CENTRAGE ABSOLU */
        /* On force le conteneur du bouton à être un bloc Flex centré */
        .stButton {{
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
            padding: 10px 0 !important;
        }}

        .stButton > button {{
            background-color: #f1c40f !important;
            color: #000000 !important;
            border: none !important;
            font-weight: bold !important;
            padding: 12px 30px !important;
            border-radius: 8px !important;
            width: 250px !important;
            text-transform: uppercase;
        }}
        
        /* Force le centrage même quand il y a deux colonnes (Retour/Suivant) */
        [data-testid="column"] .stButton {{
            justify-content: center !important;
        }}

        p, label, li, .stMarkdown {{ color: white !important; text-align: center !important; font-size: 1.1rem !important; }}
        
        /* Zone de défilement pour les villes */
        .city-scroll {{
            max-height: 350px;
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

# --- CHARGEMENT DES DONNÉES SÉCURISÉ ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("villes_france.csv", usecols=['nom', 'latitude', 'longitude', 'code_postal'])
        # Fix pour l'erreur AttributeError 'float' object has no attribute 'split'
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

# 0. ACCUEIL
if st.session_state.step == 0:
    render_header("Mise à jour Dossier")
    st.write("Bienvenue sur votre portail partenaire LetaHost.")
    st.write("Ce questionnaire permet de réactualiser vos informations de prestataire.")
    st.button("DÉMARRER", on_click=go_to, args=(1,))

# 1. IDENTITÉ
elif st.session_state.step == 1:
    render_header("1. Vos informations")
    st.session_state.nom = st.text_input("NOM *", value=st.session_state.get('nom', ''))
    st.session_state.prenom = st.text_input("Prénom *", value=st.session_state.get('prenom', ''))
    
    # Le bouton est là, mais on vérifie au clic
    if st.button("CONTINUER"):
        if st.session_state.nom and st.session_state.prenom:
            go_to(2)
            st.rerun()
        else:
            st.error("Le Nom et le Prénom sont obligatoires pour continuer.")

# 2. STRUCTURE & SIRET
elif st.session_state.step == 2:
    render_header("2. Coordonnées & Structure")
    st.session_state.societe = st.text_input("Nom de la société", value=st.session_state.get('societe', ''))
    st.session_state.siret = st.text_input("Numéro SIRET *", value=st.session_state.get('siret', ''))
    st.session_state.statut = st.selectbox("Statut juridique *", ["Auto/Micro-Entrepreneur (EI)", "EURL", "SARL", "SAS", "Autre"])
    
    c1, c2 = st.columns(2)
    with c1: st.session_state.tel1 = st.text_input("Téléphone *", value=st.session_state.get('tel1', ''))
    with c2: st.session_state.email1 = st.text_input("Email *", value=st.session_state.get('email1', ''))
    
    col_b, col_n = st.columns(2)
    with col_b: st.button("RETOUR", on_click=go_to, args=(1,))
    with col_n: 
        if st.button("SUIVANT"):
            if st.session_state.siret and st.session_state.tel1 and st.session_state.email1:
                go_to(3); st.rerun()
            else: st.error("Champs obligatoires manquants (*).")

# 3. ATTESTATION (GUIDE URSSAF)
elif st.session_state.step == 3:
    render_header("3. Attestation de vigilance")
    st.markdown('''<div style="background:rgba(255,255,255,0.1); padding:20px; border-radius:10px; text-align:left;">
    <b>👉 Procédure pour récupérer votre document :</b><br>
    1. Connectez-vous sur votre compte <b>urssaf.fr</b><br>
    2. Rubrique <b>« Mes documents »</b><br>
    3. Cliquez sur <b>« Demander une attestation »</b><br>
    4. Sélectionnez <b>« Attestation de vigilance »</b> et téléchargez le PDF.</div>''', unsafe_allow_html=True)
    file = st.file_uploader("Joindre le PDF *", type=["pdf"])
    if file: st.session_state.file_bytes = file.read()
    
    cb, cn = st.columns(2)
    with cb: st.button("RETOUR", on_click=go_to, args=(2,))
    with cn: 
        if st.button("SUIVANT"):
            if 'file_bytes' in st.session_state: go_to(4); st.rerun()
            else: st.error("L'attestation PDF est obligatoire.")

# 4. ORGANISATION (TOUS LES CHOIX)
elif st.session_state.step == 4:
    render_header("4. Organisation")
    options = ["Seul, sans remplaçant même ponctuel", "Seul, avec un remplaçant ponctuel", "Avec 1 ou 2 collaborateurs", "En équipe", "Autre"]
    st.session_state.org_type = st.radio("Structure de travail *", options)
    if "Seul, sans" not in st.session_state.org_type:
        st.session_state.details_org = st.text_input("Nom(s) des intervenants :", value=st.session_state.get('details_org', ''))
        st.session_state.tels_remp = st.text_area("Téléphones de contact :", value=st.session_state.get('tels_remp', ''))
    
    cb, cn = st.columns(2)
    with cb: st.button("RETOUR", on_click=go_to, args=(3,))
    with cn: st.button("SUIVANT", on_click=go_to, args=(5,))

# 5. DISPOS & TARIFS (RETOUR DES DIMANCHES/FÉRIÉS)
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
    
    cb, cn = st.columns(2)
    with cb: st.button("RETOUR", on_click=go_to, args=(4,))
    with cn: 
        if st.session_state.dispos: go_to(6); st.rerun()
        else: st.error("Veuillez renseigner vos disponibilités.")

# 6. SECTEUR (LISTE À COCHER)
elif st.session_state.step == 6:
    render_header("6. Secteur")
    v_base = st.selectbox("Ville de départ", sorted(df_v['affichage'].unique()) if not df_v.empty else [])
    rayon = st.slider("Rayon d'action (km)", 0, 150, 30)
    
    if st.button("CALCULER LES VILLES"):
        sel = df_v[df_v['affichage'] == v_base].iloc[0]
        lat1, lon1 = float(sel['latitude']), float(sel['longitude'])
        def dist(r): return geodesic((lat1, lon1), (r['latitude'], r['longitude'])).km
        df_v['d'] = df_v.apply(dist, axis=1)
        st.session_state.villes_trouvees = df_v[df_v['d'] <= rayon]['affichage'].tolist()

    if st.session_state.get('villes_trouvees'):
        st.write("Décochez les villes où vous n'intervenez pas :")
        villes_finales = []
        st.markdown('<div class="city-scroll">', unsafe_allow_html=True)
        for v in st.session_state.villes_trouvees:
            if st.checkbox(v, value=True, key=f"v_{v}"): villes_finales.append(v)
        st.markdown('</div>', unsafe_allow_html=True)
        st.session_state.villes_finales_list = villes_finales

    st.session_state.villes_sup = st.text_area("Villes oubliées (manuelles) :", value=st.session_state.get('villes_sup', ''))
    
    cb, cn = st.columns(2)
    with cb: st.button("RETOUR", on_click=go_to, args=(5,))
    with cn: 
        if st.session_state.get('villes_finales_list'): go_to(7); st.rerun()
        else: st.error("Sélectionnez au moins une ville.")

# 7. FINALISATION (QUESTION PERSONNALISÉE)
elif st.session_state.step == 7:
    render_header("7. Finalisation")
    st.session_state.notes = st.text_area("Avez-vous d'autres informations à nous communiquer ?", value=st.session_state.get('notes', ''))
    
    def submit():
        f = st.session_state.get('file_bytes')
        content = base64.b64encode(f).decode() if f else ""
        payload = {
            "identite": {"nom": st.session_state.nom, "prenom": st.session_state.prenom, "siret": st.session_state.siret, "statut": st.session_state.statut},
            "contact": {"tel": st.session_state.tel1, "email": st.session_state.email1},
            "disponibilites": st.session_state.dispos,
            "tarifs": {"dimanche": st.session_state.get('montant_dim'), "feries": st.session_state.get('montant_ferie')},
            "secteur": {"villes_selectionnees": st.session_state.get('villes_finales_list', []), "villes_sup": st.session_state.get('villes_sup')},
            "notes": st.session_state.notes, "attestation": content
        }
        try:
            r = requests.post("https://hub.cardin.cloud/webhook/Miseàjourdossierpresta", json=payload)
            if r.status_code == 200: st.session_state.step = 8; st.rerun()
        except: st.error("Erreur technique lors de l'envoi.")

    cb, cn = st.columns(2)
    with cb: st.button("RETOUR", on_click=go_to, args=(6,))
    with cn: st.button("TRANSMETTRE", on_click=submit)

# 8. MERCI
elif st.session_state.step == 8:
    render_header("Merci !")
    st.balloons()
    st.write("Votre dossier a été transmis avec succès.")
    st.button("RETOUR À L'ACCUEIL", on_click=lambda: st.session_state.clear())