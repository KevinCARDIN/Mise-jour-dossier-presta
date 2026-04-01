import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import requests
import base64

# --- CONFIGURATION & PERFORMANCE ---
st.set_page_config(page_title="LetaHost - Partenaires", layout="centered")

# --- DESIGN & CENTRAGE ---
def set_design():
    try:
        with open("fond.png", "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        st.markdown(f'''
        <style>
        .stApp {{ background-image: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("data:image/png;base64,{bin_str}"); background-size: cover; background-attachment: fixed; }}
        
        /* Visibilité texte noir sur blanc */
        .stTextInput>div>div>input, .stTextArea>div>textarea, .stSelectbox>div>div, .stNumberInput>div>div>input {{ 
            background-color: white !important; color: black !important; font-size: 16px !important; border-radius: 5px !important;
        }}
        
        /* Titres imposants */
        h2 {{ font-size: 3rem !important; font-weight: 800 !important; color: white !important; text-align: center !important; line-height: 1.1 !important; margin-top: 5px !important; }}
        
        /* Style des boutons Jaunes */
        div.stButton > button {{ 
            background-color: #f1c40f !important; color: black !important; font-weight: bold !important; 
            border-radius: 8px !important; text-transform: uppercase !important; border: none !important;
            height: 50px !important;
        }}
        
        p, label, .stMarkdown {{ color: white !important; text-align: center !important; }}
        [data-testid="column"] {{ display: flex !important; justify-content: center !important; align-items: center !important; }}
        </style>
        ''', unsafe_allow_html=True)
    except: pass

def render_header(title):
    try:
        with open("letahost_logo.png", "rb") as f:
            logo_encoded = base64.b64encode(f.read()).decode()
        st.markdown(f'''
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 20px;">
                <img src="data:image/png;base64,{logo_encoded}" width="130">
                <h2>{title}</h2>
            </div>
        ''', unsafe_allow_html=True)
    except: st.header(title)

set_design()

# --- CHARGEMENT DES DONNÉES (CORRECTION ERREUR 'FLOAT' SPLIT) ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("villes_france.csv", usecols=['nom', 'latitude', 'longitude', 'code_postal'])
        # Correction robuste : on force en string et on nettoie sans utiliser apply(split) qui bugge sur les NaN/Floats
        df['cp_clean'] = df['code_postal'].astype(str).str.split('.').str[0].str.zfill(5)
        df['affichage'] = df['nom'] + " (" + df['cp_clean'] + ")"
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        return df.dropna(subset=['latitude', 'longitude'])
    except:
        return pd.DataFrame(columns=['nom', 'latitude', 'longitude', 'code_postal', 'affichage'])

df_v = load_data()

# --- LOGIQUE DE NAVIGATION (FIX DOUBLE-CLIC) ---
if 'step' not in st.session_state: st.session_state.step = 0

def go_to(idx): st.session_state.step = idx

# --- ÉTAPES ---

# 0. ACCUEIL
if st.session_state.step == 0:
    render_header("Mise à jour Dossier")
    st.write("Bienvenue sur votre espace partenaire LetaHost.")
    st.write("Ce questionnaire rapide nous permet de réactualiser vos informations de prestation.")
    _, col_btn, _ = st.columns([1, 1.5, 1])
    with col_btn: st.button("DÉMARRER", on_click=go_to, args=(1,), use_container_width=True)

# 1. IDENTITÉ (Uniquement Nom/Prénom selon feedback vidéo)
elif st.session_state.step == 1:
    render_header("1. Vos informations")
    st.session_state.nom = st.text_input("NOM *", value=st.session_state.get('nom', ''))
    st.session_state.prenom = st.text_input("Prénom *", value=st.session_state.get('prenom', ''))
    if st.session_state.nom and st.session_state.prenom:
        _, col_btn, _ = st.columns([1, 1.5, 1])
        with col_btn: st.button("CONTINUER", on_click=go_to, args=(2,), use_container_width=True)

# 2. STRUCTURE (SIRET déplacé ici)
elif st.session_state.step == 2:
    render_header("2. Coordonnées & Structure")
    st.session_state.societe = st.text_input("Nom de la société", value=st.session_state.get('societe', ''))
    st.session_state.siret = st.text_input("Numéro SIRET *", value=st.session_state.get('siret', ''))
    st.session_state.statut = st.selectbox("Statut juridique *", ["Auto/Micro-Entrepreneur (EI)", "EURL", "SARL", "SAS", "Autre"])
    
    c1, c2 = st.columns(2)
    with c1: st.session_state.tel1 = st.text_input("Téléphone *", value=st.session_state.get('tel1', ''))
    with c2: st.session_state.email1 = st.text_input("Email *", value=st.session_state.get('email1', ''))
    
    col_back, col_next = st.columns(2)
    with col_back: st.button("RETOUR", on_click=go_to, args=(1,), use_container_width=True)
    with col_next: st.button("SUIVANT", on_click=go_to, args=(3,), use_container_width=True)

# 3. ATTESTATION (Instructions restaurées)
elif st.session_state.step == 3:
    render_header("3. Attestation de vigilance")
    st.write("👉 Téléchargez votre document sur **urssaf.fr** (Rubrique 'Mes documents' > 'Attestations').")
    file = st.file_uploader("Joindre le PDF *", type=["pdf"])
    if file: st.session_state.file_bytes = file.read()
    
    col_back, col_next = st.columns(2)
    with col_back: st.button("RETOUR", on_click=go_to, args=(2,), use_container_width=True)
    with col_next: st.button("SUIVANT", on_click=go_to, args=(4,), use_container_width=True)

# 4. ORGANISATION (Retrait des "N/A")
elif st.session_state.step == 4:
    render_header("4. Organisation")
    st.session_state.org_type = st.radio("Structure *", ["Seul", "Seul avec remplaçant", "En équipe"])
    if st.session_state.org_type != "Seul":
        st.session_state.details_org = st.text_input("Nom des collaborateurs :", value=st.session_state.get('details_org', ''))
        st.session_state.tels_remp = st.text_area("Téléphones :", value=st.session_state.get('tels_remp', ''))
    
    col_back, col_next = st.columns(2)
    with col_back: st.button("RETOUR", on_click=go_to, args=(3,), use_container_width=True)
    with col_next: st.button("SUIVANT", on_click=go_to, args=(5,), use_container_width=True)

# 5. DISPOS & TARIFS
elif st.session_state.step == 5:
    render_header("5. Disponibilités")
    st.session_state.dispos = st.text_area("Précisez vos jours et horaires d'intervention :", value=st.session_state.get('dispos', ''))
    
    col_back, col_next = st.columns(2)
    with col_back: st.button("RETOUR", on_click=go_to, args=(4,), use_container_width=True)
    with col_next: st.button("SUIVANT", on_click=go_to, args=(6,), use_container_width=True)

# 6. SECTEUR
elif st.session_state.step == 6:
    render_header("6. Secteur")
    v_base = st.selectbox("Ville de départ", sorted(df_v['affichage'].unique()) if not df_v.empty else ["CSV non trouvé"])
    rayon = st.slider("Rayon d'action (km)", 0, 150, 30)
    
    if st.button("CALCULER LES VILLES", use_container_width=True):
        sel = df_v[df_v['affichage'] == v_base].iloc[0]
        def dist(r): return geodesic((sel['latitude'], sel['longitude']), (r['latitude'], r['longitude'])).km
        df_v['d'] = df_v.apply(dist, axis=1)
        st.session_state.villes_trouvees = df_v[df_v['d'] <= rayon]['affichage'].tolist()
    
    if st.session_state.get('villes_trouvees'):
        st.session_state.villes_finales = st.multiselect("Villes validées :", st.session_state.villes_trouvees, default=st.session_state.villes_trouvees)

    col_back, col_next = st.columns(2)
    with col_back: st.button("RETOUR", on_click=go_to, args=(5,), use_container_width=True)
    with col_next: st.button("DERNIÈRE ÉTAPE", on_click=go_to, args=(7,), use_container_width=True)

# 7. FINALISATION
elif st.session_state.step == 7:
    render_header("7. Finalisation")
    st.session_state.notes = st.text_area("Notes ou commentaires :", value=st.session_state.get('notes', ''))
    
    def handle_submit():
        payload = {
            "identite": {"nom": st.session_state.nom, "prenom": st.session_state.prenom, "siret": st.session_state.get('siret', ''), "statut": st.session_state.get('statut', '')},
            "contact": {"tel": st.session_state.get('tel1', ''), "email": st.session_state.get('email1', '')},
            "disponibilites": st.session_state.get('dispos', ''),
            "secteur": {"villes_selectionnees": st.session_state.get('villes_finales', [])},
            "notes": st.session_state.notes
        }
        try:
            requests.post("https://hub.cardin.cloud/webhook/Miseàjourdossierpresta", json=payload)
            st.session_state.step = 8
        except: st.error("Erreur de connexion.")

    col_back, col_next = st.columns(2)
    with col_back: st.button("RETOUR", on_click=go_to, args=(6,), use_container_width=True)
    with col_next: st.button("TRANSMETTRE", on_click=handle_submit, use_container_width=True)

# 8. MERCI
elif st.session_state.step == 8:
    render_header("Merci !")
    st.balloons()
    st.write("Votre dossier a été transmis avec succès à nos équipes.")
    st.write("Nous reviendrons vers vous très prochainement.")
    _, col_btn, _ = st.columns([1, 1.5, 1])
    with col_btn: st.button("RETOUR À L'ACCUEIL", on_click=lambda: st.session_state.clear(), use_container_width=True)