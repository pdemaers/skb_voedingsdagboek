"""
Streamlit Food Diary and Weight Tracking Application

This application allows athletes to:
1. Record their daily food intake with detailed meal information
2. Track weight measurements before/after activities
3. View helpful nutritional information

The application connects to MongoDB for data persistence and uses Streamlit for the UI.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Union

import pandas as pd
import streamlit as st
from pymongo import MongoClient, errors
from pymongo.collection import Collection

# ----------------------------
# Configuration and Constants
# ----------------------------

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application constants
MEAL_TYPES = ['Breakfast', 'Lunch', 'Dinner', 'Snack']
AMOUNT_UNITS = ['gr', 'ml', 'tas', 'snede', 'el', 'kl', 'stuk']
DAY_TYPES_FOOD = ['Match', 'Training', 'Rest']
DAY_TYPES_WEIGHT = ['Wedstrijd', 'Training']

# ----------------------------
# Database Connection Helpers
# ----------------------------

def connect_to_mongodb(collection_name: str) -> Optional[Collection]:
    """
    Establishes a secure connection to a MongoDB collection using Streamlit's Secrets Manager.

    Args:
        collection_name: The name of the MongoDB collection to connect to.

    Returns:
        A reference to the specified MongoDB collection if successful, None otherwise.

    Raises:
        KeyError: If required secrets are missing from Streamlit's configuration.
        ServerSelectionTimeoutError: If connection to MongoDB times out.
        Exception: For other unexpected connection errors.
    """
    try:
        # Validate secrets exist before attempting connection
        required_secrets = ["mongo_username", "mongo_password", "mongo_cluster_url", "database_name"]
        for secret in required_secrets:
            if secret not in st.secrets["MongoDB"]:
                raise KeyError(f"Missing required secret: {secret}")

        # Build connection string from secrets
        username = st.secrets["MongoDB"]["mongo_username"]
        password = st.secrets["MongoDB"]["mongo_password"]
        cluster_url = st.secrets["MongoDB"]["mongo_cluster_url"]
        database_name = st.secrets["MongoDB"]["database_name"]

        connection_string = f"mongodb+srv://{username}:{password}@{cluster_url}/"
        
        # Attempt connection with timeout
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        client.server_info()  # Test connection
        
        db = client[database_name]
        logger.info(f"Successfully connected to MongoDB collection: {collection_name}")
        return db[collection_name]
    
    except KeyError as e:
        error_msg = f"Missing MongoDB configuration in Streamlit secrets: {e}"
        logger.error(error_msg)
        st.error(error_msg)
    except errors.ServerSelectionTimeoutError:
        error_msg = "Unable to connect to MongoDB server. Please check your internet connection or credentials."
        logger.error(error_msg)
        st.error(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error connecting to MongoDB: {e}"
        logger.error(error_msg, exc_info=True)
        st.error("An unexpected error occurred while connecting to the database.")

    return None

def get_player_ids() -> pd.Series:
    """
    Fetches all player IDs from the 'roster' collection.

    Returns:
        A pandas Series containing all player IDs.

    Raises:
        Displays a Streamlit error message if the operation fails.
    """
    try:
        collection = connect_to_mongodb("roster")
        if collection is None:
            raise ConnectionError("Could not connect to MongoDB")
            
        df = pd.DataFrame(list(collection.find()))
        return df["player_id"]
    except Exception as e:
        error_msg = f"Failed to fetch player IDs: {e}"
        logger.error(error_msg, exc_info=True)
        st.error("Failed to load player data. Please try again later.")
        return pd.Series(dtype='object')  # Return empty Series to prevent app crash

# ----------------------------
# Data Model Classes
# ----------------------------

class FoodItem:
    """Represents a single food item in a meal."""
    
    def __init__(self, time: str, food_product: str, amount_value: float, amount_unit: str):
        self.time = time
        self.food_product = food_product
        self.amount_value = amount_value
        self.amount_unit = amount_unit

    def to_dict(self) -> Dict:
        """Converts the FoodItem to a dictionary for MongoDB storage."""
        return {
            'time': self.time,
            'food_product': self.food_product,
            'amount_value': self.amount_value,
            'amount_unit': self.amount_unit
        }

class MealEntry:
    """Represents a complete meal entry for the food diary."""
    
    def __init__(self, player_id: str, meal_date: datetime, day_type: str, 
                 meal_type: str, food_items: List[FoodItem]):
        self.player_id = player_id
        self.meal_date = meal_date
        self.day_type = day_type
        self.meal_type = meal_type
        self.food_items = food_items

    def to_dict(self) -> Dict:
        """Converts the MealEntry to a dictionary for MongoDB storage."""
        return {
            "player_id": self.player_id,
            "meal_date": int(self.meal_date.strftime("%Y%m%d")),
            "day_type": self.day_type,
            "meal_type": self.meal_type,
            "meal_elements": [item.to_dict() for item in self.food_items]
        }

class WeightEntry:
    """Represents a weight measurement entry."""
    
    def __init__(self, player_id: str, registration_date: datetime, 
                 day_type: str, weight_before: float, weight_after: float):
        self.player_id = player_id
        self.registration_date = registration_date
        self.day_type = day_type
        self.weight_before = weight_before
        self.weight_after = weight_after

    def to_dict(self) -> Dict:
        """Converts the WeightEntry to a dictionary for MongoDB storage."""
        return {
            "player_id": self.player_id,
            "registration_date": int(self.registration_date.strftime("%Y%m%d")),
            "day_type": self.day_type,
            "weight_before": self.weight_before,
            "weight_after": self.weight_after
        }

# ----------------------------
# UI Components
# ----------------------------

def initialize_session_state():
    """Initializes required session state variables."""
    if 'food_items' not in st.session_state:
        st.session_state.food_items = []
    if 'preserve_player_id' not in st.session_state:
        st.session_state.preserve_player_id = None

def render_food_diary_tab():
    """Renders the food diary entry form."""
    st.subheader('Food Diary Entry')
    
    try:
        player_ids = get_player_ids()
        if player_ids.empty:
            st.warning("No player data available. Please check database connection.")
            return

        player_id = st.selectbox(
            'Player ID', 
            options=player_ids, 
            index=player_ids.tolist().index(st.session_state.get('preserve_player_id')) 
            if 'preserve_player_id' in st.session_state and st.session_state.preserve_player_id in player_ids.values 
            else None,
            placeholder="Select your player ID ...",
            key='fooddiary_playerid'
        )

        meal_date = st.date_input(
            'Date', 
            value=datetime.today(), 
            max_value=datetime.today(), 
            format="DD/MM/YYYY", 
            key='fooddiary_date'
        )

        day_type = st.radio(
            'Day type', 
            DAY_TYPES_FOOD, 
            horizontal=True, 
            index=None, 
            key='fooddiary_daytype'
        )

        meal_type = st.radio(
            'Meal type', 
            MEAL_TYPES, 
            horizontal=True, 
            index=None
        )

        render_food_items_form()

        if st.session_state.food_items:
            st.write("Added food elements:")
            st.dataframe(pd.DataFrame([item.to_dict() for item in st.session_state.food_items]))

        if st.button('Add meal', icon=":material/restaurant:"):
            submit_meal_entry(player_id, meal_date, day_type, meal_type)

    except Exception as e:
        logger.error(f"Error in food diary tab: {e}", exc_info=True)
        st.error("An error occurred while loading the food diary form.")

def render_food_items_form():
    """Renders the form for adding individual food items."""
    with st.form(key='food_items_form'):
        col1, col2, col3, col4 = st.columns([1, 3, 1, 1])

        with col1:
            time = st.time_input('Time')
        with col2:
            food_product = st.text_input('Food element')
        with col3:
            amount_value = st.number_input('Amount', min_value=1, step=1)
        with col4:
            amount_unit = st.selectbox('Unit', options=AMOUNT_UNITS)

        if st.form_submit_button("Add food element", icon=":material/bakery_dining:"):
            validate_and_add_food_item(time, food_product, amount_value, amount_unit)

def validate_and_add_food_item(time: datetime.time, food_product: str, 
                              amount_value: float, amount_unit: str):
    """Validates and adds a food item to the session state."""
    if not food_product.strip():
        st.warning("Food element cannot be empty.")
    elif amount_value <= 0:
        st.warning("Amount has to be larger than 0.")
    else:
        st.session_state.food_items.append(
            FoodItem(
                time=time.strftime("%H:%M"),
                food_product=food_product.strip(),
                amount_value=amount_value,
                amount_unit=amount_unit
            )
        )
        st.success('Food element added!')

def submit_meal_entry(player_id: str, meal_date: datetime.date, 
                     day_type: str, meal_type: str):
    """Handles submission of a complete meal entry."""
    if not st.session_state.food_items:
        st.error("You must include at least one food element.")
        return

    try:
        meal_entry = MealEntry(
            player_id=player_id,
            meal_date=meal_date,
            day_type=day_type,
            meal_type=meal_type,
            food_items=st.session_state.food_items
        )

        collection = connect_to_mongodb("meal_diary_entries")
        if collection is None:
            raise ConnectionError("Could not connect to database")

        collection.insert_one(meal_entry.to_dict())
        
        st.success("Your meal has been added successfully!")
        st.balloons()
        
        # Reset form
        st.session_state.food_items = []
        st.session_state.preserve_player_id = player_id
        st.rerun()

    except Exception as e:
        logger.error(f"Failed to submit meal entry: {e}", exc_info=True)
        st.error("Failed to save your meal. Please try again.")

def render_weight_tracking_tab():
    """Renders the weight tracking form."""
    st.subheader('Weight Registration')
    
    try:
        player_ids = get_player_ids()
        if player_ids.empty:
            st.warning("No player data available. Please check database connection.")
            return

        player_id = st.selectbox(
            'Player ID', 
            options=player_ids, 
            index=player_ids.tolist().index(st.session_state.get('preserve_player_id')) 
            if 'preserve_player_id' in st.session_state and st.session_state.preserve_player_id in player_ids.values 
            else None,
            placeholder="Select your player ID ...",
            key='weight_playerid'
        )

        registration_date = st.date_input(
            'Date', 
            value=datetime.today(), 
            max_value=datetime.today(), 
            format="DD/MM/YYYY", 
            key='weight_date'
        )

        day_type = st.radio(
            'Day Type', 
            DAY_TYPES_WEIGHT, 
            horizontal=True, 
            index=None, 
            key='weight_daytype'
        )

        col1, col2 = st.columns(2)
        with col1:
            weight_before = st.number_input("Weight before activity (kg)", min_value=0.0, step=0.1)
        with col2:
            weight_after = st.number_input("Weight after activity (kg)", min_value=0.0, step=0.1)

        if st.button('Add weight registration', icon=":material/weight:"):
            submit_weight_entry(player_id, registration_date, day_type, weight_before, weight_after)

    except Exception as e:
        logger.error(f"Error in weight tracking tab: {e}", exc_info=True)
        st.error("An error occurred while loading the weight tracking form.")

def submit_weight_entry(player_id: str, registration_date: datetime.date, 
                       day_type: str, weight_before: float, weight_after: float):
    """Handles submission of a weight entry."""
    if weight_before <= 0 or weight_after <= 0:
        st.error("Weight values must be positive numbers.")
        return

    try:
        weight_entry = WeightEntry(
            player_id=player_id,
            registration_date=registration_date,
            day_type=day_type,
            weight_before=weight_before,
            weight_after=weight_after
        )

        collection = connect_to_mongodb("weight_registration")
        if collection is None:
            raise ConnectionError("Could not connect to database")

        collection.insert_one(weight_entry.to_dict())
        
        st.success("Weight registration added successfully!")
        st.balloons()
        
        # Preserve player ID for next use
        st.session_state.preserve_player_id = player_id
        st.rerun()

    except Exception as e:
        logger.error(f"Failed to submit weight entry: {e}", exc_info=True)
        st.error("Failed to save your weight registration. Please try again.")

def render_info_tab():
    """Renders the information/help tab."""
    st.subheader("Extra Information")
    st.write("Please provide as accurate as possible information about everything you eat and drink during the day.")
    st.markdown('''
        - Describe what you eat and drink
        - Include brand names when applicable
        - Specify quantities in precise measurements
        - For restaurant meals, note the establishment
        - Fill out the diary individually without assistance from other players
        - Contact your trainer if you need help
    ''')

# ----------------------------
# Main Application
# ----------------------------

def main():
    """Main application entry point."""
    # Configure page
    st.set_page_config(
        page_title="Athlete Nutrition Tracker", 
        page_icon=":hamburger:", 
        layout="centered"
    )
    st.title('Athlete Nutrition Tracker')

    # Initialize session state
    initialize_session_state()

    # Setup tabs
    tab1, tab2, tab3 = st.tabs([
        "Food Diary", 
        "Weight Tracking", 
        "Information"
    ])

    with tab1:
        render_food_diary_tab()

    with tab2:
        render_weight_tracking_tab()

    with tab3:
        render_info_tab()

if __name__ == "__main__":
    main()