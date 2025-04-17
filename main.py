import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import datetime

# ----------------------------
# Database Connection Helpers
# ----------------------------

def connect_to_mongodb(collection_name):
    """
    Establishes a connection to the MongoDB collection using Streamlit secrets.
    """
    username = st.secrets["MongoDB"]["mongo_username"]
    password = st.secrets["MongoDB"]["mongo_password"]
    cluster_url = st.secrets["MongoDB"]["mongo_cluster_url"]
    client = MongoClient(f"mongodb+srv://{username}:{password}@{cluster_url}/")
    db = client[st.secrets["MongoDB"]["database_name"]]
    return db[collection_name]

def get_player_ids():
    """
    Fetches all player IDs from the 'roster' collection.
    """
    collection = connect_to_mongodb("roster")
    df = pd.DataFrame(list(collection.find()))
    return df["player_id"]

# ------------------------
# Constants and UI Options
# ------------------------

MEAL_TYPES = ['Ontbijt', 'Middag eten', 'Avond eten', 'Tussendoortje']
AMOUNT_UNITS = ['gr', 'ml', 'tas', 'snede', 'el', 'kl', 'stuk']
DAY_TYPES_FOOD = ['Wedstrijd', 'Training', 'Rust']
DAY_TYPES_WEIGHT = ['Wedstrijd', 'Training']

# ----------------------------
# Streamlit App Configuration
# ----------------------------

st.set_page_config(page_title="SK Beveren Voedingsdagboek", page_icon=":hamburger:", layout="centered")
# st.image("images/beveren_logo.png", width=150)
st.title('SK Beveren Voedingsdagboek')

# Setup tabs
fooddiary_tab, weightregistration_tab, info_tab = st.tabs(["Voedingsdagboek", "Gewichtsregistratie", "Extra informatie"])

# ------------------------
# Tab 1: Food Diary Entry
# ------------------------

with fooddiary_tab:

    # Dropdown to select player ID
    player_id = st.selectbox(   'Speler ID', 
                                options=get_player_ids(), 
                                index=get_player_ids().tolist().index(st.session_state.get('preserve_player_id')) if 'preserve_player_id' in st.session_state else None,
                                placeholder="Selecteer je Speler ID ...",
                                key='fooddiary_playerid')

    # Date input for the meal
    meal_date = st.date_input('Datum', value=datetime.today(), max_value=datetime.today(), format="DD/MM/YYYY", key='fooddiary_date')

    # Day type input
    day_type = st.radio('Type Dag', DAY_TYPES_FOOD, horizontal=True, index=None, key='fooddiary_daytype')

    # Meal type selection
    meal_type = st.radio('Type Maaltijd', MEAL_TYPES, horizontal=True, index=None)

    st.subheader('Elementen van de maaltijd:')

    # Initialize session state for food items
    if 'food_items' not in st.session_state:
        st.session_state.food_items = []

    # Form to add a food item
    with st.form(key='food_items_form'):
        col1, col2, col3, col4 = st.columns([1, 3, 1, 1])

        with col1:
            time = st.time_input('Tijdstip')
        with col2:
            food_product = st.text_input('Voedingsproduct')
        with col3:
            amount_value = st.number_input('Hoeveelheid', min_value=1, step=1)
        with col4:
            amount_unit = st.selectbox('Eenheid', options=AMOUNT_UNITS)

        submit_button = st.form_submit_button("Voedingsproduct toevoegen", icon=":material/bakery_dining:")

        if submit_button:
            # Validate input
            if not food_product.strip():
                st.warning("Voedingsproduct mag niet leeg zijn.")
            elif amount_value <= 0:
                st.warning("Hoeveelheid moet groter zijn dan nul.")
            else:
                # Add food item to session state
                st.session_state.food_items.append({
                    'time': time.strftime("%H:%M"),
                    'food_product': food_product,
                    'amount_value': amount_value,
                    'amount_unit': amount_unit
                })
                st.success('Voedingsproduct toegevoegd!')

    # Display current food items
    if st.session_state.food_items:
        st.write("Toegevoegde voedingsproducten:")
        st.dataframe(pd.DataFrame(st.session_state.food_items))

    # Final submission button to log the meal entry
    if st.button('Maaltijd toevoegen', icon=":material/restaurant:"):
        if not st.session_state.food_items:
            st.error("Je moet minstens één voedingsproduct toevoegen.")
        else:
            try:
                # Create meal entry dictionary
                new_meal_entry = {
                    "player_id": player_id,
                    "meal_date": int(meal_date.strftime("%Y%m%d")),
                    "day_type": day_type,
                    "weight_before": weight_before,
                    "weight_after": weight_after,
                    "meal_type": meal_type,
                    "meal_elements": st.session_state.food_items
                }

                # Insert into MongoDB
                collection = connect_to_mongodb("meal_diary_entries")
                collection.insert_one(new_meal_entry)

                st.success("Uw maaltijd is toegevoegd.")
                st.balloons()
                st.session_state.food_items = []  # Reset after submission
                st.session_state['preserve_player_id'] = player_id
                st.rerun()  # Clear form inputs

            except Exception as e:
                st.error("Verbindingsfout. Maaltijd niet kunnen toevoegen.")
                st.exception(e)

# -------------------------------
# Tab 2: Weight Registration Page
# -------------------------------

with weightregistration_tab:

    # Dropdown to select player ID
    player_id = st.selectbox(   'Speler ID', 
                                options=get_player_ids(), 
                                index=get_player_ids().tolist().index(st.session_state.get('preserve_player_id')) if 'preserve_player_id' in st.session_state else None,
                                placeholder="Selecteer je Speler ID ...",
                                key='weight_playerid')

    # Date input for the meal
    registration_date = st.date_input('Datum', value=datetime.today(), max_value=datetime.today(), format="DD/MM/YYYY", key='weight_date')

    # Day type input
    day_type = st.radio('Type Dag', DAY_TYPES_WEIGHT, horizontal=True, index=None, key='weight_daytype')

    # Weight entry for specific day types
    weight_before = None
    weight_after = None

    col1, col2 = st.columns(2)
    with col1:
        weight_before = st.number_input("Gewicht voor activiteit (kg)", min_value=0.0, step=0.1)
    with col2:
        weight_after = st.number_input("Gewicht na activiteit (kg)", min_value=0.0, step=0.1)

    # Final submission button to log the meal entry
    if st.button('Gewichtsregistratie toevoegen', icon=":material/weight:"):
        if weight_before == None or weight_after == None:
            st.error("Je moet een gewicht voor en na de activiteit invullen.")
        else:
            try:
                # Create meal entry dictionary
                new_weight_entry = {
                    "player_id": player_id,
                    "registration_date": int(meal_date.strftime("%Y%m%d")),
                    "day_type": day_type,
                    "weight_before": weight_before,
                    "weight_after": weight_after
                }

                # Insert into MongoDB
                collection = connect_to_mongodb("weight_registration")
                collection.insert_one(new_weight_entry)

                st.success("Uw gewicht is toegevoegd.")
                st.balloons()
                st.session_state['preserve_player_id'] = player_id
                st.rerun()  # Clear form inputs

            except Exception as e:
                st.error("Verbindingsfout. Gewicht niet kunnen toevoegen.")
                st.exception(e)

# -----------------------------
# Tab 3: Extra Information Page
# -----------------------------

with info_tab:
    st.subheader("Extra informatie")
    st.write("Maak zo een nauwkeurig mogelijke opsomming van alles wat je eet en drinkt op een dag.")
    st.markdown('''
        - Beschrijf wat je eet en drinkt.
        - Geef eventueel merknamen van het product.
        - Geef hoeveelheden weer zoals een kopje, stukken, ml, gram, porties ...
        - Vermeld de hoeveelheden zo nauwkeurig mogelijk in eenheden, kopjes, porties, theelepels, ml of grammen.
        - Als sommige voedingsproducten van buitenshuis komen (bv. een hamburger van McDonald's), vermeld dan de hoeveelheid op het etiket.
        - Als je op school eet, schrijf dan op welk eten je hebt gegeten en schrijf het woord "refter" aan het einde van de maaltijd.
        - Lees de onderstaande voorbeelden zorgvuldig voordat je begint te schrijven.
        - Vul het dagboek individueel in, zonder aanwezigheid van andere spelers.
        - Als je ergens hulp bij nodig hebt, vraag dan je ouders of trainers om hulp of neem contact met ons op.
    ''')