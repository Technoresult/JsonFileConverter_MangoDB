import os
import streamlit as st
import json
import re
from datetime import datetime
from pymongo import MongoClient
from bson.json_util import dumps
from urllib.parse import quote_plus

# Function to generate filename with date
def generate_filename(metal_type):
    today = datetime.now().strftime("%Y-%m-%d")
    return f"{metal_type[0].upper()}_{today}.json"

# Function to convert table data to JSON
def table_to_json(table_data, metal_type):
    if metal_type == "Gold":
        parts = re.findall(r'(\w+)\s+(₹\s*[\d,.]+)\s+(₹\s*[\d,.]+)\s+(₹\s*[\d,.]+)', table_data)
        
        gold_prices = []
        
        for city, price_22k, price_24k, price_18k in parts:
            try:
                city_dict = {
                    "City": city,
                    "24K Today": price_24k.strip(),
                    "22K Today": price_22k.strip(),
                    "18K Today": price_18k.strip()
                }
                gold_prices.append(city_dict)
            except ValueError:
                st.warning(f"Skipping invalid data for city: {city}, prices: {price_24k}, {price_22k}, {price_18k}")
        
        return {"gold_prices": gold_prices}
    else:
        parts = re.findall(r'(\w+)\s+(₹\s*[\d,.]+)\s+(₹\s*[\d,.]+)\s+(₹\s*[\d,.]+)', table_data)
        
        silver_rates = []
        
        for city, price_10g, price_100g, price_1kg in parts:
            try:
                city_dict = {
                    "city": city,
                    "10_gram": price_10g.strip(),
                    "100_gram": price_100g.strip(),
                    "1_kg": price_1kg.strip()
                }
                silver_rates.append(city_dict)
            except ValueError:
                st.warning(f"Skipping invalid data for city: {city}, prices: {price_10g}, {price_100g}, {price_1kg}")
        
        return {"silver_rates": silver_rates}

# Function to upload data to MongoDB Atlas
def upload_to_mongodb(json_data, metal_type):
    # Replace with your MongoDB Atlas connection details
    username = "technoresult"
    password = "Domain@202!"  # Replace with your actual password
    cluster = "goldcalculator-01.lfvxjyn.mongodb.net"
    
    # Escape username and password
    escaped_username = quote_plus(username)
    escaped_password = quote_plus(password)
    
    # Construct the connection string
    mongo_uri = f"mongodb+srv://{escaped_username}:{escaped_password}@{cluster}/?retryWrites=true&w=majority&appName=GoldCalculator-01"
    
    client = MongoClient(mongo_uri)
    db = client["your_database_name"]  # Replace with your actual database name
    collection = db[f"{metal_type.lower()}_prices"]

    # Add a timestamp to the document
    json_data["timestamp"] = datetime.utcnow()

    # Insert the document
    result = collection.insert_one(json_data)
    return result.inserted_id

# Streamlit app
st.title("Precious Metal Price Data Converter")

# Initialize session state variables
if 'json_string' not in st.session_state:
    st.session_state.json_string = ""

metal_type = st.selectbox("Select metal type:", ["Gold", "Silver"])

st.write(f"Paste your {metal_type.lower()} price data below. The format should be:")
if metal_type == "Gold":
    st.code("City ₹ 24K_price ₹ 22K_price ₹ 18K_price")
else:
    st.code("City ₹ 10gram_price ₹ 100gram_price ₹ 1kg_price")

table_data = st.text_area("Paste your data here:", height=200)

if st.button("Convert to JSON"):
    if table_data:
        json_data = table_to_json(table_data, metal_type)
        
        st.write("Converted JSON data:")
        st.json(json_data, expanded=True)
        
        st.session_state.json_string = json.dumps(json_data, indent=2, ensure_ascii=False).encode('utf-8').decode('utf-8')
        filename = generate_filename(metal_type)
        st.download_button(
            label="Download JSON",
            file_name=f"{metal_type.lower()}_prices.json",
            mime="application/json",
            data=st.session_state.json_string,
        )
    else:
        st.warning("Please paste some data before converting.")

# MongoDB upload section
st.write("Upload to MongoDB Atlas")

with st.form(key='mongodb_upload_form'):
    submit_button = st.form_submit_button(label="Upload to MongoDB Atlas")

if submit_button:
    if st.session_state.json_string:
        json_data = json.loads(st.session_state.json_string)
        try:
            inserted_id = upload_to_mongodb(json_data, metal_type)
            st.success(f"Data uploaded successfully to MongoDB Atlas! Document ID: {inserted_id}")
        except Exception as e:
            st.error(f"Failed to upload data to MongoDB Atlas. Error: {str(e)}")
    else:
        st.warning("Please convert data to JSON before uploading.")

st.write("Note: Make sure your data is in the correct format. Each city should be on a new line or separated by spaces.")

st.write("Example data:")
if metal_type == "Gold":
    example_data = """
    Chennai ₹ 7,452 ₹ 6,831 ₹ 5,596
    Mumbai ₹ 7,403 ₹ 6,786 ₹ 5,553
    Delhi ₹ 7,418 ₹ 6,800 ₹ 5,564
    Kolkata ₹ 7,403 ₹ 6,786 ₹ 5,553
    """
else:
    example_data = """
    Chennai ₹ 977.50 ₹ 9,775 ₹ 97,750 
    Mumbai ₹ 932.50 ₹ 9,325 ₹ 93,250
    Delhi ₹ 932.50 ₹ 9,325 ₹ 93,250
    Kolkata ₹ 932.50 ₹ 9,325 ₹ 93,250
    """
st.code(example_data)
