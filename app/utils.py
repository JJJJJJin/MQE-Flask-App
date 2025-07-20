import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
from . import db
from .models import Customer, CustomerAddressUpdate, Log
import requests
import time

# for geocoding debug, process bar will be shown in terminal
from tqdm import tqdm

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
REQIURED_SHEETS = ['Transactions', 'Customers', 'Products']

# Check if the uploaded file has the correct extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_file(file):
    if not allowed_file(file.filename):
        return False, f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
    
    try:
        file.seek(0)
        f = BytesIO(file.read())
        x_f = pd.ExcelFile(f, engine='openpyxl')

        if not all(sheet in x_f.sheet_names for sheet in REQIURED_SHEETS):
            return False, f"File must contain the following sheets: {', '.join(REQIURED_SHEETS)}"
        
        for s in REQIURED_SHEETS:
            if x_f.parse(s).empty:
                return False, f"Sheet '{s}' is empty. Please provide valid data."

    except Exception as e:
        print(f"Error reading file: {e}")
        return False, str(e)
    
    return True, None

# Process to analyse the uploaded file
def process_file(file):
    try:
        file.seek(0)
        filename = file.filename
        x_f = pd.ExcelFile(BytesIO(file.read()), engine='openpyxl')

        # 1. Process Customers sheet
        customers_df = x_f.parse('Customers')
        process_customers(customers_df)

        # 2. Process Transactions and Products
        transactions_df = x_f.parse('Transactions')
        products_df = x_f.parse('Products')
        
        tran_merged_df = transactions_df.merge(products_df[['product_code', 'category']], on='product_code', how='left')

        # Output 2: Total transaction amount per customer per category
        category_totals = tran_merged_df.groupby(['customer_id', 'category'])['amount'].sum().reset_index()

        # Output 3: Top customer per category
        top_customers = category_totals.sort_values(['category', 'amount'], ascending=[True, False]) \
            .groupby('category') \
            .first() \
            .reset_index()
        
        # Output 4: Rank customers by total purchase
        total_purchase = tran_merged_df.groupby('customer_id')['amount'].sum().reset_index()
        total_purchase = total_purchase.sort_values(by='amount', ascending=False)
        total_purchase['rank'] = total_purchase['amount'].rank(method='dense', ascending=False).astype(int)

        # Log the upload
        customers_count = len(customers_df)
        transactions_count = len(transactions_df)
        products_count = len(products_df)
        log = Log(
            filename=filename,
            customers_rows=customers_count,
            transactions_rows=transactions_count,
            products_rows=products_count
        )
        db.session.add(log)
        db.session.commit()

    except Exception as e:
        print(f"Error processing file: {e}")
        return None, None, None
    
    return category_totals, top_customers, total_purchase

def clean_customer_string(raw_str):
    return str(raw_str).strip().lstrip('{').rstrip('}')

def process_customers(customers_df):
    column_name = customers_df.columns[0]  # Assume first column contains the string
    geo_cache = {}

    for _, row in tqdm(customers_df.iterrows(), total=len(customers_df), desc="Geocoding Customers"):
        raw_str = clean_customer_string(row[column_name])
        parsed = parse_customer_row(raw_str)

        customer_id = parsed['customer_id']
        name = parsed['name']
        email = parsed['email']
        dob = parsed['dob']
        address = parsed['address']
        phone = '' # leave this for future use maybe
        created_date = parsed['created_date']

        # Geocode current address
        new_lat, new_lon = geocode_address(address, cache=geo_cache)

        c = Customer.query.filter_by(customer_id=customer_id).first()
        if not c:
            # New customer: save address + geolocation
            c = Customer(
                customer_id=customer_id,
                name=name,
                email=email,
                dob=dob,
                address=address,
                phone=phone,
                created_at=created_date,
                latitude=new_lat,
                longitude=new_lon
            )
            db.session.add(c)
        else:
            # Existing customer: check for address change
            if c.address != address:
                # Log address + lat/lon change
                address_update = CustomerAddressUpdate(
                    customer_id=customer_id,
                    old_address=c.address,
                    new_address=address,
                    old_latitude=c.latitude,
                    old_longitude=c.longitude,
                    new_latitude=new_lat,
                    new_longitude=new_lon
                )
                db.session.add(address_update)

                # Update current customer data
                c.address = address
                c.latitude = new_lat
                c.longitude = new_lon

    db.session.commit()

# Helper function to parse one customer row
def parse_customer_row(row):
    ps = row.split('_', 4)
    if len(ps) != 5:
        raise ValueError(f"Invalid customer row format: {row}")
    
    customer_id = ps[0].strip()
    name = ps[1].strip()
    email = ps[2].strip()
    dob = pd.to_datetime(ps[3].strip(), errors='coerce').date()

    address_and_time = ps[4].rsplit('_', 1)
    if len(address_and_time) != 2:
        raise ValueError(f"Invalid address/created_date format: {ps[4]}")

    address = address_and_time[0].strip()
    created_date = datetime(1899, 12, 30) + timedelta(days=float(address_and_time[1]))

    return {
        'customer_id': customer_id,
        'name': name,
        'email': email,
        'dob': dob,
        'address': address,
        'created_date': created_date
    }

# Geocode address using Nominatim api
def geocode_address(address, cache={}):
    if address in cache:
        return cache[address]

    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'q': address,
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'FlaskApp/1.0 (ddd739305175@gmail.com)'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()

        if data:
            lat, lon = float(data[0]['lat']), float(data[0]['lon'])
            cache[address] = (lat, lon)
            time.sleep(1)  # Respect rate limit
            return lat, lon
    except Exception as e:
        print(f"Geocoding error for {address}: {e}")

    cache[address] = (None, None)
    return None, None

# Generate Excel output from processed data
def generate_output_excel(category_totals, top_customers, total_purchase):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        category_totals.to_excel(writer, index=False, sheet_name='Category_Totals')
        top_customers.to_excel(writer, index=False, sheet_name='Top_Customers')
        total_purchase.to_excel(writer, index=False, sheet_name='Customer_Rank')

    output.seek(0)
    return output