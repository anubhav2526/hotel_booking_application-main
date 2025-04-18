import streamlit as st
import sqlite3
import os
from dotenv import load_dotenv
import requests
from datetime import date, datetime, timedelta
import pandas as pd
from groq import Groq
import re
import logging
import time
import random
import hashlib
from PIL import Image
import base64

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='hotel_booking_debug.log')

# Custom CSS for better UI
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    
    .main-title {
        font-size: 48px;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        margin-bottom: 30px;
        padding: 20px;
        text-shadow: 2px 2px 4px rgba(255,255,255,0.1);
    }
    
    .subheader {
        font-size: 24px;
        color: #ffffff;
        margin-top: 20px;
        text-align: center;
        font-weight: 500;
    }
    
    .stButton>button {
        background: linear-gradient(45deg, #1a237e, #3949ab);
        color: white;
        border-radius: 25px;
        padding: 12px 30px;
        font-size: 16px;
        font-weight: 500;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255,255,255,0.1);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255,255,255,0.2);
        background: linear-gradient(45deg, #283593, #3f51b5);
    }
    
    .stButton>button:disabled {
        background: #9fa8da;
        color: #ffffff;
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
    }
    
    .sidebar .sidebar-content {
        background: #1a1a1a;
        padding: 20px;
    }
    
    .hotel-card {
        background: #1a1a1a;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(255,255,255,0.1);
        transition: all 0.3s ease;
        border: 1px solid #333;
    }
    
    .hotel-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 20px rgba(255,255,255,0.15);
    }
    
    .success-message {
        background: #1b5e20;
        color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        margin-top: 15px;
        box-shadow: 0 2px 10px rgba(255,255,255,0.1);
    }
    
    .error-message {
        background: #b71c1c;
        color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        margin-top: 15px;
        box-shadow: 0 2px 10px rgba(255,255,255,0.1);
    }
    
    .info-message {
        background: #0d47a1;
        color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        box-shadow: 0 2px 10px rgba(255,255,255,0.1);
    }
    
    .welcome-container {
        background: rgba(26, 26, 26, 0.95);
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(255,255,255,0.1);
        margin: 20px auto;
        max-width: 800px;
        border: 1px solid #333;
    }
    
    .feature-card {
        background: #1a1a1a;
        border-radius: 15px;
        padding: 20px;
        margin: 10px;
        box-shadow: 0 4px 15px rgba(255,255,255,0.1);
        text-align: center;
        border: 1px solid #333;
    }
    
    .feature-card h3 {
        color: #ffffff;
        margin: 10px 0;
    }
    
    .feature-card p {
        color: #cccccc;
    }
    
    .feature-icon {
        font-size: 40px;
        margin-bottom: 15px;
        color: #3949ab;
    }
    
    /* Add styles for form inputs */
    .stTextInput>div>div>input {
        color: #ffffff;
        background-color: #1a1a1a;
        border: 1px solid #333;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #3949ab;
        box-shadow: 0 0 0 2px rgba(57, 73, 171, 0.2);
    }
    
    /* Style for labels */
    label {
        color: #ffffff !important;
        font-weight: 500;
    }
    
    /* Style for selectboxes */
    .stSelectbox>div>div>div {
        background-color: #1a1a1a;
        color: #ffffff;
        border: 1px solid #333;
    }
    
    /* Style for multiselect */
    .stMultiSelect>div>div>div {
        background-color: #1a1a1a;
        color: #ffffff;
        border: 1px solid #333;
    }
    
    /* Style for date inputs */
    .stDateInput>div>div>input {
        background-color: #1a1a1a;
        color: #ffffff;
        border: 1px solid #333;
    }
    
    /* Style for number inputs */
    .stNumberInput>div>div>input {
        background-color: #1a1a1a;
        color: #ffffff;
        border: 1px solid #333;
    }
    
    /* Style for checkboxes */
    .stCheckbox>div>label {
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# Add a background image with overlay for better text readability
def add_bg_from_url():
    st.markdown(
         f"""
         <style>
         .stApp {{
             background-image: linear-gradient(rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.9)), url("https://images.unsplash.com/photo-1566073771259-6a8506099945?ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80");
             background-attachment: fixed;
             background-size: cover;
         }}
         </style>
         """,
         unsafe_allow_html=True
     )

# Password hashing function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Database Manager Class
class DatabaseManager:
    def __init__(self):
        self.create_tables()

    def create_tables(self):
        conn = sqlite3.connect('hotel_booking.db')
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    hotel_name TEXT,
                    city TEXT,
                    check_in DATE,
                    check_out DATE,
                    room_type TEXT,
                    total_price REAL,
                    booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    hotel_id TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Database error during table creation: {e}")
        finally:
            conn.close()

    def register_user(self, username, password, email, full_name):
        conn = sqlite3.connect('hotel_booking.db')
        try:
            cursor = conn.cursor()
            hashed_password = hash_password(password)
            cursor.execute('INSERT INTO users (username, password, email, full_name) VALUES (?, ?, ?, ?)',
                           (username, hashed_password, email, full_name))
            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            logging.error(f"Registration failed: {e}")
            return False
        except sqlite3.Error as e:
            logging.error(f"Database error during registration: {e}")
            return False
        finally:
            conn.close()

    def authenticate_user(self, username, password):
        conn = sqlite3.connect('hotel_booking.db')
        try:
            cursor = conn.cursor()
            hashed_password = hash_password(password)
            cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_password))
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logging.error(f"Database error during authentication: {e}")
            return False
        finally:
            conn.close()

    def save_booking(self, user_id, hotel_name, hotel_id, city, check_in, check_out, room_type, total_price):
        conn = sqlite3.connect('hotel_booking.db')
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO bookings (user_id, hotel_name, hotel_id, city, check_in, check_out, room_type, total_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, hotel_name, hotel_id, city, check_in, check_out, room_type, total_price))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logging.error(f"Database error during booking save: {e}")
            return None
        finally:
            conn.close()

    def get_user_bookings(self, username):
        conn = sqlite3.connect('hotel_booking.db')
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT b.* FROM bookings b JOIN users u ON b.user_id = u.id
                WHERE u.username = ? ORDER BY b.booking_date DESC
            ''', (username,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Database error during fetching bookings: {e}")
            return []
        finally:
            conn.close()

    def get_user_id(self, username):
        conn = sqlite3.connect('hotel_booking.db')
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            logging.error(f"Database error during fetching user ID: {e}")
            return None
        finally:
            conn.close()

# Google Hotels API Client Class
class GoogleHotelsAPIClient:
    BASE_URL = "https://serpapi.com/search.json"

    def __init__(self):
        self.api_key = os.environ.get("SERPAPI_KEY")
        if not self.api_key:
            st.error("SERPAPI_KEY environment variable is not set")
            logging.error("SERPAPI_KEY environment variable is not set")
            raise ValueError("API Key Missing")

    def search_hotels(self, **params):
        default_params = {
            "engine": "google_hotels",
            "api_key": self.api_key,
            "currency": "INR",
            "gl": "in",  # Localize to India
            "hl": "en"   # Use English
        }
        
        # Map the parameters to the API expected format
        if 'destination' in params:
            default_params['q'] = params['destination']
        if 'num_people' in params:
            default_params['adults'] = params['num_people']
        if 'rooms' in params:
            default_params['rooms'] = params['rooms']
        if 'min_price' in params and params['min_price'] > 0:
            default_params['min_price'] = params['min_price']
        if 'max_price' in params and params['max_price'] > 0:
            default_params['max_price'] = params['max_price']
        if 'property_types' in params and params['property_types']:
            default_params['property_types'] = ",".join(params['property_types'])
        if 'amenities' in params and params['amenities']:
            default_params['amenities'] = ",".join(params['amenities'])
        if 'brands' in params and params['brands']:
            default_params['brands'] = ",".join(params['brands'])
        if 'hotel_class' in params and params['hotel_class']:
            default_params['hotel_class'] = ",".join(params['hotel_class'])
        if 'free_cancellation' in params:
            default_params['free_cancellation'] = "true" if params['free_cancellation'] else None
        if 'special_offers' in params:
            default_params['special_offers'] = "true" if params['special_offers'] else None
        if 'eco_certified' in params:
            default_params['eco_certified'] = "true" if params['eco_certified'] else None
        if 'vacation_rentals' in params:
            default_params['vacation_rentals'] = "true" if params['vacation_rentals'] else None
        if 'bedrooms' in params and params['bedrooms'] > 0:
            default_params['bedrooms'] = params['bedrooms']
        if 'bathrooms' in params and params['bathrooms'] > 0:
            default_params['bathrooms'] = params['bathrooms']
        
        try:
            logging.debug(f"Sending hotel search request with params: {default_params}")
            response = requests.get(self.BASE_URL, params=default_params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                error_message = data['error']
                logging.error(f"API returned error: {error_message}")
                st.error(f"Search failed: {error_message}")
                return None
            
            # Extract and format the hotel results
            hotels = []
            if 'hotels_results' in data:
                for hotel in data['hotels_results']:
                    hotel_data = {
                        'id': hotel.get('hotel_id', ''),
                        'name': hotel.get('name', 'Unknown Hotel'),
                        'location': hotel.get('address', 'Location not available'),
                        'price': hotel.get('price', {}).get('total', 0),
                        'rating': hotel.get('rating', 0),
                        'amenities': hotel.get('amenities', []),
                        'property_token': hotel.get('hotel_id', '')
                    }
                    hotels.append(hotel_data)
            
            if not hotels:
                logging.warning("No hotels found in the search results")
                return None
                
            logging.info(f"Hotel search successful for '{params.get('destination')}' - Found {len(hotels)} hotels")
            return hotels
            
        except requests.exceptions.HTTPError as e:
            error_message = f"HTTP Error: {str(e)}"
            if e.response.status_code == 400:
                try:
                    error_details = e.response.json().get('error', 'No additional error details provided')
                    error_message += f" - Details: {error_details}"
                except ValueError:
                    error_message += " - Could not parse error details from response"
            logging.error(error_message)
            st.error(error_message)
            return None
        except requests.exceptions.Timeout:
            error_message = "Request timed out. Please try again later."
            logging.error(error_message)
            st.error(error_message)
            return None
        except requests.exceptions.ConnectionError:
            error_message = "Connection Error. Please check your internet connection."
            logging.error(error_message)
            st.error(error_message)
            return None
        except requests.exceptions.RequestException as e:
            error_message = f"Request failed: {str(e)}"
            logging.error(error_message)
            st.error(error_message)
            return None
        except ValueError as e:
            error_message = f"Invalid response from API: {str(e)}"
            logging.error(error_message)
            st.error(error_message)
            return None
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            logging.error(error_message)
            st.error(error_message)
            return None

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'show_registration' not in st.session_state:
    st.session_state['show_registration'] = False
if 'error_message' not in st.session_state:
    st.session_state['error_message'] = None
if 'success_message' not in st.session_state:
    st.session_state['success_message'] = None
if 'search_results' not in st.session_state:
    st.session_state['search_results'] = None
if 'selected_hotel' not in st.session_state:
    st.session_state['selected_hotel'] = None
if 'show_booking_summary' not in st.session_state:
    st.session_state['show_booking_summary'] = False
if 'show_payment' not in st.session_state:
    st.session_state['show_payment'] = False
if 'show_confirmation' not in st.session_state:
    st.session_state['show_confirmation'] = False
if 'booking_params' not in st.session_state:
    st.session_state['booking_params'] = {}
if 'form_destination' not in st.session_state:
    st.session_state['form_destination'] = ""
if 'form_num_people' not in st.session_state:
    st.session_state['form_num_people'] = 2
if 'form_rooms' not in st.session_state:
    st.session_state['form_rooms'] = 1
if 'form_check_in' not in st.session_state:
    st.session_state['form_check_in'] = date.today()
if 'form_check_out' not in st.session_state:
    st.session_state['form_check_out'] = date.today() + timedelta(days=1)
if 'form_sort_by' not in st.session_state:
    st.session_state['form_sort_by'] = "Relevance"
if 'form_min_price' not in st.session_state:
    st.session_state['form_min_price'] = 0
if 'form_max_price' not in st.session_state:
    st.session_state['form_max_price'] = 1000
if 'form_property_types' not in st.session_state:
    st.session_state['form_property_types'] = []
if 'form_amenities' not in st.session_state:
    st.session_state['form_amenities'] = []
if 'form_rating' not in st.session_state:
    st.session_state['form_rating'] = "Any"
if 'form_brands' not in st.session_state:
    st.session_state['form_brands'] = []
if 'form_hotel_class' not in st.session_state:
    st.session_state['form_hotel_class'] = []
if 'form_free_cancellation' not in st.session_state:
    st.session_state['form_free_cancellation'] = False
if 'form_special_offers' not in st.session_state:
    st.session_state['form_special_offers'] = False
if 'form_eco_certified' not in st.session_state:
    st.session_state['form_eco_certified'] = False
if 'form_vacation_rentals' not in st.session_state:
    st.session_state['form_vacation_rentals'] = False
if 'reset_filters_confirm' not in st.session_state:
    st.session_state['reset_filters_confirm'] = False
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'booking_state' not in st.session_state:
    st.session_state['booking_state'] = "idle"
if 'search_error' not in st.session_state:
    st.session_state['search_error'] = None
if 'is_searching' not in st.session_state:
    st.session_state['is_searching'] = False
if 'date_error' not in st.session_state:
    st.session_state['date_error'] = None

# Initialize database and API clients
try:
    db_manager = DatabaseManager()
    google_hotels_client = GoogleHotelsAPIClient()
except Exception as e:
    st.error(f"Error initializing application: {str(e)}")
    st.stop()

# Login Page
def login_page():
    add_bg_from_url()
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">Welcome to LuxeStay</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subheader">Your Premium Hotel Booking Experience</p>', unsafe_allow_html=True)
    
    # Create three columns for features
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🏨</div>
                <h3>Premium Hotels</h3>
                <p>Access to luxury hotels worldwide</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">💳</div>
                <h3>Easy Booking</h3>
                <p>Simple and secure payment process</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🤖</div>
                <h3>AI Assistant</h3>
                <p>24/7 support for your queries</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display error or success messages if any
    if st.session_state.get('error_message'):
        st.error(st.session_state['error_message'])
        st.session_state['error_message'] = None
    if st.session_state.get('success_message'):
        st.success(st.session_state['success_message'])
        st.session_state['success_message'] = None
    
    # Login form with enhanced styling
    with st.form(key='login_form', clear_on_submit=True):
        st.markdown('<h2 style="text-align: center; color: #2c3e50;">Login</h2>', unsafe_allow_html=True)
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        col1, col2 = st.columns(2)
        with col1:
            login_button = st.form_submit_button("Login", use_container_width=True)
        with col2:
            register_button = st.form_submit_button("Register", use_container_width=True)
        
        if login_button:
            try:
                if not username or not password:
                    st.session_state['error_message'] = "Please enter both username and password"
                elif db_manager.authenticate_user(username, password):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['success_message'] = "Login successful!"
                    st.rerun()
                else:
                    st.session_state['error_message'] = "Invalid username or password"
            except Exception as e:
                st.session_state['error_message'] = f"An error occurred: {str(e)}"
        
        if register_button:
            st.session_state['show_registration'] = True
            st.rerun()
    
    # Registration form
    if st.session_state.get('show_registration', False):
        with st.form(key='register_form', clear_on_submit=True):
            st.markdown('<h2 style="text-align: center; color: #2c3e50;">Register</h2>', unsafe_allow_html=True)
            full_name = st.text_input("Full Name", key="reg_full_name")
            email = st.text_input("Email", key="reg_email")
            reg_username = st.text_input("Username", key="reg_username")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
            col1, col2 = st.columns(2)
            with col1:
                register_submit = st.form_submit_button("Create Account", use_container_width=True)
            with col2:
                back_button = st.form_submit_button("Back to Login", use_container_width=True)
            
            if register_submit:
                try:
                    if not all([full_name, email, reg_username, reg_password, confirm_password]):
                        st.session_state['error_message'] = "All fields are required"
                    elif reg_password != confirm_password:
                        st.session_state['error_message'] = "Passwords do not match"
                    elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                        st.session_state['error_message'] = "Invalid email format"
                    elif len(reg_password) < 6:
                        st.session_state['error_message'] = "Password must be at least 6 characters long"
                    else:
                        if db_manager.register_user(reg_username, reg_password, email, full_name):
                            st.session_state['success_message'] = "Registration successful! Please login."
                            st.session_state['show_registration'] = False
                            st.rerun()
                        else:
                            st.session_state['error_message'] = "Username or email already exists"
                except Exception as e:
                    st.session_state['error_message'] = f"An error occurred during registration: {str(e)}"
            
            if back_button:
                st.session_state['show_registration'] = False
                st.rerun()

# Main App
def main_app():
    add_bg_from_url()
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    st.markdown(f'<h1 class="main-title">Welcome, {st.session_state["username"]}!</h1>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### Navigation")
        page = st.selectbox("Go to", ["Search Hotels", "My Bookings", "Chat with Bot", "Logout"])
        
        if page == "Logout":
            if st.button("Confirm Logout"):
                st.session_state.clear()
                st.rerun()
    
    if page == "Search Hotels":
        if st.session_state.get('show_booking_summary'):
            show_booking_summary()
        elif st.session_state.get('show_payment'):
            show_payment_page()
        elif st.session_state.get('show_confirmation'):
            show_confirmation_page()
        else:
            hotel_search_page()
    elif page == "My Bookings":
        my_bookings_page()
    elif page == "Chat with Bot":
        chat_page()

# Function to check room availability (mock implementation)
def check_room_availability(hotel):
    extracted_rate = hotel.get('total_rate', {}).get('extracted_lowest', None)
    return extracted_rate is not None

# Hotel Search Page
def hotel_search_page():
    add_bg_from_url()
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">Hotel Search</h1>', unsafe_allow_html=True)
    
    # Initialize session state for search
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'search_error' not in st.session_state:
        st.session_state.search_error = None
    if 'is_searching' not in st.session_state:
        st.session_state.is_searching = False
    if 'date_error' not in st.session_state:
        st.session_state.date_error = None
    
    # Display any previous search errors
    if st.session_state.search_error:
        st.markdown(f'<div class="error-message">{st.session_state.search_error}</div>', unsafe_allow_html=True)
        st.session_state.search_error = None
    
    # Display any date validation errors
    if st.session_state.date_error:
        st.markdown(f'<div class="error-message">{st.session_state.date_error}</div>', unsafe_allow_html=True)
        st.session_state.date_error = None
    
    with st.form("search_form"):
        # Basic Search Section
        st.markdown('<h3 style="color: #ffffff;">Basic Search</h3>', unsafe_allow_html=True)
        destination = st.text_input("Destination", value=st.session_state.get('form_destination', ''), 
                                  help="Enter city name or specific location")
        num_people = st.number_input("Number of People", min_value=1, max_value=10, 
                                   value=st.session_state.get('form_num_people', 2),
                                   help="Select number of guests")
        rooms = st.number_input("Number of Rooms", min_value=1, max_value=5,
                              value=st.session_state.get('form_rooms', 1),
                              help="Select number of rooms needed")
        
        # Date Selection Section
        st.markdown('<h3 style="color: #ffffff;">Dates</h3>', unsafe_allow_html=True)
        today = datetime.now().date()
        check_in = st.date_input("Check-in Date", 
                               value=st.session_state.get('form_check_in', today),
                               min_value=today,
                               help="Select check-in date")
        check_out = st.date_input("Check-out Date",
                                value=st.session_state.get('form_check_out', today + timedelta(days=1)),
                                min_value=check_in + timedelta(days=1),
                                help="Select check-out date")
        
        # Advanced Filters Section
        st.markdown('<h3 style="color: #ffffff;">Advanced Filters</h3>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            min_price = st.number_input("Minimum Price", min_value=0, max_value=10000,
                                      value=st.session_state.get('form_min_price', 0),
                                      help="Set minimum price per night")
            max_price = st.number_input("Maximum Price", min_value=min_price, max_value=10000,
                                      value=st.session_state.get('form_max_price', 1000),
                                      help="Set maximum price per night")
            star_rating = st.selectbox("Star Rating",
                                     options=['Any', '3+', '4+', '5'],
                                     index=st.session_state.get('form_rating_index', 0),
                                     help="Select minimum star rating")
        
        with col2:
            amenities = st.multiselect("Amenities",
                                     options=['WiFi', 'Pool', 'Spa', 'Gym', 'Restaurant', 'Parking'],
                                     default=st.session_state.get('form_amenities', []),
                                     help="Select required amenities")
            property_types = st.multiselect("Property Types",
                                          options=['Hotel', 'Resort', 'Apartment', 'Hostel'],
                                          default=st.session_state.get('form_property_types', ['Hotel']),
                                          help="Select property types")
            vacation_rentals = st.checkbox("Include Vacation Rentals",
                                         value=st.session_state.get('form_vacation_rentals', False),
                                         help="Include vacation rentals in search results")
        
        # Search Button
        search_button = st.form_submit_button("Search Hotels", 
                                            help="Click to search for hotels matching your criteria")
    
    # Handle search form submission
    if search_button:
        try:
            # Validate inputs
            if not destination.strip():
                st.session_state.search_error = "Please enter a destination"
                st.rerun()
            
            if check_out <= check_in:
                st.session_state.date_error = "Check-out date must be after check-in date"
                st.rerun()
            
            if max_price < min_price:
                st.session_state.search_error = "Maximum price must be greater than minimum price"
                st.rerun()
            
            # Update session state
            st.session_state.update({
                'form_destination': destination,
                'form_num_people': num_people,
                'form_rooms': rooms,
                'form_check_in': check_in,
                'form_check_out': check_out,
                'form_min_price': min_price,
                'form_max_price': max_price,
                'form_rating': star_rating,
                'form_amenities': amenities,
                'form_property_types': property_types,
                'form_vacation_rentals': vacation_rentals,
                'form_rating_index': ['Any', '3+', '4+', '5'].index(star_rating)
            })
            
            # Set searching state
            st.session_state.is_searching = True
            
            # Perform search
            try:
                search_results = google_hotels_client.search_hotels(
                    destination=destination,
                    num_people=num_people,
                    rooms=rooms,
                    check_in=check_in,
                    check_out=check_out,
                    min_price=min_price,
                    max_price=max_price,
                    property_types=property_types,
                    amenities=amenities,
                    vacation_rentals=vacation_rentals
                )
                
                if not search_results:
                    st.session_state.search_error = "No hotels found matching your criteria. Try adjusting your search parameters."
                else:
                    st.session_state.search_results = search_results
                    st.session_state.search_error = None
                
            except Exception as e:
                st.session_state.search_error = f"Error searching hotels: {str(e)}"
                logging.error(f"Search error: {str(e)}")
            
            finally:
                st.session_state.is_searching = False
                st.rerun()
            
        except Exception as e:
            st.session_state.search_error = f"An error occurred: {str(e)}"
            logging.error(f"Form submission error: {str(e)}")
            st.rerun()
    
    # Display search results
    if st.session_state.search_results:
        st.markdown('<h2 style="color: #ffffff;">Search Results</h2>', unsafe_allow_html=True)
        
        for hotel in st.session_state.search_results:
            with st.container():
                st.markdown(f'''
                    <div class="hotel-card">
                        <h3 style="color: #ffffff;">{hotel['name']}</h3>
                        <p style="color: #cccccc;">📍 {hotel['location']}</p>
                        <p style="color: #cccccc;">⭐ {hotel['rating']} ({hotel['reviews']} reviews)</p>
                        <p style="color: #cccccc;">💰 ${hotel['price']} per night</p>
                        <p style="color: #cccccc;">🛏️ {hotel['rooms_available']} rooms available</p>
                    </div>
                ''', unsafe_allow_html=True)
                
                if st.button("Select", key=f"select_{hotel['id']}"):
                    st.session_state.selected_hotel = hotel
                    st.session_state.show_booking_summary = True
                    st.rerun()
    
    # Show loading state during search
    if st.session_state.is_searching:
        st.markdown('<div style="text-align: center; color: #ffffff;">Searching for hotels...</div>', unsafe_allow_html=True)
        st.spinner()

# Booking Summary Page
def show_booking_summary():
    add_bg_from_url()
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">Booking Summary</h1>', unsafe_allow_html=True)
    
    if 'selected_hotel' not in st.session_state:
        st.error("No hotel selected. Please search for hotels first.")
        if st.button("Back to Search"):
            st.session_state['show_booking_summary'] = False
            st.session_state['show_search_results'] = True
            st.rerun()
        return
    
    hotel = st.session_state['selected_hotel']
    
    # Display hotel details
    st.markdown("### Hotel Details")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Hotel:** {hotel['name']}")
        st.markdown(f"**Location:** {hotel['location']}")
        st.markdown(f"**Price per night:** ${hotel['price']}")
        st.markdown(f"**Rating:** {hotel['rating']} ⭐")
    
    with col2:
        if hotel.get('amenities'):
            st.markdown("**Amenities:**")
            for amenity in hotel['amenities']:
                st.markdown(f"- {amenity}")
    
    # Room selection
    st.markdown("### Room Selection")
    num_rooms = st.number_input("Number of Rooms", min_value=1, max_value=5, value=1)
    total_price = hotel['price'] * num_rooms
    
    st.markdown(f"### Total Price: ${total_price}")
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Proceed to Payment", use_container_width=True):
            st.session_state['num_rooms'] = num_rooms
            st.session_state['total_price'] = total_price
            st.session_state['show_booking_summary'] = False
            st.session_state['show_payment'] = True
            st.rerun()
    
    with col2:
        if st.button("Back to Search", use_container_width=True):
            st.session_state['show_booking_summary'] = False
            st.session_state['show_search_results'] = True
            st.rerun()

def show_payment_page():
    add_bg_from_url()
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">Payment Details</h1>', unsafe_allow_html=True)
    
    # Validate session state
    if 'selected_hotel' not in st.session_state:
        st.error("No hotel selected. Please search for hotels first.")
        if st.button("Back to Search", use_container_width=True):
            st.session_state['show_payment'] = False
            st.session_state['show_search_results'] = True
            st.rerun()
        return
    
    hotel = st.session_state['selected_hotel']
    num_rooms = st.session_state.get('num_rooms', 1)
    total_price = st.session_state.get('total_price', hotel['price'])
    
    # Display booking summary with improved styling
    st.markdown("""
        <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h3 style='color: #2c3e50; margin-bottom: 10px;'>Booking Summary</h3>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Hotel:** {hotel['name']}")
        st.markdown(f"**Location:** {hotel['location']}")
        st.markdown(f"**Number of Rooms:** {num_rooms}")
        st.markdown(f"**Check-in:** {st.session_state['form_check_in'].strftime('%Y-%m-%d')}")
        st.markdown(f"**Check-out:** {st.session_state['form_check_out'].strftime('%Y-%m-%d')}")
    
    with col2:
        st.markdown(f"**Price per Room:** ${hotel['price']}")
        st.markdown(f"**Total Price:** ${total_price}")
        st.markdown("**Payment Status:** Pending")
    
    # Payment form with improved validation
    with st.form(key='payment_form', clear_on_submit=True):
        st.markdown("""
            <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
                <h3 style='color: #2c3e50; margin-bottom: 10px;'>Payment Information</h3>
            </div>
        """, unsafe_allow_html=True)
        
        card_number = st.text_input("Card Number", max_chars=16, help="Enter 16-digit card number")
        expiry = st.text_input("Expiry Date (MM/YY)", max_chars=5, help="Format: MM/YY")
        cvv = st.text_input("CVV", max_chars=3, type="password", help="3-digit security code")
        cardholder = st.text_input("Cardholder Name", help="Name as it appears on card")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Pay Now", use_container_width=True):
                # Validate payment details
                validation_errors = []
                
                if not card_number or len(card_number) != 16 or not card_number.isdigit():
                    validation_errors.append("Please enter a valid 16-digit card number")
                
                if not expiry or not is_expiry_valid(expiry):
                    validation_errors.append("Please enter a valid expiry date (MM/YY)")
                
                if not cvv or len(cvv) != 3 or not cvv.isdigit():
                    validation_errors.append("Please enter a valid 3-digit CVV")
                
                if not cardholder:
                    validation_errors.append("Please enter the cardholder name")
                
                if validation_errors:
                    for error in validation_errors:
                        st.error(error)
                    return
                
                try:
                    # Process payment and save booking
                    user_id = db_manager.get_user_id(st.session_state['username'])
                    if not user_id:
                        st.error("User not found. Please login again.")
                        return
                    
                    booking_id = db_manager.save_booking(
                        user_id=user_id,
                        hotel_name=hotel['name'],
                        hotel_id=hotel['id'],
                        city=hotel['location'],
                        check_in=st.session_state['form_check_in'],
                        check_out=st.session_state['form_check_out'],
                        room_type="Standard",
                        total_price=total_price
                    )
                    
                    if booking_id:
                        st.session_state['booking_id'] = booking_id
                        st.session_state['show_payment'] = False
                        st.session_state['show_confirmation'] = True
                        st.rerun()
                    else:
                        st.error("Failed to save booking. Please try again.")
                except Exception as e:
                    st.error(f"An error occurred during payment processing: {str(e)}")
                    logging.error(f"Payment error: {str(e)}")
        
        with col2:
            if st.form_submit_button("Back", use_container_width=True):
                st.session_state['show_payment'] = False
                st.session_state['show_booking_summary'] = True
                st.rerun()

def show_confirmation_page():
    add_bg_from_url()
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">Booking Confirmed!</h1>', unsafe_allow_html=True)
    
    if 'booking_id' not in st.session_state:
        st.error("No booking found. Please complete the booking process.")
        if st.button("Back to Search"):
            st.session_state['show_confirmation'] = False
            st.session_state['show_search_results'] = True
            st.rerun()
        return
    
    st.markdown("### Booking Details")
    hotel = st.session_state['selected_hotel']
    num_rooms = st.session_state.get('num_rooms', 1)
    total_price = st.session_state.get('total_price', hotel['price'])
    
    # Display booking details
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Booking ID:** {st.session_state['booking_id']}")
        st.markdown(f"**Hotel:** {hotel['name']}")
        st.markdown(f"**Location:** {hotel['location']}")
        st.markdown(f"**Number of Rooms:** {num_rooms}")
    
    with col2:
        st.markdown(f"**Check-in Date:** {st.session_state['form_check_in'].strftime('%Y-%m-%d')}")
        st.markdown(f"**Check-out Date:** {st.session_state['form_check_out'].strftime('%Y-%m-%d')}")
        st.markdown(f"**Total Price:** ${total_price}")
    
    st.markdown("### Thank you for your booking!")
    st.markdown("A confirmation email has been sent to your registered email address.")
    
    if st.button("Back to Search", use_container_width=True):
        st.session_state['show_confirmation'] = False
        st.session_state['show_search_results'] = True
        st.rerun()

# My Bookings Page
def my_bookings_page():
    add_bg_from_url()
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">My Bookings</h1>', unsafe_allow_html=True)
    
    if 'username' not in st.session_state:
        st.error("Please login to view your bookings")
        return
    
    bookings = db_manager.get_user_bookings(st.session_state['username'])
    if not bookings:
        st.info("You have no bookings yet. Start by searching for a hotel!")
        if st.button("Search Hotels", use_container_width=True):
            st.session_state['show_search_results'] = True
            st.rerun()
        return
    
    # Display booking history
    st.markdown("### Your Booking History")
    for booking in bookings:
        with st.container():
            st.markdown('<div class="hotel-card">', unsafe_allow_html=True)
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Hotel:** {booking[2]}")
                st.markdown(f"**Location:** {booking[3]}")
                st.markdown(f"**Check-in:** {booking[4]}")
                st.markdown(f"**Check-out:** {booking[5]}")
                st.markdown(f"**Room Type:** {booking[6]}")
                st.markdown(f"**Total Price:** ${booking[7]}")
            
            with col2:
                st.markdown(f"**Booking ID:** {booking[0]}")
                st.markdown(f"**Booking Date:** {booking[8]}")
            st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("Back to Search", use_container_width=True):
        st.session_state['show_search_results'] = True
        st.rerun()

# Chat Page
def chat_page():
    add_bg_from_url()
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">Chat with Travel Bot</h1>', unsafe_allow_html=True)
    
    # Initialize Groq client with error handling
    try:
        groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        if not groq_client.api_key:
            st.error("GROQ_API_KEY environment variable is not set. Please contact support.")
            return
    except Exception as e:
        st.error(f"Error initializing chat service: {str(e)}")
        return
    
    # Chat interface with improved styling
    st.markdown("""
        <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h3 style='color: #2c3e50; margin-bottom: 10px;'>Chat with Hotel Assistant</h3>
            <p style='color: #7f8c8d;'>Ask questions about your booking or get help with your stay.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Display chat messages with improved styling
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(f"""
                    <div style='padding: 10px; border-radius: 5px; 
                              background-color: {'#e3f2fd' if message["role"] == "assistant" else '#f5f5f5'};'>
                        {message["content"]}
                    </div>
                """, unsafe_allow_html=True)
    
    # Chat input with improved UX
    if prompt := st.chat_input("What would you like to know?", key="chat_input"):
        try:
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get assistant response with loading state
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = handle_booking_chat(prompt, google_hotels_client)
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    except Exception as e:
                        error_msg = "I apologize, but I encountered an error. Please try again or contact support."
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        logging.error(f"Chat error: {str(e)}")
        except Exception as e:
            st.error("An error occurred while processing your message. Please try again.")
            logging.error(f"Chat processing error: {str(e)}")
    
    # Navigation buttons with improved styling
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        if st.button("Back to Bookings", use_container_width=True):
            st.session_state['show_search_results'] = True
            st.rerun()

# Handle booking chat
def handle_booking_chat(user_input, google_hotels_client):
    if user_input.lower() in ["cancel", "stop"]:
        st.session_state['booking_state'] = "idle"
        st.session_state['booking_params'] = {}
        return "Booking cancelled."
    
    elif st.session_state['booking_state'] == "destination":
        st.session_state['booking_params'] = {'destination': user_input}
        st.session_state['booking_state'] = "check_in"
        return "When do you want to check in? (YYYY-MM-DD)"
    
    elif st.session_state['booking_state'] == "check_in":
        try:
            check_in = date.fromisoformat(user_input)
            if check_in < date.today():
                return "Check-in date must be today or in the future."
            st.session_state['booking_params']['check_in'] = check_in
            st.session_state['booking_state'] = "check_out"
            return "When do you want to check out? (YYYY-MM-DD)"
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD (e.g., 2025-03-26)."
    
    elif st.session_state['booking_state'] == "check_out":
        try:
            check_out = date.fromisoformat(user_input)
            if check_out <= st.session_state['booking_params']['check_in']:
                return "Check-out date must be at least one day after the check-in date."
            st.session_state['booking_params']['check_out'] = check_out
            st.session_state['booking_state'] = "num_people"
            return "How many people are staying? (1-8)"
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD (e.g., 2025-03-26)."
    
    elif st.session_state['booking_state'] == "num_people":
        try:
            num_people = int(user_input)
            if num_people < 1 or num_people > 8:
                return "Number of people must be between 1 and 8."
            st.session_state['booking_params']['num_people'] = num_people
            st.session_state['booking_state'] = "rooms"
            return "How many rooms do you need? (1-5)"
        except ValueError:
            return "Please enter a valid number (e.g., 2)."
    
    elif st.session_state['booking_state'] == "rooms":
        try:
            rooms = int(user_input)
            if rooms < 1 or rooms > 5:
                return "Number of rooms must be between 1 and 5."
            st.session_state['booking_params']['rooms'] = rooms
            st.session_state['booking_state'] = "idle"
            
            # Perform hotel search
            search_results = google_hotels_client.search_hotels(
                destination=st.session_state['booking_params']['destination'],
                num_people=st.session_state['booking_params']['num_people'],
                rooms=rooms,
                check_in=st.session_state['booking_params']['check_in'],
                check_out=st.session_state['booking_params']['check_out']
            )
            
            if search_results:
                st.session_state['search_results'] = search_results
                st.session_state['show_search_results'] = True
                return "I found some hotels matching your criteria. Please check the 'Search Hotels' page for results."
            else:
                return "Sorry, I couldn't find any hotels matching your criteria. Please try different search parameters."
                
        except ValueError:
            return "Please enter a valid number (e.g., 1)."

# Payment Validation Helper
def is_expiry_valid(expiry):
    try:
        month, year = map(int, expiry.split('/'))
        current_year = date.today().year % 100
        current_month = date.today().month
        return 1 <= month <= 12 and (year > current_year or (year == current_year and month >= current_month))
    except:
        return False

def validate_search_form(destination, check_in, check_out, min_price, max_price):
    """Validate search form inputs and return list of errors"""
    errors = []
    
    if not destination:
        errors.append("Please enter a destination")
    
    if check_out <= check_in:
        errors.append("Check-out date must be after check-in date")
    
    if min_price > max_price:
        errors.append("Minimum price cannot be greater than maximum price")
    
    if min_price < 0:
        errors.append("Minimum price cannot be negative")
    
    if max_price <= 0:
        errors.append("Maximum price must be greater than 0")
    
    return errors

# Run the app
if not st.session_state['logged_in']:
    login_page()
else:
    main_app()