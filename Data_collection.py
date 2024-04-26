import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import pickle
import mysql.connector
from sqlalchemy import create_engine

def main():
    global df

    # Create an empty DataFrame to store the data
    df = pd.DataFrame(columns=['ID','Year', 'Brand', 'Model', 'Mileage','Bodystyle','Exterior Color','Interior Color',\
                            'Drivetrain','MPG', 'Fuel Type','Transmission', 'Engine',  'Price'])
    
    # Getting data from Cars.com by using Virginia zip codes
    page = 50
    zips = [20147, 20155, 22030, 22193, 22407, 22554, 22630, 23112, 23223, 23322,\
            23464, 23666, 23805, 24015, 24401, 24501]
    loop_url(page, zips)


# Extract Year 
def extract_year(info):
    pattern = r'"model_year":"(.*?)"'
    matches = re.search(pattern, str(info))

    if matches:
        year = matches.group(1)
        return int(year)
    else:
        return None


# Extract Brand 
def extract_brand(info):
    pattern = r'"make":"(.*?)"'
    matches = re.search(pattern, str(info))

    if matches:
        brand = matches.group(1)
        return brand.lower()
    else:
        return None

# Extract Model 
def extract_model(info):  
    pattern = r'"model":"(.*?)"'
    matches = re.search(pattern, str(info))

    if matches:
        model = matches.group(1)
        return model.lower()
    else:
        return None

# Extract Bodystyle        
def extract_bodystyle(info):
    pattern = r'"bodystyle":"(.*?)"'
    matches = re.search(pattern, str(info))

    if matches:
        bodystyle = matches.group(1)
        return bodystyle.lower()
    else:
        return None

# Extract Price 
def extract_price(info):
    price_info = info.find('span', class_='primary-price')
    price = price_info.text.strip() if price_info else None
    price = re.findall(r'\d+', price)
    price = ''.join(price)
    return int(price)


# Extract Mileage 
def extract_mileage(info):
    mileage_info = info.find('div', class_='mileage')
    mileage = mileage_info.text.strip() if mileage_info else None
    mileage = re.findall(r'\d+', mileage)
    mileage = ''.join(mileage)
    return int(mileage)

# Function to extract car details from a given HTML content
def extract_details(info):
    exterior_color = None
    interior_color = None
    drivetrain = None
    mpg = None
    fuel_type = None
    transmission = None
    engine = None
    detailed_link = None
    
    # Find all links in the HTML content
    all_links = info.find_all('a', href=True)
    
    # Extract detailed links related to vehicle details
    detailed_links = [link['href'] for link in all_links if "vehicledetail" in link['href']][0]
    
    # Construct detailed link
    link = 'https://www.cars.com' + str(detailed_links)
    
    # Get the response from the detailed link
    response = requests.get(link)
        
    # Parse the response HTML content
    sub_soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all HTML elements containing car information
    sub_elements = sub_soup.find_all('dl', class_='fancy-description-list')

    # Loop through each HTML element to extract relevant information
    for dl_element in sub_elements:
        try:
            # Find dt and dd elements within the current dl element
            dt_elements = dl_element.find_all('dt', limit=7)
            dd_elements = dl_element.find_all('dd', limit=7)
            
            # Extract exterior color
            if dt_elements and dt_elements[0].text.strip() == 'Exterior color':
                exterior_color = dd_elements[0].text.strip()
                exterior_color = exterior_color.lower() if exterior_color is not None and exterior_color != "-" else None
                
            # Extract interior color
            if dt_elements and dt_elements[1].text.strip() == 'Interior color':
                interior_color = dd_elements[1].text.strip()
                interior_color = interior_color.lower() if interior_color is not None and interior_color != "-" else None
    
            # Extract drivetrain
            if dt_elements and dt_elements[2].text.strip() == 'Drivetrain':
                drivetrain = dd_elements[2].text.strip().split()[0]
                drivetrain = drivetrain.lower() if drivetrain is not None and drivetrain != "-" else None
            
            # Extract MPG
            if dt_elements and dt_elements[3].text.strip() == 'MPG':
                mpg = dd_elements[3].text.strip().split()[0]
                mpg = mpg if mpg is not None and mpg != "-" else None
            
            # Extract Fuel type
            if dt_elements and dt_elements[4].text.strip() == 'Fuel type':
                fuel_type = dd_elements[4].text.strip()
                fuel_type = fuel_type.lower() if fuel_type is not None and fuel_type != "-" else None
    
            # Extract Transmission
            if dt_elements and dt_elements[5].text.strip() == 'Transmission':
                transmission = dd_elements[5].text.strip()
                transmission = transmission.lower() if transmission is not None and transmission != "-" else None
    
            # Extract Engine
            if dt_elements and dt_elements[6].text.strip() == 'Engine':
                engine = dd_elements[6].text.strip()
                engine = engine.lower() if engine is not None and engine != "-" else None
        
        except:
            pass

    # Return extracted car details
    return exterior_color, interior_color, drivetrain, mpg, fuel_type, transmission, engine


def load_database(df):
    # Load password from pickle file
    with open('./Flask/pickle/pw.pkl', 'rb') as f:
        pw = pickle.load(f)
        
    # Load host from pickle file
    with open('./Flask/pickle/host.pkl', 'rb') as f:
        host = pickle.load(f)
    
    # Create engine to connect to MySQL database
    engine = create_engine("mysql+mysqlconnector://root:" + pw + "@" + host + "/usedcar", pool_pre_ping=True)
    
    # Write DataFrame to MySQL database table named "usedcar"
    df.to_sql(name="usedcar", con=engine, if_exists='append')
    
    # Reset DataFrame to None after writing to database
    df = None


def loop_url(pages, zips):
    try:
        for zip in zips:
            print(f"Start to collect the data from {zip} area")
            for page in range(1, int(pages)+1):     
                url = 'https://www.cars.com/shopping/results/?dealer_id=&keyword=&list_price_max\
                =&list_price_min=&makes[]=&maximum_distance=500&mileage_max=&monthly_payment=&page='+str(page)+\
                '&page_size=20&sort=best_match_desc&stock_type=used&year_max=&year_min=&zip='+str(zip)
        
                # Send a request to a webpage and receive a response.
                response = requests.get(url)
                
                # Parse the response.
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find the HTML element that contains the car information.
                car_elements = soup.find_all('div', class_='vehicle-card')
                scrape_car_info(car_elements)
                
            load_database(df)
            print(f"Upload the data from {zip} to MySQL")
            
    except:
        pass
    
    
def scrape_car_info(car_elements):
    global df

    try:
        for info in car_elements:  
    
            year = extract_year(info)
            brand = extract_brand(info)
            model = extract_model(info)
            price = extract_price(info)
            mileage = extract_mileage(info)
            bodystyle = extract_bodystyle(info)
            exterior_color, interior_color, drivetrain, mpg, fuel_type, transmission, engine = extract_details(info)
            
            # Generating unique ID for each car
            id = str(year)+brand+model+str(mileage)
            
            # Removing spaces from ID
            id = id.replace(" ","")
            
            
            # Create a DataFrame to store the data you want to append
            data_to_append = pd.DataFrame({
                'ID': [id],
                'Year': [year],
                'Brand': [brand],
                'Model': [model],
                'Mileage': [mileage],
                'Bodystyle': [bodystyle],
                'Exterior Color': [exterior_color],
                'Interior Color': [interior_color],
                'Drivetrain': [drivetrain],
                'MPG': [mpg],
                'Fuel Type': [fuel_type],
                'Transmission': [transmission],
                'Engine': [engine],
                'Price': [price]
            })

            # Appending the new data to the main DataFrame
            df = pd.concat([df, data_to_append], ignore_index=True)   
        return df
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    

if __name__ == "__main__":
    main()
    print("Done")