



# In[]:

# The assignment starts by webscraping the website of the Finnish parliament. 
# The mandate of the actual parliament started in 2023 and will end in 2027. After obtaining the links for every personal webpage 
# of each parliament, we will scrape the main information and create a dataset to compute summary statistics with.
# After that we will work with geographical data with regards to Finland and we will also conduct the text analysis of 
# the plenary sessionsâ€™ press releases of the parliament that are available on the website.
# Finally, we will compare the program of the two main political parties through text analysis.

# Throughout the code, we will often import libraries, csv files and packages more than once in case there is the need (or desire) to run only a specific section of the code

#Please note that the current MPs are being updated due to the european elections, so the the website could temporarily display more than 200 MPs


# It's a website that uses javascript
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Driver of Selenium
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# URL of the webpage with the MPs
url = "https://www.eduskunta.fi/EN/kansanedustajat/nykyiset_kansanedustajat/Pages/default.aspx"

# Open the page
driver.get(url)

# Wait for the page to be loaded
try:
    # wait 20 second for the elements to be there
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.clearfix"))
    )
except Exception as e:
    print(f"Error during the loading of the page: {e}")
    driver.quit()
    exit()

# Now we get the content of the webpage
html = driver.page_source

# Close the driver
driver.quit()

# Now we use beautiful soup
soup = BeautifulSoup(html, 'html.parser')

# Obtain each link that is in the tag <li>with the class clearfix
links = set()  # use set to avoid duplicates
exclude_link = "https://www.eduskunta.fi/EN/kansanedustajat/Pages/807.aspx"
for li in soup.find_all('li', class_='clearfix'):
    a_tag = li.find('a', href=True)
    if a_tag and a_tag['href'] != exclude_link:
        links.add(a_tag['href'])

# Print links obtained
for link in links:
    print("Extracted link:", link)

# In[function for webscraping]: 
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import re

# Create a session with retry logic
session = requests.Session()
retry = Retry(
    total=5,  # Total number of retries
    backoff_factor=1,  # A backoff factor to apply between attempts
    status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP status codes
    allowed_methods=["HEAD", "GET", "OPTIONS"]  # Retry for these methods
)
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)
session.mount("http://", adapter)

def get_info(link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com',
        'Connection': 'keep-alive'
    }
    
    try:
        webpage = session.get(link, headers=headers, timeout=30, allow_redirects=True)
        webpage.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Request error for {link}: {e}")
        return None

    page_content = BeautifulSoup(webpage.text, 'html.parser')

    # Name and Surname
    try:
        name_surname_element = page_content.find("div", id="ctl00_PlaceHolderMain_MOPInformation_MOPWrapper", class_="current-mop").find("h1")
        name_surname = name_surname_element.text.strip() if name_surname_element else "NA"
        name_surname = re.sub(r'\s+', ' ', name_surname)  # Clean extra whitespace and newlines
    except AttributeError:
        name_surname = "NA"
    
    # Parliamentary Group
    try:
        parliamentary_group = page_content.find("div", id="ctl00_PlaceHolderMain_MOPInformation_MOPWrapper", class_="current-mop").find("p").text.strip()
        if not parliamentary_group:
            parliamentary_group = "NA"
    except AttributeError:
        parliamentary_group = "NA"
    
    # Electoral District
    try:
        electoral_district_label = page_content.find('h2', string=re.compile('Electoral district:'))
        if electoral_district_label:
            district_name_and_date = electoral_district_label.find_next('div', class_='mop-info-value').get_text(strip=True)
            electoral_district = ' '.join(district_name_and_date.split()[:-1]).replace("Electoral District of", "").strip()
        else:
            electoral_district = "NA"
    except AttributeError:
        electoral_district = "NA"

    # Date and Place of Birth
    try:
        date_and_place_of_birth_label_div = page_content.find('div', class_='mop-title-label', string=re.compile('Date and place of birth:'))
        if date_and_place_of_birth_label_div:
            info_date_and_place_of_birth_div = date_and_place_of_birth_label_div.find_next('div', class_='mop-info-value')
            birth_info = info_date_and_place_of_birth_div.find('li').get_text(strip=True)
            match = re.match(r'(\d{4})\s+(.*)', birth_info)
            if match:
                birth_year = match.group(1)
                birth_place = match.group(2)
                age = 2024 - int(birth_year)
                
            # If there is only the birth year    
            elif re.match(r'^\d{4}$', birth_info):
                birth_year = birth_info
                birth_place = "NA"
                age = 2024 - int(birth_year)
                
            # If there is only the birth place    
            elif re.match(r'^[A-Za-z\s]+$', birth_info):
                birth_year = "NA"
                birth_place = birth_info
                age = "NA"
                                     
            else:
                birth_year, birth_place, age = "NA", "NA", "NA"
        else:
            birth_year, birth_place, age = "NA", "NA", "NA"
    except AttributeError:
        birth_year, birth_place, age = "NA", "NA", "NA"

    # Education
    try:
        education_label = page_content.find('div', class_='mop-title-label', string=re.compile('Education:'))
        if education_label:
            education = education_label.find_next('div', class_='mop-info-value').get_text(strip=True)
        else:
            # If the first selector doesn't find the element, try the second selector
            education_element = page_content.find('h2', string=re.compile('Profession / Title:'))
            if education_element:
                education = education_element.find_next('div', class_='mop-info-value').get_text(strip=True)
            else:
                education = "NA"
    except AttributeError:
        education = "NA"

    return [link, name_surname, parliamentary_group, electoral_district, age, birth_place, education]

# Test the function
link1 = 'https://www.eduskunta.fi/EN/kansanedustajat/Pages/1385.aspx'
result = get_info(link1)
print(result)


# In[]
information_collected = list ()
# SIMPLER ALTERNATIVE
# for link in links:
    
#     information_collected.append(get_info(link))
    
#     #sleep so we don't overwhelm the server
#     sleep(5)

# Using tqdm to show progress in real time - otherwise we get anxious, classic gen z :(
from tqdm import tqdm
for link in tqdm(links, desc="Scraping links", unit="link"):
    info = get_info(link)
    if info:
        information_collected.append(info)
# In[step ]
# Now we can print or save the collected information
print(information_collected)

# In[]:

import pandas as pd    
dataset = pd.DataFrame(information_collected, columns = ['url', 'name', 'Parliamentary Group', 'Electoral District', 'Age', 'Birth place', 'Education'])
print(dataset)

# In[]:
 # Define the function to classify education level
def classify_education_level(education):
    tertiary_keywords = ["tertiary", "veterinary","university", "phd", "degree", "master", "bachelor", "law", "doctor of philosophy", "licentiate", "doctoral research", "professor", "architect"]
    secondary_keywords = ["high school", "secondary", "social sciences student", "vocational"]
    # Vocational studies can be categorized as either secondary or tertiary, depending on the specific course
    # For simplicity, we assume that all vocational studies are "secondary education"
    education = education.lower()  # Convert to lower case to make the search case-insensitive
    
    if any(keyword in education for keyword in tertiary_keywords):
        return "tertiary"
    elif any(keyword in education for keyword in secondary_keywords):
        return "secondary"
    else:
        return "secondary"  # We assume that everyone has at least a secondary education, even if it is not specified. 
    # This is the case if we cannot deduce the level of education from what is written on the website
# Apply the function to create a new column 'education level'
dataset['education level'] = dataset['Education'].apply(classify_education_level)

print(dataset)

# In[WE DONâ€™T RUN THIS PART, IT IS ONLY TO SHOW HOW TO WORK WITH MACHINE LEARNING METHODS]:
# Now we want to implement a machine learning method to predict the gender based on names. 
# As we have studied during class, there are several approaches to achieve this:

#     Pre-trained Models: Use a pre-trained model that has been trained on a large dataset of names and their corresponding genders.
#     Rule-Based Methods: Use a database or API with a large collection of names and their genders.
#     Custom Machine Learning Model: Train your own model using a dataset of names and genders.

# Given that training a custom machine learning model requires a significant amount of data and preprocessing, the simplest and most efficient approach for this task is to use a pre-trained model.

#!pip install genderize
# In[]
# Unfortunately this method allows us to only request 100 names per day, so we will run the code in two days :/
# CELL FOR THE FIRST 100 NAMES

# from genderize import Genderize, GenderizeException
# import time

# # Predict gender using the genderize package in chunks
# genderize = Genderize()

# # Include  API key
# api_key = '2a097762d12087e97a3cc1c546bda54c'

# # Initialize Genderize with the API key
# genderize = Genderize(api_key=api_key)




# # Extract first names for gender prediction
# first_names = dataset['name'].apply(lambda x: x.split()[0] if x != "NA" else "NA")


# # Get only the first 100 names 

# first_100_names = first_names[:100]
# print(first_100_names)
# # Predict gender using the genderize package
# genderize = Genderize()
# gender_predictions = genderize.get(first_100_names.tolist())
# genders = [pred['gender'] if pred['gender'] is not None else 'NA' for pred in gender_predictions]

# # Add the gender predictions to the dataset
# dataset['Gender'] = genders


# print(dataset)
# # In[] #SECOND PART OF GENDER PREDICTION
# # Unfortunately this method allows us to only request 100 names per day, so we will run the code in two days :/
# # CELL FOR THE second 100 NAMES

# from genderize import Genderize, GenderizeException
# import time

# # Predict gender using the genderize package in chunks
# genderize = Genderize()

# # Include  API key
# api_key = '2a097762d12087e97a3cc1c546bda54c'

# # Initialize Genderize with the API key
# genderize = Genderize(api_key=api_key)




# # Extract first names for gender prediction
# first_names = dataset['name'].apply(lambda x: x.split()[0] if x != "NA" else "NA")


# # Get only the second 100 names 

# second_100_names = first_names[100:200]
# print(second_100_names)
# # Predict gender using the genderize package
# genderize = Genderize()
# gender_predictions = genderize.get(second_100_names.tolist())
# genders = [pred['gender'] if pred['gender'] is not None else 'NA' for pred in gender_predictions]

# # Add the gender predictions to the dataset
# dataset['Gender'] = genders


# print(dataset)


# In[]:
pip install gender-guesser
# In[]
from gender_guesser.detector import Detector



# Extract first names for gender prediction
first_names = dataset['name'].apply(lambda x: x.split()[0] if x != "NA" else "NA")
print(first_names)

# Initialize the gender detector
detector = Detector()
# It's possible that the gender-guesser package might not recognize some names, 
# especially if they are specific to a certain language or culture and 
# are not well-represented in its database. 
# Gender-guesser works reasonably well for many common names but 
# might not be as effective for names from languages or cultures that are underrepresented in the dataset it was trained on.
#  Hence we define a custom dictionary for Finnish names


finnish_names_gender = {
    'Aino': 'female',
    'Aino-Kaisa': 'female',
    'Anna-Kaisa': 'female',
    'Anna-Kristiina': 'female',
    'Anna-Maja': 'female',
    'Anni': 'female',
    'Eeva-Johanna': 'female',
    'Emilia': 'female',
    'Fatim': 'female',
    'Hanna-Leena': 'female',
    'Helmi': 'female',
    'Ilona': 'female',
    'Janne': 'male',
    'Jenna': 'female',
    'Jessi': 'female',
    'Jussi': 'male',
    'Kaisa': 'female',
    'Kerttu': 'female',
    'Kim': 'male',
    'Leena': 'female',
    'Li': 'female',
    'Mari': 'female',
    'Mari-Leena': 'female',
    'Maria': 'female',
    'Minna': 'female',
    'Oili': 'female',
    'PÃ¤ivi': 'female',
    'Pihla': 'female',
    'Pinja': 'female',
    'Rami': 'male',
    'Riitta': 'female',
    'Saara': 'female',
    'Saara-Sofia': 'female',
    'Saku': 'male',
    'Sanna': 'female',
    'Sari': 'female',
    'Sheikki': 'male',
    'Sinuhe': 'male',
    'Taina': 'female',
    'Tiina': 'female'

}





# Predict gender using the gender_guesser package and the custom dictionary
def predict_gender(name):
    if name == "NA":
        return "NA"
    # Check in the custom dictionary first
    if name in finnish_names_gender:
        return finnish_names_gender[name]
    # Fall back to gender_guesser if not found in the dictionary
    gender = detector.get_gender(name)
    if gender in ["male", "female"]:
        return gender
    else:
        return "NA"


# Apply the function to create a new column 'Gender'
dataset['Gender'] = first_names.apply(predict_gender)


# In[]:
# Save the DataFrame as a CSV file
dataset.to_csv('parliamentary_info.csv', index=False)
print("CSV file has been saved successfully.")



# In[STEP 1 of summary statistics]

# START OF SUMMARY STATISTICS + GEOGRAPHICAL DATA

import pandas as pd

dataset = pd.read_csv('parliamentary_info.csv')

# Look at the data for 10 random MPs
print(dataset.sample(n=10))

# We want to create some summary statistics on:
# 
# - Gender composition of the chamber and parties
# - Age at the chamber level vs. party level
# - Representation of Italy at the regional level
# - Education level at the party level
 


## Gender Composition
# 
# Let's start by studying the gender composition of the chamber, and of each of the parties.
# `groupby` combined with `mean` will give us what we want provided we turn the column gender from `str` to `numeric`



# In[STEP 2]

#
# Make up this numeric gender variable
dataset['Share women'] = dataset['Gender'].apply(lambda x: 1 if x == 'female' else 0)

# Get the average at chamber level, and the average by party
chamber = dataset['Share women'].mean()
by_party = dataset.groupby('Parliamentary Group')['Share women'].mean().reset_index()

# Add a row to by_party
chamber_level = pd.DataFrame([['chamber', chamber]], columns=['Parliamentary Group', 'Share women'])
dataset_gender = pd.concat([chamber_level, by_party], axis=0)

dataset_gender = dataset_gender.set_index('Parliamentary Group')
print(dataset_gender.head())

# Let's plot the information

import matplotlib.pyplot as plt

dataset_gender = dataset_gender.sort_values(by='Share women', ascending=False)
# Plotting the bar chart
fig, ax = plt.subplots(figsize=(14, 8))
dataset_gender.plot(kind='bar', legend=False, ax=ax)
plt.title('Gender representation by Party')
plt.xlabel('Party')
plt.ylabel('Share of Women (%)')
plt.xticks(rotation=45, ha='right')  # Rotate labels and align them to the right for better readability
plt.tight_layout()

# Show the plot
plt.show()

# We see that Liike Nyt-Movement's Parliamentary Group and Parliamentary Group Timo Vornanen have no women in their party! However, those parties are composed by only one person.

# In[]:
    

# ## Age of the chamber
# 
# Let's compute the same statistics by age. Start by creating an age column

# In[STEP 3]:


dataset.columns




# Get the average at chamber level, and the average by party
chamber = dataset['Age'].mean()
by_party = dataset.groupby('Parliamentary Group')['Age'].mean().reset_index()

# Add a row to by_party
chamber_level = pd.DataFrame([['chamber', chamber]], columns = ['Parliamentary Group', 'Age'])
dataset_age = pd.concat([chamber_level, by_party], axis = 0)


# In[STEP 4]:


dataset_age = dataset_age.set_index('Parliamentary Group')
print(dataset_age.head())



# In[STEP 5]
# Plotting the bar chart
fig, ax = plt.subplots(figsize=(14, 8))
dataset_age.plot(kind='bar', legend=False, ax=ax)
plt.title('Average age by Party')
plt.xlabel('Party')
plt.ylabel('Average age')
plt.xticks(rotation=45, ha='right')  # Rotate labels and align them to the right for better readability
plt.tight_layout()

# Show the plot
plt.show()

# In[]:

# ### Ready to look at education and party membership

# In[STEP 6]:


# We want to know the shares for each party - first we need the total number in each party
dataset['party_size'] = dataset.groupby('Parliamentary Group').transform("size")

# And now we summarize by party/education level
dataset['composition'] = 100*dataset.groupby(['Parliamentary Group', 'education level']).transform("size")/dataset['party_size']

# Get the composition
df_plot = dataset[['Parliamentary Group', 'education level', 'composition']].drop_duplicates()

 
import matplotlib.pyplot as plt
# Pivoting the data for plotting
df_plot_pivot = df_plot.pivot_table(values='composition', index='Parliamentary Group', columns='education level', fill_value=0)

# Sorting the pivot table by 'Secondary' column in descending order
df_plot_pivot = df_plot_pivot.sort_values(by='secondary', ascending=False)

# Plotting the stacked bar chart
df_plot_pivot.plot(kind='bar', stacked=True, figsize=(12, 8))
plt.title('Composition of Education Level by Party')
plt.xlabel('Party')
plt.ylabel('Composition (%)')
plt.legend(title='Education Level')
plt.xticks(rotation=45, ha = 'right')  # Rotate labels for better readability and align them to the right
plt.tight_layout()

# Show the plot
plt.show() 

    
    
    
# In[STEP 7]    

# ## Now we can do some summary statistics with the birthplace of the MPs. 
# However, before starting we need show and demonstrate that we can work with geographical data
# 


dataset['Birth place'].sample(n=2)

# In[STEP 8]
# GEOSPATIAL EXERCISE
# Work with geospatial data 
# This dataset is from :https://simplemaps.com/data/fi-cities 
# We are going to use this dataset to demonstrate our  skills in doing analytical work 
# with geospatial analysis. The dataset consists of more than 400 cities in Finland, 
# and it includes essential information such as latitude, longitude, region, and population for each city.
# We are going to use this dataset also for the representation of the areas of Finland in the parliament. 
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon
import folium


import matplotlib.pyplot as plt

data=pd.read_csv('fi_cities.csv')


# Renaming the columns
data.rename(columns = {'lat':'latitude', 'lng':'longitude'}, inplace = True)




data.columns



data.info()



# Display the first five rows of the dataset
data.head(5)


# In[STEP 9]
# FIVE LARGEST CITIES - with the following lines of code we can see which are the largest cities in Finland
# Sort the DataFrame by population in descending order
df_sorted = data.sort_values('population', ascending=False)

print("Five largest  Largest Cities in Finland:")
# Get the top 5 largest cities
bigcities = df_sorted.head(5)


bigcities


# In[STEP 10]:
    
import folium

# Create the map
map1 = folium.Map(location=[61.9241, 25.7482], zoom_start=6, prefer_canvas=True)

# Add markers
map1.add_child(folium.Marker(location=[60.1708, 24.9375], popup='Helsinki'))
map1.add_child(folium.Marker(location=[61.4981, 23.7600], popup='Tampere'))
map1.add_child(folium.Marker(location=[60.2056, 24.6556], popup='Espoo'))
map1.add_child(folium.Marker(location=[60.4500, 22.2667], popup='Turku'))
map1.add_child(folium.Marker(location=[60.2944, 25.0403], popup='Vantaa'))

# Add a polyline
folium.PolyLine(locations=[
    (60.1708, 24.9375), 
    (61.4981, 23.7600),
    (60.2056, 24.6556), 
    (60.4500, 22.2667),
    (60.2944, 25.0403)
], weight=5, color="pink", line_opacity=0.5).add_to(map1) 

# Save the map to an HTML file
map1.save('map.html')

# In the folder of the current directiory, double-click on map.html to open it in your default web browser

# In[STEP 11]
#CREATE A GEODATAFRAME



# Create a geometry column
data['coordinates'] = list(zip(data.longitude, data.latitude))

# Make geometry column Shapely objects
data['coordinates'] = data['coordinates'].apply(Point)

# Cast as GeoDataFrame
gdf = gpd.GeoDataFrame(data, geometry='coordinates')
# Display Geodataframe
gdf

# In[STEP 12]

fig, ax = plt.subplots()
gdf.plot(ax=ax)
ax.set_title('Cities in Finland')
ax.set_facecolor('black')
plt.show()

# In[STEP 13]
# Geopandas is a library that can read shapefiles.
# With Geopandas, we can transform these shapefiles into interactive maps that we can plot
# and explore.
# Shapefiles are files that contain geographic information about features 
# like countries, cities, or rivers. Geopandas can read these files and turn them into maps
# that we can plot on. We downloaded the shapefile from : https://www.eea.europa.eu/data-and-maps/data/eea-reference-grids-2/gis-files/finland-shapefile

fiMap = gpd.read_file('Finland_shapefile/fi_1km.shp')
fiMap.plot()

#This part can take up to 5 minutes

# In[STEP 14]

# In Geopandas, the epsg parameter refers to the EPSG code, 
# which stands for European Petroleum Survey Group. The EPSG code is a unique identifier 
# assigned to a specific coordinate reference system (CRS). This CRS provides accurate 
# and consistent spatial reference for Finland, enabling precise mapping and spatial 
# analysis within the country.
# We found EPSG code corresponding to the CRS from this pg :https://epsg.io/?q=Finland%20kind%3APROJCRS



crs = {'init':'EPSG:4326'}
geometry = [Point(xy) for xy in zip(data['longitude'], data['latitude'])]
geo_df = gpd.GeoDataFrame(data, 
                          crs = crs, 
                          geometry = geometry)

fig, ax = plt.subplots(figsize = (10,10))
fiMap.to_crs(epsg=4326).plot(ax=ax, color='lightgrey')
geo_df.plot(ax=ax)
ax.set_title('cities in Finland')




# In[STEP 15]
# Now we go back to our dataset of the member of the parliament to compute further statistics
!pip install rapidfuzz


# In[Further exercise with Geopanda, with data from previous classes. We found them on Virtuale]

import geopandas as gpd

""
dataset = gpd.read_file(r"cities")


# We can very easily plot this kind of data, `geopandas` and `matplotlib` take care of everything for us

dataset


# We can filter for Finlandâ€™s cities

# In[a]:


fin_data = dataset.loc[dataset['ADM0NAME'] == 'Finland',:].copy()

# In[b]:

import matplotlib.pyplot as plt

# Create the plot
fig, ax = plt.subplots()
fin_data.plot(ax=ax, marker='o', color='red', markersize=5)

# Add labels for each point
for x, y, label in zip(fin_data.geometry.x, fin_data.geometry.y, fin_data['NAME']):
    ax.annotate(label, xy=(x, y), xytext=(3, 3), textcoords='offset points', fontsize=8)

# Customize the plot (optional)
ax.set_title('Plot of Cities')
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')

# Show the plot
plt.show()


# Then, in terms of visualization, you can create any column you'd like, and represent it using plotting

# In[c]

import numpy as np
fin_data['size_dot'] = fin_data['POP_MAX']/10000

# In[d]:
    
    
# We can scale the size of the dot depending on the population

# Create the plot
fig, ax = plt.subplots()
fin_data.plot(ax=ax, marker='o', color='red', markersize=fin_data['size_dot'])


# Add labels for each point
for x, y, label, size in zip(fin_data.geometry.x, fin_data.geometry.y, fin_data['NAME'], fin_data['size_dot']):
    ax.annotate(label, xy=(x, y), xytext=(3, 3), textcoords='offset points')

# Customize the plot (optional)
ax.set_title('Plot of Cities')
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')

# Show the plot
plt.show()


# In[e]:

# Now we can overlap the city with the finland borders to have a better map
import geopandas as gpd
import matplotlib.pyplot as plt

# Load the cities dataset
dataset = gpd.read_file("cities")

# Filter for Finnish cities
fin_data = dataset.loc[dataset['ADM0NAME'] == 'Finland', :].copy()

# Load the NUTS2 regions shapefile and filter for Finland
nuts2 = gpd.read_file("NUTS_RG_20M_2021_4326.geojson")
nuts2 = nuts2[nuts2['NUTS_ID'].str.startswith('FI')]

# Ensure the CRS is correct
nuts2.crs = 'EPSG:4326'

# Calculate size of dots based on population
fin_data['size_dot'] = fin_data['POP_MAX'] / 10000

# Create the plot
fig, ax = plt.subplots(figsize=(10, 10))

# Plot the NUTS2 borders
nuts2.plot(ax=ax, color='none', edgecolor='black', linewidth=1)

# Plot the cities
fin_data.plot(ax=ax, marker='o', color='red', markersize=fin_data['size_dot'])

# Add labels for each point
for x, y, label in zip(fin_data.geometry.x, fin_data.geometry.y, fin_data['NAME']):
    ax.annotate(label, xy=(x, y), xytext=(3, 3), textcoords='offset points', fontsize=8)

# Customize the plot 
ax.set_title('Plot of Cities with Finland Borders')
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')

# Show the plot
plt.show()






# In[f]: we will see how the CRS matter
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# Load the NUTS2 regions shapefile (large areas)
# The division in NUTS 2 level of Finland implies a division in 5 main areas: 
    # West Finland
    # Helsinki-Uusimaa
    # South Finland
    # North & East Finland
    # Ã…land (smaller island on the left low corner)
# nuts2 = gpd.read_file("NUTS_RG_20M_2021_4326.geojson")
# nuts2 = nuts2[nuts2['NUTS_ID'].str.startswith('FI')]

# # Specify the crs
# nuts2.crs = 'EPSG:4326'
# print(nuts2)

# In[g]:
    
# Plot the NUTS2 regions of Finland
fig, ax = plt.subplots(1, 2, figsize=(18, 6))

nuts22 = nuts2.to_crs("+proj=laea +x_0=0 +y_0=0 +lon_0=0 +lat_0=0")

# Plot original data
nuts2.plot(ax=ax[0], color='blue', markersize=1, zorder=1)
ax[0].set_title("Original CRS: EPSG:4326")

# Plot reprojected data
nuts22.plot(ax=ax[1], color='blue', markersize=1, zorder=1)
ax[1].set_title("Reprojected CRS: LAEA")

plt.show()

# In[STEP 16]

# Load the GDP per capita data that we have already used during classes (found on
# Virtuale)
gdp_per_capita = pd.read_csv("gdp_per_capita.csv")
print(gdp_per_capita)

# Compute the GDP per capita deviation
gdp_per_capita['deviation'] = gdp_per_capita['gdp_per_cap'] / gdp_per_capita['weighted_avg_gdp_per_cap']

# Merge the datasets
to_plot = pd.merge(nuts2, gdp_per_capita, how='left', left_on='NUTS_ID', right_on='geo')

# Create a color map for the plot
cmap = plt.get_cmap('coolwarm')
norm = mcolors.TwoSlopeNorm(vmin=to_plot['deviation'].min(), vcenter=1, vmax=to_plot['deviation'].max())

# Create the plot
fig, ax = plt.subplots(1, 1, figsize=(12, 8))
to_plot.plot(column='deviation', cmap=cmap, norm=norm, linewidth=0.8, edgecolor='black', ax=ax)

# Add a colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])  # Set the array to empty as the data is already in the plot
cbar = plt.colorbar(sm, ax=ax)

# Customize the plot (optional)
ax.set_title('Deviation of GDP per capita by Region (Finland)', fontsize=15)
ax.set_axis_off()

# Show the plot
plt.show()


# Optionally: Dissolve polygons to get the borders of Finland
finland_borders = nuts2.dissolve(by='CNTR_CODE')
finland_borders.boundary.plot(ax=ax, edgecolor='black', linewidth=2)
plt.show()
# Of course the richest region is the one of the capital
# In[]
# 
# 
# - Then we want to underline the borders of the country, so we take the boundaries of the polygons

# In[STEP 17]:


countries = to_plot[['country', 'geometry']].dissolve(by='country')
countries['geometry'] = countries.boundary


# We can now overlay the two plots to better distinguish country borders

# In[STEP 18]:


# Create the plot
fig, ax = plt.subplots(1, 1, figsize=(12, 8))

# Plot the GeoDataFrame
to_plot.plot(column='deviation', cmap=cmap, norm=norm, linewidth=0.8, edgecolor='black', ax=ax, zorder = 1)
countries.plot(ax=ax, color='black', markersize=1, zorder = 2)
# Add a colorbar
# Add a colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])  # Set the array to empty as the data is already in the plot
cbar = plt.colorbar(sm, ax=ax)

# Customize the plot 
ax.set_title('Deviation of GDP per capita by Region', fontsize=15)
ax.set_axis_off()

# Show the plot
plt.show()

#cl, the richest region is the one of the capital

# In[STEP 19]:
    
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from shapely.geometry import Point
from tqdm import tqdm
from rapidfuzz import process, fuzz

# Load the local database of coordinates
city_coords = pd.read_csv("fi_cities.csv")

# Function to find coordinates for a place name using fuzzy matching
def get_coordinates(place_name):
    if pd.isna(place_name):
        return None
    place_name = str(place_name)  # Ensure the place_name is a string
    match, score, _ = process.extractOne(place_name, city_coords['city'], scorer=fuzz.ratio)
    if score >= 80:  # Adjust the threshold as needed
        row = city_coords[city_coords['city'] == match]
        if not row.empty:
            return Point(row.iloc[0]['lng'], row.iloc[0]['lat'])
    print(f"Coordinates not found for: {place_name}")
    return None

# Load the NUTS2 regions shapefile
nuts2 = gpd.read_file("NUTS_RG_20M_2021_4326.geojson")
nuts2 = nuts2[nuts2['NUTS_ID'].str.startswith('FI')]

# Ensure the CRS is correct
nuts2.crs = 'EPSG:4326'
print(nuts2)

# Load the Finnish Parliament members dataset
dataset = pd.read_csv("parliamentary_info.csv")

# Match coordinates for birthplaces
tqdm.pandas()
dataset['geometry'] = dataset['Birth place'].progress_apply(get_coordinates)

# Drop rows where coordinates were not found
dataset = dataset.dropna(subset=['geometry'])

# Convert the DataFrame to a GeoDataFrame
geo_df = gpd.GeoDataFrame(dataset, geometry='geometry')
geo_df.crs = 'EPSG:4326'

# Print the geocoded dataframe
print(geo_df)

# Spatial join to map coordinates to NUTS2 regions
geo_df = gpd.sjoin(geo_df, nuts2, how='left', op='within')

# Count the number of members per NUTS2 region
counts = geo_df.groupby('NUTS_ID').size().reset_index(name='count')

# Merge the counts with the NUTS2 GeoDataFrame
nuts2 = nuts2.merge(counts, on='NUTS_ID', how='left').fillna(0)

# Convert counts to percentages
nuts2['count_percentage'] = (nuts2['count'] / dataset.shape[0]) * 100

# Plot the results
fig, ax = plt.subplots(figsize=(10, 10))

# Plot using color based on 'count_percentage'
plot = nuts2.plot(column='count_percentage', cmap='coolwarm', edgecolor='black', linewidth=0.5,
                  alpha=0.9, ax=ax, legend=True,
                  scheme='Quantiles', k=10, 
                  legend_kwds={'title': "Percentage of MPs by Region",
                               'loc': 'center left', 'bbox_to_anchor': (1, 0.5)})

# Remove x and y axis labels
ax.set_xticks([])
ax.set_yticks([])

# Set a title
ax.set_title('MP Distribution Across Finnish NUTS2 Regions')

# Show the plot
plt.show()


# In[] 
# Analysis for the Finnish Parliament: to determine which regions are overrepresented by normalizing representation by the population of each region, we can use the eurostat package to get population data for the NUTS2 regions of Finland.  

# In[deviation from the mean]:
    
# To create a graph that highlights areas which are overrepresented,
# we need to adjust the colormap to better reflect overrepresentation. 
# One way to achieve this is to define overrepresentation as having a higher percentage of MPs relative to the average percentage per region. 
# We will use a diverging colormap to show areas with higher representation in one color and those with lower representation in another.
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from shapely.geometry import Point
from tqdm import tqdm
from rapidfuzz import process, fuzz

# Load the local database of coordinates
city_coords = pd.read_csv("fi_cities.csv")

# Function to find coordinates for a place name using fuzzy matching
def get_coordinates(place_name):
    if pd.isna(place_name):
        return None
    place_name = str(place_name)  # Ensure the place_name is a string
    match, score, _ = process.extractOne(place_name, city_coords['city'], scorer=fuzz.ratio)
    if score >= 80:  # Adjust the threshold as needed
        row = city_coords[city_coords['city'] == match]
        if not row.empty:
            return Point(row.iloc[0]['lng'], row.iloc[0]['lat'])
    print(f"Coordinates not found for: {place_name}")
    return None

# Load the NUTS2 regions shapefile
nuts2 = gpd.read_file("NUTS_RG_20M_2021_4326.geojson")
nuts2 = nuts2[nuts2['NUTS_ID'].str.startswith('FI')]

# Ensure the CRS is correct
nuts2.crs = 'EPSG:4326'
print(nuts2)

# Load the Finnish Parliament members dataset
dataset = pd.read_csv("parliamentary_info.csv")

# Match coordinates for birthplaces
tqdm.pandas()
dataset['geometry'] = dataset['Birth place'].progress_apply(get_coordinates)

# Drop rows where coordinates were not found
dataset = dataset.dropna(subset=['geometry'])

# Convert the DataFrame to a GeoDataFrame
geo_df = gpd.GeoDataFrame(dataset, geometry='geometry')
geo_df.crs = 'EPSG:4326'

# Print the geocoded dataframe
print(geo_df)

# Spatial join to map coordinates to NUTS2 regions
geo_df = gpd.sjoin(geo_df, nuts2, how='left', op='within')

# Count the number of members per NUTS2 region
counts = geo_df.groupby('NUTS_ID').size().reset_index(name='count')

# Merge the counts with the NUTS2 GeoDataFrame
nuts2 = nuts2.merge(counts, on='NUTS_ID', how='left').fillna(0)

# Convert counts to percentages
nuts2['count_percentage'] = (nuts2['count'] / dataset.shape[0]) * 100

# Calculate the average percentage of MPs per region
average_percentage = nuts2['count_percentage'].mean()

# Calculate the deviation from the average percentage
nuts2['deviation_from_average'] = nuts2['count_percentage'] - average_percentage

# Plot the results
fig, ax = plt.subplots(figsize=(10, 10))

# Use a diverging colormap to show over and underrepresentation
cmap = plt.get_cmap('coolwarm')
norm = mcolors.TwoSlopeNorm(vmin=nuts2['deviation_from_average'].min(),
                            vcenter=0,
                            vmax=nuts2['deviation_from_average'].max())

# Plot using color based on 'deviation_from_average'
plot = nuts2.plot(column='deviation_from_average', cmap=cmap, edgecolor='black', linewidth=0.5,
                  alpha=0.9, ax=ax, legend=True,
                  norm=norm,
                  legend_kwds={'label': "Deviation from Average (%)",
                               'orientation': "horizontal",
                               'shrink': 0.6})

# Remove x and y axis labels
ax.set_xticks([])
ax.set_yticks([])

# Set a title
ax.set_title('MP Overrepresentation Across Finnish NUTS2 Regions')

# Show the plot
plt.show()





















# In[overrepresentation using population data] 
# Step-by-Step Implementation:

#     Load Necessary Libraries and Data:
#         Load the NUTS2 shapefile for Finland.
#         Load the dataset of Finnish Parliament members.

#     Geocode Birthplaces:
#         Match birthplaces to their corresponding coordinates.

#     Spatial Join with NUTS2 Regions:
#         Map the geocoded birthplaces to NUTS2 regions.

#     Get Population Data for NUTS2 Regions:
#         Use the eurostat package to get the population of each NUTS2 region.

#     Normalize Representation by Population:
#         Calculate the share of MPs from each region and normalize by the population to determine overrepresentation.

#     Plot the Data:
#         Plot the normalized representation data on a map.

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from shapely.geometry import Point
from tqdm import tqdm
from rapidfuzz import process, fuzz
import eurostat

# Load the local database of coordinates
city_coords = pd.read_csv("fi_cities.csv")

# Function to find coordinates for a place name using fuzzy matching
def get_coordinates(place_name):
    if pd.isna(place_name):
        return None
    place_name = str(place_name)  # Ensure the place_name is a string
    match, score, _ = process.extractOne(place_name, city_coords['city'], scorer=fuzz.ratio)
    if score >= 80:  # Adjust the threshold as needed
        row = city_coords[city_coords['city'] == match]
        if not row.empty:
            return Point(row.iloc[0]['lng'], row.iloc[0]['lat'])
    print(f"Coordinates not found for: {place_name}")
    return None

# Load the NUTS2 regions shapefile
nuts2 = gpd.read_file("NUTS_RG_20M_2021_4326.geojson")
nuts2 = nuts2[nuts2['NUTS_ID'].str.startswith('FI')]

# Ensure the CRS is correct
nuts2.crs = 'EPSG:4326'
print(nuts2)

# Load the Finnish Parliament members dataset
dataset = pd.read_csv("parliamentary_info.csv")

# Match coordinates for birthplaces
tqdm.pandas()
dataset['geometry'] = dataset['Birth place'].progress_apply(get_coordinates)

# Drop rows where coordinates were not found
dataset = dataset.dropna(subset=['geometry'])

# Convert the DataFrame to a GeoDataFrame
geo_df = gpd.GeoDataFrame(dataset, geometry='geometry')
geo_df.crs = 'EPSG:4326'

# Print the geocoded dataframe
print(geo_df)

# Spatial join to map coordinates to NUTS2 regions
geo_df = gpd.sjoin(geo_df, nuts2, how='left', op='within')

# Count the number of members per NUTS2 region
counts = geo_df.groupby('NUTS_ID').size().reset_index(name='count')

# Merge the counts with the NUTS2 GeoDataFrame
nuts2 = nuts2.merge(counts, on='NUTS_ID', how='left').fillna(0)

# Convert counts to percentages
nuts2['count_percentage'] = (nuts2['count'] / dataset.shape[0]) * 100

# Get population data from Eurostat
population_df = eurostat.get_data_df('demo_r_pjangrp3')

# Filter for Finnish NUTS2 regions
population_df = population_df[population_df['geo\\TIME_PERIOD'].str.startswith('FI') & (population_df['unit'] == 'NR')]

# Select the most recent year and relevant columns
recent_year = '2023'
population_df = population_df[['geo\\TIME_PERIOD', recent_year]].rename(columns={'geo\\TIME_PERIOD': 'NUTS_ID', recent_year: 'population'})

# Convert population to numeric and remove any rows with missing data
population_df['population'] = pd.to_numeric(population_df['population'], errors='coerce')
population_df = population_df.dropna(subset=['population'])

# Check for duplicate entries and keep only the latest data
population_df = population_df.drop_duplicates(subset=['NUTS_ID'])

# Ensure that the number of rows matches the expected number of NUTS2 regions in Finland
assert population_df['NUTS_ID'].nunique() == len(nuts2)

# Merge population data with NUTS2 GeoDataFrame
nuts2 = nuts2.merge(population_df, on='NUTS_ID', how='left')

# Calculate representation per capita
nuts2['representation_per_capita'] = nuts2['count'] / nuts2['population'] * 1000  # MPs per 1000 people

# Ensure vmin, vcenter, and vmax are in ascending order
vmin = nuts2['representation_per_capita'].min()
vmax = nuts2['representation_per_capita'].max()
vcenter = (vmin + vmax) / 2

# Plot the results
fig, ax = plt.subplots(figsize=(10, 10))

# Use a diverging colormap to show over and underrepresentation
cmap = plt.get_cmap('coolwarm')
norm = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)

# Plot using color based on 'representation_per_capita'
plot = nuts2.plot(column='representation_per_capita', cmap=cmap, edgecolor='black', linewidth=0.5,
                  alpha=0.9, ax=ax, legend=True,
                  norm=norm,
                  legend_kwds={'label': "MPs per 1000 People",
                               'orientation': "horizontal",
                               'shrink': 0.6})

# Remove x and y axis labels
ax.set_xticks([])
ax.set_yticks([])

# Set a title
ax.set_title('MP Representation per Capita Across Finnish NUTS2 Regions')

# Show the plot
plt.show()

# In[]:
    
# Now we show an alternative method, where we use a Quantiles scheme for the legend and
# adjust the legend settings. The scheme='Quantiles' and k=10 will create the legend with 10 quantile bins
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from shapely.geometry import Point
from tqdm import tqdm
from rapidfuzz import process, fuzz
import eurostat

# Load the local database of coordinates
city_coords = pd.read_csv("fi_cities.csv")

# Function to find coordinates for a place name using fuzzy matching
def get_coordinates(place_name):
    if pd.isna(place_name):
        return None
    place_name = str(place_name)  # Ensure the place_name is a string
    match, score, _ = process.extractOne(place_name, city_coords['city'], scorer=fuzz.ratio)
    if score >= 80:  # Adjust the threshold as needed
        row = city_coords[city_coords['city'] == match]
        if not row.empty:
            return Point(row.iloc[0]['lng'], row.iloc[0]['lat'])
    print(f"Coordinates not found for: {place_name}")
    return None

# Load the NUTS2 regions shapefile
nuts2 = gpd.read_file("NUTS_RG_20M_2021_4326.geojson")
nuts2 = nuts2[nuts2['NUTS_ID'].str.startswith('FI')]

# Ensure the CRS is correct
nuts2.crs = 'EPSG:4326'
print(nuts2)

# Load the Finnish Parliament members dataset
dataset = pd.read_csv("parliamentary_info.csv")

# Match coordinates for birthplaces
tqdm.pandas()
dataset['geometry'] = dataset['Birth place'].progress_apply(get_coordinates)

# Drop rows where coordinates were not found
dataset = dataset.dropna(subset=['geometry'])

# Convert the DataFrame to a GeoDataFrame
geo_df = gpd.GeoDataFrame(dataset, geometry='geometry')
geo_df.crs = 'EPSG:4326'

# Print the geocoded dataframe
print(geo_df)

# Spatial join to map coordinates to NUTS2 regions
geo_df = gpd.sjoin(geo_df, nuts2, how='left', op='within')

# Count the number of members per NUTS2 region
counts = geo_df.groupby('NUTS_ID').size().reset_index(name='count')

# Merge the counts with the NUTS2 GeoDataFrame
nuts2 = nuts2.merge(counts, on='NUTS_ID', how='left').fillna(0)

# Convert counts to percentages
nuts2['count_percentage'] = (nuts2['count'] / dataset.shape[0]) * 100

# Get population data from Eurostat
population_df = eurostat.get_data_df('demo_r_pjangrp3')

# Filter for Finnish NUTS2 regions
population_df = population_df[population_df['geo\\TIME_PERIOD'].str.startswith('FI') & (population_df['unit'] == 'NR')]

# Select the most recent year and relevant columns
recent_year = '2023'
population_df = population_df[['geo\\TIME_PERIOD', recent_year]].rename(columns={'geo\\TIME_PERIOD': 'NUTS_ID', recent_year: 'population'})

# Convert population to numeric and remove any rows with missing data
population_df['population'] = pd.to_numeric(population_df['population'], errors='coerce')
population_df = population_df.dropna(subset=['population'])

# Check for duplicate entries and keep only the latest data
population_df = population_df.drop_duplicates(subset=['NUTS_ID'])

# Ensure that the number of rows matches the expected number of NUTS2 regions in Finland
assert population_df['NUTS_ID'].nunique() == len(nuts2)

# Merge population data with NUTS2 GeoDataFrame
nuts2 = nuts2.merge(population_df, on='NUTS_ID', how='left')

# Calculate representation per capita
nuts2['representation_per_capita'] = nuts2['count'] / nuts2['population'] * 1000  # MPs per 1000 people

# Ensure vmin, vcenter, and vmax are in ascending order
vmin = nuts2['representation_per_capita'].min()
vmax = nuts2['representation_per_capita'].max()
vcenter = (vmin + vmax) / 2

# Plot the results
fig, ax = plt.subplots(figsize=(10, 10))

# Use a sequential colormap to show overrepresentation
cmap = plt.get_cmap('coolwarm')

# Plot using color based on 'representation_per_capita' and use Quantiles scheme
plot = nuts2.plot(column='representation_per_capita', cmap=cmap, edgecolor='black', linewidth=0.5,
                  alpha=0.9, ax=ax, legend=True,
                  scheme='Quantiles', k=10,
                  legend_kwds={'title': "Percentage of MPs by Region",
                               'loc': 'center left', 'bbox_to_anchor': (1, 0.5)})

# Remove x and y axis labels
ax.set_xticks([])
ax.set_yticks([])

# Set a title
ax.set_title('MP Representation per Capita Across Finnish NUTS2 Regions')

# Show the plot
plt.show()

#The difference in colors between the two graphs is likely due to the different methods used for normalization and color scaling. 

# In[]


# TEXT ANALYSIS
# Now, we aim to conduct a text analysis on the press releases of the plenary sessions of the Finnish Parliament. This involves several key steps:
# 1) Web Scraping: We collect the press releases from the Finnish Parliament website using Selenium and 
#    BeautifulSoup, extracting relevant information such as titles, content, and publication dates in order to create a dataset;
# 2) Keyword Analysis: We define specific themes and create "bags of words" to track the relevance 
#    of these themes in the plenary sessions press releases over the years.
# 3) Data Cleaning: The extracted content is cleaned by removing stopwords, punctuation, and other irrelevant parts. 
#    We also perform lemmatization to ensure consistency in word forms.
# 4) Sentiment Analysis: Using the TextBlob library, we analyze the sentiment of the press releases to understand 
#    the overall tone and mood.
# 5) Topic Modeling: We use Latent Dirichlet Allocation (LDA) to identify underlying topics within the press releases,
#    adjusting parameters to optimize the coherence and interpretability of these topics.

# In conclusion, we will conduct a text analysis on the two major Finnish political parties to understand 
# the main themes of their principle programs.

# In[]
# Packages installed to conduct Text Analysis:
import os

# Define a list of packages to install
packages = [
    "requests",
    "beautifulsoup4",
    "pandas",
    "numpy",
    "tqdm",
    "selenium",
    "webdriver-manager",
    "prettytable",
    "matplotlib",
    "gensim",
    "pyLDAvis",
    "textblob",
    "wordcloud",
    "spacy",
    "nltk",
    "vaderSentiment",
]

# Install each package using pip
for package in packages:
    os.system(f"pip install {package}")


# In[]
# Import packages related to webscraping
import requests
from bs4 import BeautifulSoup

# Import packages for data management
import pandas as pd

# Import generalist package
import numpy as np

# Import package for completion monitoring
from tqdm import trange

# Import package to introduce time delays
from time import sleep

# Selenium and related packages for browser automation
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Regular expressions for text processing
import re

# Configure the Chrome driver
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

# Navigate to the press releases (plenary session) page
driver.get("https://www.eduskunta.fi/EN/tiedotteet/Pages/default.aspx#cf1151f2-8482-460e-8c1b-9901bb38b0eb=%7B%22k%22%3A%22%22%2C%22r%22%3A%5B%7B%22n%22%3A%22owstaxIdClassificationCompleteMatching%22%2C%22t%22%3A%5B%22%5C%22%C7%82%C7%824c307c233065336138653534372d666435352d343364642d613337322d6239303966313530353735367c506c656e6172792073657373696f6e%5C%22%22%5D%2C%22o%22%3A%22OR%22%2C%22k%22%3Afalse%2C%22m%22%3A%7B%22%5C%22%C7%82%C7%824c307c233065336138653534372d666435352d343364642d613337322d6239303966313530353735367c506c656e6172792073657373696f6e%5C%22%22%3A%22Plenary%20session%22%7D%7D%5D%2C%22l%22%3A1033%7D")

# Wait until the links are present
try:
    press_releases_links = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//h3[@class="ms-srch-ellipsis"]/a'))
    )
except:
    print("Links were not found")
    driver.quit()
    exit()

# Extract URLs from the WebElement objects
url_list = [link.get_attribute("href") for link in press_releases_links]
print(url_list)


# Define headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com',
    'Connection': 'keep-alive'
}

# In[]

# To begin with, we want to create a dataset that concerns the press realeses of the plenary sessions of the Finnish Parliament.
# The dataset is initially made up of four colums: title, content, publication date and year of the press release.

# We create a list that includes all the press releases concerning Parliament's plenary sessions
list_plenary_session = list()


# Function to extract year from the publication date
def extract_year(date_str):
    match = re.search(r'\b(\d{4})\b', date_str)
    return int(match.group(1)) if match else None

# Iterate over each URL in the list
for url in url_list:
    try:
        # Make the GET request to the page
        webpage = requests.get(url, headers=headers, timeout=30, allow_redirects=True)

        # Check if the request was successful
        if webpage.status_code == 200:
            # Parse the HTML content of the page
            page_content = BeautifulSoup(webpage.text, 'html.parser')

            # Find the title element
            title_element = page_content.find("h1", class_="ms-rteElement-eduskuntaH1")
            title = title_element.text.strip() if title_element else "Title not found"

            # Find the content element
            content_element = page_content.find(
                "div",
                id="ctl00_PlaceHolderMain_NewsRichHtmlField1__ControlWrapper_RichHtmlField",
                attrs={"class": "ms-rtestate-field"}
            )
            content = content_element.text.strip() if content_element else "Content not found"

            # Find the publication date element
            publication_date_element = page_content.find("div", class_="dvPublishingStartDate")
            if publication_date_element:
                nobr_element = publication_date_element.find("nobr")
                if nobr_element:
                    publication_date = nobr_element.text.strip()
                else:
                    publication_date = "Publication date not found"
            else:
                publication_date = "Publication date not found"

            # Extract year from the publication date
            year = extract_year(publication_date)

            # Add the title, content, publication date, and year to the list
            list_plenary_session.append([title, content, publication_date, year])

        else:
            print(f"Error loading page: {url}")

    except requests.exceptions.RequestException as e:
        print(f"Error of request for {url}: {e}")

# Create DataFrame from the list
dataset = pd.DataFrame(list_plenary_session, columns=['title', 'content', 'publication date', 'year'])


# Let's have a look at the data we just scraped
print(dataset.sample(n=3).to_string(index=False))

# In[]

# Now, we will use regular expressions to extract specific press releases concerning the Parliament,
# including press releases of some of its resolutions such as approvals and appointments.
# In the following order, we will extract:
# - The object of press releases concerning Parliament, in particular regarding its actions; 
# - The object of press releases concerning measures that involve Government

# The object of the releases concerning Parliament

# Define a function to extract the object of the press releases concerning Parliament.
def extract_release(title):
    # Use regular expression to find titles that start with "Parliament" followed by any punctuation and the release object.
    releases = re.search(r'^(Parliament)[:\s]+(.*?)\s*$', title)
    
    if releases:
        # If a match is found, return the release object (second group in the regex).
        releases = releases.group(2)
    else:
        # If no match is found, return "Not applicable".
        releases = "Not applicable"
    return releases

# Apply the 'extract_release' function to the 'title' column of the dataset
dataset['Parliamentary Actions'] = dataset['title'].apply(lambda x: extract_release(x))

# Display the updated dataset with the new columns.
print(dataset.to_string(index=False))


# Measures that involve Government

# Define a function to extract measures involving the Government from the titles.
def extract_measure(title):
    # Use regular expression to find "Government" followed by the measure in the title.
    measures = re.search(r'\bGovernment\b\s+(.*)', title)
    
    if measures:
        # If a match is found, return the measure (the text after "Government").
        measures = measures.group(1).strip()  # Strip leading/trailing whitespace
    else:
        # If no match is found, return "Not applicable".
        measures = "Not applicable"
    return measures

# Apply the 'extract_measure' function to the 'title' column of the dataset
# and create a new column 'Measures' with the extracted measures.
dataset['Measures'] = dataset['title'].apply(lambda x: extract_measure(x))

# Display the updated dataset with the new column.
print(dataset)



# In[]

# Now that we have the press releases of the plenary sessions, we will create 'bags of words',
# which are simple lists of words pertaining to specific themes we want to track in the Finnish Parliament press releases.
# These themes include:
# 
# - Legislation and Reforms
# - Economy and Finance
# - Internal Policy
# - Foreign Policy
# - Environment and Sustainability
#
# This way, we can monitor the relevance of these themes in the press releases over the three years.

# Create the bag of words
# Define the bags of words for each theme
bags_of_words = {
    'Legislation and Reforms': ['legislation', 'reform', 'bill', 'law', 'amendment', 'statute', 'policy', 'regulation', 'act', 'decree'],
    'Economy and Finance': ['economy', 'finance', 'budget', 'deficit', 'tax', 'revenue', 'expenditure', 'growth', 'investment', 'inflation', 'debt', 'fiscal', 'monetary', 'trade', 'unemployment', 'GDP'],
    'Internal Policy': ['governance', 'election', 'parliament', 'democracy', 'policy', 'reform', 'cabinet', 'minister', 'legislation', 'party', 'vote', 'government'],
    'Foreign Policy': ['foreign', 'international', 'diplomacy', 'treaty', 'alliance', 'cooperation', 'relations', 'trade', 'conflict', 'security', 'military', 'defense', 'embassy'],
    'Environment and Sustainability': ['environment', 'sustainability', 'climate', 'pollution', 'energy', 'conservation', 'biodiversity', 'renewable', 'emissions', 'waste', 'recycling', 'green', 'ecosystem', 'habitat', 'sustainable']
}

# Function to count occurrences of words in the bags of words
def bag_counts(text):
    text = text.lower()
    nbr_words = len(text.split(' '))
    counts = {}
    
    for theme, words in bags_of_words.items():
        count = sum(text.count(word) for word in words)
        counts[theme] = count / nbr_words if nbr_words > 0 else 0
    
    return counts

# Apply the function to the 'content' column and create new columns for each theme
theme_counts = dataset['content'].apply(bag_counts)

# Convert the resulting series of dictionaries into a DataFrame and merge with the original DataFrame
theme_counts_df = pd.DataFrame(list(theme_counts))
dataset = pd.concat([dataset, theme_counts_df], axis=1)

# Display the DataFrame with relevance scores
print(dataset.to_string(index=False))

# Save the DataFrame to a CSV file
dataset.to_csv('plenary_session.csv', index=False)

# We can now apply this function to our dataset
dataset = pd.read_csv("plenary_session.csv")

# Heatmap Analysis Comment
# The heatmap visualization shows the relevance scores for different themes across various press releases of the Finnish Parliament.
# The colors in the heatmap help quickly identify areas of high and low relevance for each theme:
# Red indicates low relevance, while blue and purple shades indicate higher relevance.
# This visual representation aids in understanding the thematic focus of the Finnish Parliament's plenary sessions press releases over time.

# In[]

# Group by 'year' and calculate the mean for each theme. we decided to use years and not months so that the plot will show the quarters for each year on the x axis

dataset_grouped= dataset.groupby('year')[['Legislation and Reforms', 'Economy and Finance', 'Internal Policy', 'Foreign Policy', 'Environment and Sustainability']].mean()

# Display the grouped DataFrame with averages
print(dataset.to_string(index=False))

import matplotlib.pyplot as plt

# Assuming dataset_grouped is the DataFrame that was grouped by year
# Plotting the data
plt.figure(figsize=(10, 6))
plt.plot(dataset_grouped.index, dataset_grouped['Legislation and Reforms'], label='Legislation and Reforms', marker='o')
plt.plot(dataset_grouped.index, dataset_grouped['Economy and Finance'], label='Economy and Finance', marker='s')
plt.plot(dataset_grouped.index, dataset_grouped['Internal Policy'], label='Internal Policy', marker='^')
plt.plot(dataset_grouped.index, dataset_grouped['Foreign Policy'], label='Foreign Policy', marker='D')
plt.plot(dataset_grouped.index, dataset_grouped['Environment and Sustainability'], label='Environment and Sustainability', marker='x')
plt.title('Finnish Parliament Press Releases Main Themes Over Years')
plt.xlabel('Year')
plt.ylabel('Indicator')
plt.legend()
plt.grid(True)
plt.show()

# The plot illustrates that the Finnish Parliament's focus has shifted over the years, with Internal Policy peaking in 2023. 
# Both Economy and Finance, as well as Legislation and Reforms, experienced a decline, although the latter showed a slight increase 
# afterward. Foreign Policy themes show a gradual rise, while Environment and Sustainability themes remain consistently low 
# throughout the observed period.

# In[]

# Now we want to identify the most important theme basing on the number of occurrences of specific keywords.
# Adapt the function to your themes
def bag_identify(x):
    # Initialize counts
    counts = {}
    
    # Count occurrences for each theme
    for theme, words in bags_of_words.items():
        counts[theme] = sum([x.lower().count(y) for y in words])
    
    # Find the most important theme
    most_important = max(counts, key=counts.get)
    
    # Create the output list
    arguments = [int(theme == most_important) for theme in bags_of_words.keys()]
    
    return arguments

# Apply the function to the 'content' column and create new columns for each theme
theme_columns = list(bags_of_words.keys())
dataset[theme_columns] = pd.DataFrame(dataset['content'].apply(lambda x: bag_identify(x)).tolist(), index=dataset.index)

# Group by 'year' and calculate the mean for each theme
dataset_grouped = dataset.groupby('year')[theme_columns].mean()

# Display the grouped DataFrame with averages
print(dataset_grouped.to_string(index=False))


# Plotting the data
plt.figure(figsize=(10, 6))
plt.plot(dataset_grouped.index, dataset_grouped['Legislation and Reforms'], label='Legislation and Reforms', marker='o')
plt.plot(dataset_grouped.index, dataset_grouped['Economy and Finance'], label='Economy and Finance', marker='s')
plt.plot(dataset_grouped.index, dataset_grouped['Internal Policy'], label='Internal Policy', marker='^')
plt.plot(dataset_grouped.index, dataset_grouped['Foreign Policy'], label='Foreign Policy', marker='D')
plt.plot(dataset_grouped.index, dataset_grouped['Environment and Sustainability'], label='Environment and Sustainability', marker='x')
plt.title('Most Important Themes in Finnish Parliament Press Releases Over the Years')
plt.xlabel('Year')
plt.ylabel('Share')
plt.legend()
plt.grid(True)
plt.show()

# In 2022, Economy and Finance were the dominant themes, but this diminished significantly by 2023, with Internal Policy 
# becoming the most prominent. The increased relevance of Foreign Policy towards 2024 indicates a growing importance 
# of international issues. Legislation and Reforms also increased in relevance over the years. Conversely, 
# Environment and Sustainability have consistently remained the least emphasized theme in the plenary sessions press releases.

# In[]

# ## Descriptive Methods - Sentiment Analysis

from textblob import TextBlob

# Load the dataset
dataset = pd.read_csv("plenary_session.csv")

# Apply sentiment analysis on the 'content' column and add the results to a new 'sentiment' column
dataset['sentiment'] = dataset['content'].apply(lambda x: TextBlob(x).sentiment.polarity)

# Calculate the mean, maximum, and minimum sentiment for each year
df_plot_mean = dataset.groupby('year')['sentiment'].mean()
df_plot_max = dataset.groupby('year')['sentiment'].max()
df_plot_min = dataset.groupby('year')['sentiment'].min()

# Plot the sentiment analysis results over the years
plt.figure(figsize=(10, 6))
plt.plot(df_plot_mean.index, df_plot_mean, label='average', marker='o')
plt.plot(df_plot_mean.index, df_plot_max, label='max', marker='o')
plt.plot(df_plot_mean.index, df_plot_min, label='min', marker='o')
plt.title('Finnish Parliament press releases main sentiment over year')
plt.xlabel('Year')
plt.ylabel('Share')
plt.legend()
plt.grid(True)
plt.show()

# The plot shows the sentiment trends in Finnish Parliament press releases over time. 
# The average sentiment (blue line) remains relatively stable, hovering around neutral. 
# The maximum sentiment (orange line) peaks in 2023, indicating more positive press releases during that period. 
# Conversely, the minimum sentiment (green line) dips further into negativity in 2023, suggesting a mix of highly positive 
# and negative sentiments in that year.


# In[]

# Descriptive Methods - WordCloud
# Word clouds are a simple way to visually represent the most frequently occurring keywords in a text or corpus. 
# This helps in quickly identifying the main themes or topics.

from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Generate the word cloud for the content of a specific document (row - index - 9 in this case).
wordcloud = WordCloud(max_font_size=50, max_words=100, background_color="white").generate(dataset.loc[9, 'content'])

# Display the generated word cloud image.
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")  # Hide the axis
plt.show()

# In[]

# Cleaning the text
# To improve the word cloud's clarity, we exclude common stopwords (e.g., "the", "and") that do not add value to the main content.
# This process helps the word cloud visually represent the most frequent and significant words in the text, 
# providing a clearer insight into the primary themes.

from wordcloud import STOPWORDS

# Set of stopwords to exclude from the word cloud
stopwords = set(STOPWORDS)
print(stopwords)  # Display the set of stopwords

# Generate the word cloud again with stopwords excluded.
wordcloud = WordCloud(max_font_size=50, max_words=100, background_color="white", stopwords=stopwords).generate(dataset.loc[9, 'content'])

# Display the word cloud with stopwords excluded
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")  # Hide the axis
plt.show()


# In[]

# When words are conjugated, they are not considered the same:
# Now we want to enhance our code, by making such words match. There are two processes for this:
#     - `Stemming` - Truncating to a root that might not exist.
#     - `Lemmatizing` - going back to the word root of a term, it should exist in a dictionary.
# Both processes involve altering each word in a corpus to revert to its root form.

import spacy
from random import choice

# Import the core library for english words
nlp = spacy.load('en_core_web_sm')

# Let's lemmatize a random paragraph of our dataset
random_par = dataset.sample(n=1)['content'].values[0].split('\n')
random_par = choice(random_par).split(' ')

# Remove stop words and lemmatize
random_par = ' '.join([x for x in random_par if x not in stopwords])

# Process the text using spaCy 
doc = nlp(random_par)
 
# Extract lemmatized tokens
lemmatized_tokens = [token.lemma_ for token in doc if token.is_stop == False]
 
# Join the lemmatized tokens into a sentence
lemmatized_text = ' '.join(lemmatized_tokens)
 
print(random_par, '\n')
print(lemmatized_text)

# Let's also eliminate portions of the text that don't aid in understanding its meaning from the words.:
# 
#     - Punctuation
#     - Stopwords
#     - Numbers
#     - Special signs: percentages, apostrophes..
#     
# Clean text
def cleaning_text(text_elem):
    # You apply the spacy functions
    doc = nlp(text_elem)
    
    # We now proceed token by token, keep only the ones we want, remove the others
    doc = [token for token in doc if token.is_stop == False]
    doc = [token for token in doc if token.is_punct == False]
    doc = [token for token in doc if token.is_alpha == True]
    
    # And now we lemmatize
    doc = [token.lemma_ for token in doc if token.lemma_ != "well"]
    
    cleaned_text = ' '.join(doc)
    return(cleaned_text)

# Let's clean a random part paragraph of our dataset
random_par = dataset.sample(n=1)['content'].values[0].split('\n')
random_par = choice(random_par)

# We clean and lemmatize
cleaned = cleaning_text(random_par)

# Print both
print(random_par, '\n')
print(cleaned)

# Apply our function/pipeline to every piece of content
dataset['content_clean'] = dataset['content'].apply(lambda x: cleaning_text(x))

# Save the cleaned dataset to a CSV file
dataset.to_csv('plenary_session_cleaned.csv', index=False)

# Now read the cleaned dataset from the CSV file
dataset_cleaned = pd.read_csv('plenary_session_cleaned.csv')

# Display the cleaned dataset
print(dataset_cleaned.head())

# In[]

# Select a random index for the sample
idx = 7

# Generate the word cloud from the original version of the text
wordcloud1 = WordCloud(max_font_size=50, max_words=100, background_color="white",
                     stopwords=stopwords).generate(dataset.loc[idx, 'content'])

# Generate the word cloud from the cleaned version of the text
wordcloud2 = WordCloud(max_font_size=50, max_words=100, background_color="white",
                     stopwords=stopwords).generate(dataset.loc[idx, 'content_clean'])

# Create a figure with two subplots to display the word clouds
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 7))  # Adjust figsize to fit your screen

# Display the word cloud from the original text
ax1.imshow(wordcloud1, interpolation='bilinear')
ax1.axis("off")  # Remove the axes
ax1.set_title('Raw')  # Set the title

# Display the word cloud from the cleaned text
ax2.imshow(wordcloud2, interpolation='bilinear')
ax2.axis("off")  # Remove the axes
ax2.set_title('Cleaned')  # Set the title

# Adjust subplots to fit into figure area
plt.tight_layout()

# Show the figure with the word clouds
plt.show()

# We can now compare the key words present in the original text with those in the cleaned text,
# highlighting the impact of text cleaning on word frequency and distribution.

# In[]

# Learning based methods
# We will use a typology of unsupervised methods, Latent Dirichlet Allocation (LDA)
# - In a corpora of texts, we want to identify the items that are similar to each others.
import gensim.corpora as corpora
from gensim.models import CoherenceModel

# Take our documents, transform it so that each word is divided
documents = dataset.loc[: , 'content_clean'].tolist()
processed_texts  = [[word for word in doc.split(' ')] for doc in documents]
 
id2word = corpora.Dictionary(processed_texts)

# Term Document Frequency
corpus = [id2word.doc2bow(text) for text in processed_texts]

from gensim.models.ldamodel import LdaModel
import pandas as pd

# Set number of topics
num_topics = 10


# Build LDA model
lda_model = LdaModel(corpus=corpus, id2word=id2word, num_topics=num_topics, random_state=42, passes=10, alpha="auto", per_word_topics=True)


from pprint import pprint

pprint(lda_model.print_topics())

# In the LDA model output, each word within a topic has an associated weight indicating its importance. 
# Higher weights mean the word is more significant in defining the topic. For instance, in a topic with "0.017*'Finland'", 
# "Finland" is highly relevant with a weight of 0.017.

# In[]

# The code below calculates the coherence score for the LDA model,
# which is a measure of how interpretable the topics generated by the model are.

coherence_model_lda = CoherenceModel(model=lda_model, texts=processed_texts, dictionary=id2word, coherence="c_v")
coherence_lda = coherence_model_lda.get_coherence()
print("Coherence Score: ", coherence_lda)
 
# The coherence score validates the quality of the topics generated and indicates whether the model is suitable for extracting themes and insights from the dataset.
# It is really important to point out that, since the Finnish Parliament's website is continuously updated, 
# new links to plenary sessions' press releases can be added, modifying the dataset, and potentially causing the coherence score to change.

# Now we want to visualize what happens
import pyLDAvis
import pyLDAvis.gensim_models as gensimvis

pyLDAvis.enable_notebook()
vis = gensimvis.prepare(lda_model, corpus, id2word)

vis

# The LDA model has identified 10 main topics in the documents. Each topic is characterized by terms with 
# associated weights indicating their importance.  
# The pyLDAvis visualization allows for interactive exploration of these topics, facilitating interpretation and analysis.

# Since all the press releases are written in English, there is no need to use language detection tools like langdetect.

# In[]

# Since we have a lot of terms that appear in too many subjects, we can have one or both of the two issues:
# 
# - Words that are meaningless to differentiate between press releases because they are everywhere.
# - Too many topics, so in any case there will be several repeated topics.
# 
# We want to work on both. Starting with removing words like "Parliament", "Government".

# Take our documents, transform it so that each word is divided
documents = dataset.loc[: , 'content_clean'].tolist()
processed_texts  = [[word for word in doc.split(' ') if word not in ['Parliament', 'Government']] for doc in documents]
 
id2word = corpora.Dictionary(processed_texts)

# Term Document Frequency
corpus = [id2word.doc2bow(text) for text in processed_texts]

# Set number of topics
num_topics = 10

# Build LDA model
lda_model = LdaModel(corpus=corpus, id2word=id2word, num_topics=num_topics, random_state=42, passes=10, alpha="auto", per_word_topics=True)

# In[]

# Let's look at the coherence score again
coherence_model_lda = CoherenceModel(model=lda_model, texts=processed_texts, dictionary=id2word, coherence="c_v")
coherence_lda = coherence_model_lda.get_coherence()
print("Coherence Score: ", coherence_lda)


vis = gensimvis.prepare(lda_model, corpus, id2word)
vis


# In[]

# A lot of our topics are overlapping. Let's try to reduce the number of topics, whilst keeping in mind measurements of the quality of our classification.

lda_model = LdaModel(corpus=corpus, id2word=id2word, num_topics=5, random_state=42, passes=10, alpha="auto", per_word_topics=True)

coherence_model_lda = CoherenceModel(model=lda_model, texts=processed_texts, dictionary=id2word, coherence="c_v")
coherence_lda = coherence_model_lda.get_coherence()
print("Coherence Score: ", coherence_lda)

vis = gensimvis.prepare(lda_model, corpus, id2word)
vis

# In[]

# Let's optimize on the number of topics

# In this case, we just try for a number of topics from 3 to 10, and see what has the highest coherence score.

import numpy as np
possibilities = np.linspace(3, 10, num = 8)
possibilities


# We try each number of topics, and see what works!
from tqdm import trange
coherences = list()

for idx in trange(len(possibilities)):
    
    num_topics = possibilities[idx]
    # Estimate the model
    lda_model = LdaModel(corpus=corpus, id2word=id2word, num_topics=num_topics, random_state=42, passes=10, alpha="auto", per_word_topics=True)
    
    # Evaluate the model
    coherence_model_lda = CoherenceModel(model=lda_model, texts=processed_texts, dictionary=id2word, coherence="c_v")
    coherence_lda = coherence_model_lda.get_coherence()
    
    # Store the information
    coherences.append(coherence_lda)
# Put that in a pandas
optim_data = pd.DataFrame({'num_topics' : possibilities, 'coherence':coherences})


# Let's plot it

# Plotting
plt.figure(figsize=(10, 5))
plt.plot(optim_data['num_topics'], optim_data['coherence'], marker='o')
plt.title('Coherence Score by Number of Topics')
plt.xlabel('Number of Topics')
plt.ylabel('Coherence Score')
plt.xticks(optim_data['num_topics'])  # Ensure all topic counts are labeled
plt.grid(True)
plt.show()


# The model looks marginally better, that topics make more sense semantically, when the number is 6 or 9. We select 6.

lda_model = LdaModel(corpus=corpus, id2word=id2word, num_topics= 6, random_state=42, passes=10, alpha="auto", per_word_topics=True)
vis = gensimvis.prepare(lda_model, corpus, id2word)
vis

# In[]
# Some topics still appear very similar to each other. Now, we want to better understand what each topic is exactly about.
# To do this, we will extract the proportion of each topic for each document and add this information to our dataset.

num_topics = 6
# Prepare a dictionary to store the topic proportions for each document.
topic_proportions = {f'topic_{i}': [] for i in range(num_topics)}

# Extract topic proportions for each document in the corpus.
for bow in corpus:
    # Get the sparse distribution of topics for the document.
    sparse_distribution = lda_model.get_document_topics(bow, minimum_probability=0)
    # Initialize a full distribution with zero proportions for all topics.
    full_distribution = {topic: 0 for topic in range(num_topics)}
    # Update the full distribution with the actual topic proportions.
    full_distribution.update(dict(sparse_distribution))
    
    # Append the topic proportions to the corresponding lists.
    for topic_id, prop in full_distribution.items():
        topic_proportions[f'topic_{topic_id}'].append(prop)
        
# Add each topic proportion as a new column in the dataset.
for topic, proportions in topic_proportions.items():
    dataset[topic] = proportions

# Sort the dataset based on the proportions of topic_4 in descending order.
dataset.sort_values("topic_4", ascending=False)

# Filter and display documents with a high proportion (greater than 0.95) of topic_5.
dataset.loc[dataset['topic_5'] > 0.95, 'content']


# In[]:
# Now, we compare the two main Finnish parties' principle programs, with the aim to identify key themes and 
# sentiments in their political agendas:
# - the National Coalition Party
# - the Social Democratic Party (SDP).

# Main principles of the Parliamentary Group of the National Coalition Party

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import os

# Initialize Selenium WebDriver
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

# URL to scrape
url = "https://www.kokoomus.fi/principle-program/?lang=en"

# Function to scrape the content
def scrape_content(url):
    driver.get(url)
    time.sleep(5)  # Wait for the page to load

    # Extract the page source
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    # Find the content container (modify this as needed based on the actual HTML structure)
    content_container = soup.find('div', class_='container')
    if content_container:
        return content_container.get_text(separator=' ', strip=True)
    return ""

# Scrape the content
content = scrape_content(url)
driver.quit()

# Get the current working directory
current_directory = os.getcwd()

# Save the content to a file in the current directory
if content:
    principle_program_path = os.path.join(current_directory, 'principle_program.txt')
    with open(principle_program_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Content successfully written to {principle_program_path}")
else:
    print("Failed to scrape the content.")

# Save the content to a file
with open('principle_program.txt', 'w', encoding='utf-8') as f:
    f.write(content)

# In[]:

# Since we previously used spacy, we will now use the NLTK library to demonstrate a different approach. 
# As we have mentioned during the classes, it is a famous alternative.   

import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger') 
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
import os


def get_wordnet_pos(word):
    """Map POS tag to first character lemmatize() accepts"""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}

    return tag_dict.get(tag, wordnet.NOUN)

lemmatizer = WordNetLemmatizer()

principle_program_path = os.path.join(os.getcwd(), 'principle_program.txt')

if os.path.exists(principle_program_path):
    with open(principle_program_path, 'r', encoding='utf-8') as file:
        text = file.read()
else:
    raise FileNotFoundError(f"{principle_program_path} not found. Ensure the scraping step was successful.")

# Tokenize, lemmatize, and remove punctuation
tokens = word_tokenize(text)
lemmatized_tokens = [lemmatizer.lemmatize(token.lower(), get_wordnet_pos(token.lower())) for token in tokens if token.isalpha()]
lemmatized_text = ' '.join(lemmatized_tokens)

lemmatized_program_path = os.path.join(os.getcwd(), 'lemmatized_program.txt')

with open(lemmatized_program_path, 'w', encoding='utf-8') as file:
    file.write(lemmatized_text)
print(f"Lemmatized text successfully written to {lemmatized_program_path}")


# In[]:
from wordcloud import WordCloud
import matplotlib.pyplot as plt

lemmatized_program_path = os.path.join(os.getcwd(), 'lemmatized_program.txt')

if os.path.exists(lemmatized_program_path):
    with open(lemmatized_program_path, 'r', encoding='utf-8') as file:
        lemmatized_text = file.read()
else:
    raise FileNotFoundError(f"{lemmatized_program_path} not found. Ensure the lemmatization step was successful.")

wordcloud = WordCloud(width=800, height=400, background_color='white').generate(lemmatized_text)

# Display the word cloud
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.show()

# This is just a preliminary version, indeed the biggest words are "must", people", "national" and "party", let's remove these words.

# In[]:
    
# To exclude specific words from the analysis, we can introduce a step to filter out these words after tokenization and before 
# generating the word cloud. We now modify the script to exclude some words, such as "people", "must", "s", "national", and "party":
    
import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet, stopwords
from nltk.stem import WordNetLemmatizer
import os
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Function to get the part of speech (POS) tag for a word to assist lemmatization
def get_wordnet_pos(word):
    """Map POS tag to first character lemmatize() accepts"""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}
    return tag_dict.get(tag, wordnet.NOUN)

# Initialize the WordNet lemmatizer and stop words
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# Path to the file containing the principle program text
principle_program_path = os.path.join(os.getcwd(), 'principle_program.txt')

if os.path.exists(principle_program_path):
    with open(principle_program_path, 'r', encoding='utf-8') as file:
        text = file.read()
else:
    raise FileNotFoundError(f"{principle_program_path} not found. Ensure the scraping step was successful.")

# Define phrases to be combined
phrases_to_combine = {
    "european union": "europe",
    "european": "europe",
    "europe": "europe",
    "union": "europe"
}

# Replace phrases in the text
for phrase, replacement in phrases_to_combine.items():
    text = re.sub(r'\b{}\b'.format(phrase), replacement, text, flags=re.IGNORECASE)

# Define the list of words to exclude
exclude_words = {'people', 'must', 's', 'national', 'party', 'take', 'use', 'finland', 'allow', 'finnish', 'able', 'want', 'good', 'base', 'value','also', 'well','part','open','world'}

# Tokenize, lemmatize, and remove punctuation, stopwords, and specific words
tokens = word_tokenize(text)
lemmatized_tokens = [
    lemmatizer.lemmatize(token.lower(), get_wordnet_pos(token.lower())) 
    for token in tokens if token.isalpha() and token.lower() not in exclude_words and token.lower() not in stop_words
]
lemmatized_text = ' '.join(lemmatized_tokens)

# Path to save the lemmatized text
lemmatized_text_path = os.path.join(os.getcwd(), 'lemmatized_text.txt')

# Write the lemmatized text to a file
with open(lemmatized_text_path, 'w', encoding='utf-8') as file:
    file.write(lemmatized_text)
print(f"Lemmatized text successfully written to {lemmatized_text_path}")

# In[]

lemmatized_text_path = os.path.join(os.getcwd(), 'lemmatized_text.txt')

if os.path.exists(lemmatized_text_path):
    with open(lemmatized_text_path, 'r', encoding='utf-8') as file:
        lemmatized_text = file.read()
else:
    raise FileNotFoundError(f"{lemmatized_text_path} not found. Ensure the lemmatization step was successful.")

# Generate the word cloud with excluded words
wordcloud = WordCloud(width=800, height=400, background_color='white', stopwords=exclude_words).generate(lemmatized_text)

# Display the word cloud
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.show()


# In[]
# Again, we now use a different approach for sentiment analysis by employing the VADER sentiment analyzer.

# Initialize the VADER sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Read the lemmatized text from the file
if os.path.exists(lemmatized_text_path):
    with open(lemmatized_text_path, 'r', encoding='utf-8') as file:
        lemmatized_text = file.read()
else:
    raise FileNotFoundError(f"{lemmatized_text_path} not found. Ensure the lemmatization step was successful.")

# Perform sentiment analysis on the lemmatized text
sentiment_scores = analyzer.polarity_scores(lemmatized_text)

# Print sentiment analysis results
print(f"Sentiment analysis results for the text:")
print(f"Positive: {sentiment_scores['pos']}")
print(f"Neutral: {sentiment_scores['neu']}")
print(f"Negative: {sentiment_scores['neg']}")
print(f"Compound: {sentiment_scores['compound']}")

# The sentiment analysis results suggest that the text is predominantly neutral but with a strong positive tilt, 
# as evidenced by the high positive and compound scores. There is very little negative sentiment present.

# In[]
# The Social Democratic Party
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import os

# Initialize Selenium WebDriver
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

# URL to scrape
url = "https://www.sdp.fi/en/declaration-of-principles/"

# Function to scrape the content
def scrape_content(url):
    driver.get(url)
    time.sleep(5)  # Wait for the page to load

    # Extract the page source
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    # Find the content container (modify this as needed based on the actual HTML structure)
    content_container = soup.find('div', class_='container container--medium')
    if content_container:
        return content_container.get_text(separator=' ', strip=True)
    return ""

# Scrape the content
content = scrape_content(url)
driver.quit()

# Get the current working directory
current_directory = os.getcwd()

# Save the content to a file in the current directory
if content:
    extract_content_path = os.path.join(current_directory, 'extract_content.txt')
    with open(extract_content_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Content successfully written to {extract_content_path}")
else:
    print("Failed to scrape the content.")

# Save the content to a file
with open('extract_content.txt', 'w', encoding='utf-8') as f:
    f.write(content)

# In[]:

import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger') 
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
import os


def get_wordnet_pos(word):
    """Map POS tag to first character lemmatize() accepts"""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}

    return tag_dict.get(tag, wordnet.NOUN)

lemmatizer = WordNetLemmatizer()

extract_content_path = os.path.join(os.getcwd(), 'extract_content.txt')

if os.path.exists(extract_content_path):
    with open(extract_content_path, 'r', encoding='utf-8') as file:
        text = file.read()
else:
    raise FileNotFoundError(f"{extract_content_path} not found. Ensure the scraping step was successful.")

# Tokenize, lemmatize, and remove punctuation
tokens = word_tokenize(text)
lemmatized_tokens = [lemmatizer.lemmatize(token.lower(), get_wordnet_pos(token.lower())) for token in tokens if token.isalpha()]
lemmatized_text = ' '.join(lemmatized_tokens)

lemmatized_content_path = os.path.join(os.getcwd(), 'lemmatized_content.txt')

with open(lemmatized_content_path, 'w', encoding='utf-8') as file:
    file.write(lemmatized_text)
print(f"Lemmatized text successfully written to {lemmatized_content_path}")

# In[]:
from wordcloud import WordCloud
import matplotlib.pyplot as plt

lemmatized_content_path = os.path.join(os.getcwd(), 'lemmatized_content.txt')

if os.path.exists(lemmatized_content_path):
    with open(lemmatized_content_path, 'r', encoding='utf-8') as file:
        lemmatized_text = file.read()
else:
    raise FileNotFoundError(f"{lemmatized_content_path} not found. Ensure the lemmatization step was successful.")

wordcloud = WordCloud(width=800, height=400, background_color='white').generate(lemmatized_text)

# Display the word cloud
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.show()

# Again, this is just a preliminary version.

# In[]:
    
import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet, stopwords
from nltk.stem import WordNetLemmatizer
import os
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Function to get the part of speech (POS) tag for a word to assist lemmatization
def get_wordnet_pos(word):
    """Map POS tag to first character lemmatize() accepts"""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}
    return tag_dict.get(tag, wordnet.NOUN)

# Initialize the WordNet lemmatizer and stop words
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# Path to the file containing the principle program text
extract_content_path = os.path.join(os.getcwd(), 'extract_content.txt')

if os.path.exists(extract_content_path):
    with open(extract_content_path, 'r', encoding='utf-8') as file:
        text = file.read()
else:
    raise FileNotFoundError(f"{extract_content_path} not found. Ensure the scraping step was successful.")

# Define phrases to be combined
phrases_to_combine = {
    "european union": "europe",
    "european": "europe",
    "europe": "europe",
    "union": "europe"
}

# Replace phrases in the text
for phrase, replacement in phrases_to_combine.items():
    text = re.sub(r'\b{}\b'.format(phrase), replacement, text, flags=re.IGNORECASE)

# Define the list of words to exclude
exclude_words = {'must', 'social', 'provide', 'influence', 'create', 'economy', 'democratic', 'strong', 'every', 'need', 'mean', 'member', 'base', 'will', 'increase', 'part'}

# Tokenize, lemmatize, and remove punctuation, stopwords, and specific words
tokens = word_tokenize(text)
lemmatized_tokens = [
    lemmatizer.lemmatize(token.lower(), get_wordnet_pos(token.lower())) 
    for token in tokens if token.isalpha() and token.lower() not in exclude_words and token.lower() not in stop_words
]
lemmatized_text = ' '.join(lemmatized_tokens)

# Path to save the lemmatized text
lemmatized_text_path = os.path.join(os.getcwd(), 'lemmatized_content.txt')

# Write the lemmatized text to a file
with open(lemmatized_text_path, 'w', encoding='utf-8') as file:
    file.write(lemmatized_text)
print(f"Lemmatized text successfully written to {lemmatized_text_path}")

# In[]

lemmatized_text_path = os.path.join(os.getcwd(), 'lemmatized_content.txt')

if os.path.exists(lemmatized_text_path):
    with open(lemmatized_text_path, 'r', encoding='utf-8') as file:
        lemmatized_text = file.read()
else:
    raise FileNotFoundError(f"{lemmatized_text_path} not found. Ensure the lemmatization step was successful.")

# Generate the word cloud with excluded words
wordcloud = WordCloud(width=800, height=400, background_color='white', stopwords=exclude_words).generate(lemmatized_text)

# Display the word cloud
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.show()

# In[]

# Initialize the VADER sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Read the lemmatized text from the file
if os.path.exists(lemmatized_text_path):
    with open(lemmatized_text_path, 'r', encoding='utf-8') as file:
        lemmatized_text = file.read()
else:
    raise FileNotFoundError(f"{lemmatized_text_path} not found. Ensure the lemmatization step was successful.")

# Perform sentiment analysis on the lemmatized text
sentiment_scores = analyzer.polarity_scores(lemmatized_text)

# Print sentiment analysis results
print(f"Sentiment analysis results for the text:")
print(f"Positive: {sentiment_scores['pos']}")
print(f"Neutral: {sentiment_scores['neu']}")
print(f"Negative: {sentiment_scores['neg']}")
print(f"Compound: {sentiment_scores['compound']}")

# Overall Comparison
# From the wordclouds, we can notice that the National Coalition Party emphasizes economic development, individual rights
# and market freedom. On the other hand, SDP focuses more on democratic values, sustainability and social equality.
# However, both parties aim at enhancing societal well-being, even though they use different approaches.





# In[]: 
    