from time import sleep, strftime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from datetime import timedelta
from datetime import date
from datetime import datetime
import csv
import os.path
import requests
from discord import Webhook, RequestsWebhookAdapter
import discord
import operator



# Configuration Options

#Airports you want to test, add a comma between every pair
departing_airports_str = "SGF, COU, MCI"
destination_airports_str = "NRT, HND"

# Number of days to look in the future
# Recommended 293 since the main carriers don't post their prices atleast 330 days in advance, then give 30 days for the month view and an additional 7 days as a buffer.
days_to_look_ahead = 293

# Number of days to keep data
days_to_keep_data = 90

# Frequency per day to run the script
number_of_iterations = 4

# Number of over night stays, as a string
nights = "10-14"

# Chromedriver's path
chromedriver_path = 'chromedriver.exe'

# Number of ADULT travelers
num_adults = 8

# CSV Data File Name
csv_file_name = 'historical_data.csv'

# Discord Webhook File
webhook_file_path = 'webhook.txt'

# ITA Matrix URL
url = 'https://matrix.itasoftware.com'

# Page element information
departing_from_id = 'cityPair-orig-0'

destination_id = 'cityPair-dest-0'

radio_button_id = 'gwt-uid-168'

calendar_date_id = 'calDate-0'

calendar_stay_id = 'calStay-0'

extra_stops_class = 'KIR33AB-a-G'

search_button_id = 'searchButton-0'

num_adults_xPath = '//*[@id="searchPanel-0"]/div/div/div[2]/div[1]/div/div/select'

lwest_price_class = 'KIR33AB-c-a'

# Actual page scraping function
# INPUT: Two string IATA Codes
# OUTPUT: Integer to represent the price
def page_scrape():

    #print('Starting to scrape the results for '+iataFROM+' to '+iataTO)

    # Get the date object of today + days to look at (293 is default)
    future_date = date.today() + timedelta(days=days_to_look_ahead)

    # Convert the date time objects into strings
    date_start = future_date.strftime("%m/%d/%Y")


    # Create the webdriver and start the chromdriver exe
    option = webdriver.ChromeOptions()
    option.add_argument('--disable-blink-features=AutomationControlled')

    driver = webdriver.Chrome(executable_path=chromedriver_path, options=option)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    # Open the webpage
    driver.get(url)
    
    print('Opening webpage, waiting to load')

    # Get the Dparting From input element
    departing_from_element = driver.find_element_by_id(departing_from_id)

    # Insert Departing From Airports String
    departing_from_element.send_keys(departing_airports_str)
    sleep(2)

    # Get the Destination input element
    destination_airports_element = driver.find_element_by_id(destination_id)

    # Insert Destination Airports String
    destination_airports_element.send_keys(destination_airports_str)
    sleep(2)

    # Get the "See calendar of lowest fares" radio button element
    radio_button_element = driver.find_element_by_id(radio_button_id)

    # Select the calendar radio button
    radio_button_element.click()
    sleep(2)

    # Wait until the departing date input box appears

    calendar_date_element = WebDriverWait(driver, 180).until(
        EC.presence_of_element_located((By.ID, calendar_date_id))
    )

    # Insert date string
    calendar_date_element.send_keys(date_start)
    sleep(2)

    # Get the Length of Stay input element  
    length_of_stay_element = driver.find_element_by_id(calendar_stay_id)

    # Insert lenght of stay string
    length_of_stay_element.send_keys(nights)
    sleep(2)

    # Get the number of adults drop down element
    number_of_adults_element = driver.find_element_by_xpath(num_adults_xPath)

    # Select number of adults
    adult_options = number_of_adults_element.find_elements_by_tag_name("option")
    adult_options[num_adults-1].click()
    sleep(2)

    # Get the Extra Stops drop down element
    # Since there's 3 instances of this drop down class, it's the 3rd one
    all_drop_downs_with_class = driver.find_elements_by_class_name(extra_stops_class)
    extra_stops_element = all_drop_downs_with_class[2]

    # Select no limit
    no_limit_option = extra_stops_element.find_element_by_tag_name("option")
    no_limit_option.click()
    sleep(2)

    # Get the Search Button Element
    search_button_element = driver.find_element_by_id(search_button_id)

    # Select Search button
    search_button_element.click()

    # Wait until lowest price class element is found
    lowest_price_element = WebDriverWait(driver, 180).until(
        EC.presence_of_element_located((By.CLASS_NAME, lwest_price_class))
    )

    # Grab the element text = Price
    price = lowest_price_element.text

    # Close the driver as we're done here
    driver.close()

    # Filter out non numeric numbers from the container text
    numeric_filter = filter(str.isdigit, price)
    price_cleaned = int("".join(numeric_filter))

    print(price_cleaned)

    # return the price
    return price_cleaned
#end page_scrape


# Load Stack from CSV if exists
# Create Empty Stack if it doesnt
# Input: Nothing
# Output: queue of tuples(int, string)
def load_stack():
    if not (os.path.exists(csv_file_name)):
        open(csv_file_name, 'a+')
        return []

    data = []

    # Open up file and put data into a stack
    with open(csv_file_name) as file:

        csv_reader = csv.reader(file)

        for row in csv_reader:

            # Ignore the row if it's empty
            if len(row) == 0:
                continue

            # Ensure the first slot is a integer
            row[0] = int(row[0])
            data.append(tuple(row))

    # Return the stack of tuples
    return data
# End load_stack

# Saves the stack
# Input: queue of tuples(int, string)
def save_stack(data):

    # Opens the file for writing
    with open(csv_file_name, 'w', newline='') as file:

        # Write every tuple in the data provided
        csv_out = csv.writer(file)
        for row in data:
            csv_out.writerow(row)
# End save_Stack
        
# Pops the top of the stack until we get the timeframe of data we want
# Input: Integer, queue of tuples(int,string)
# Output: queue of tuples(int, string)
def clean_stack(timeframe, data):
    
    while (len(data) > (timeframe * number_of_iterations)):
        data.pop(0)

    return data
# End Clean Stack

# Returns the lowest tuple in the timeframe provided
# Input: Integer, queue of tuples(int, string)
# Output: Integer
def return_lowest_in_timeframe(timeframe, dataset):

    new_dataset = clean_stack(timeframe,dataset)

    return min(new_dataset, key=operator.itemgetter(0))
# End return_lowest_in_timeframe

#Main Driver Function
def main():

    # ================= Page Scraping =================

    # Grab the price of the lowest price
    price = page_scrape()

    # ================= Data Evaluation ================= 

    # Load data from file
    data = load_stack()

    # Create a new tuple of the lowest price and the flight pair string
    lowest_tuple_today = (price, "SGF/COU/MCI-TYO")
    lowest_today_str = str(lowest_tuple_today[0])

    # Add it to the data stack
    data.append(lowest_tuple_today)

    # Create new data stack that adheres how many data entires we want
    new_data = clean_stack(days_to_keep_data,data)

    # Save the new stack to storage
    save_stack(new_data)

    # Grab the lowest price overall
    lowest_tuple_overall = return_lowest_in_timeframe(days_to_keep_data,data)
    lowest_overall_str = str(lowest_tuple_overall[0])

    # Grab the lowest monthly
    lowest_tuple_monthly = return_lowest_in_timeframe(30,data)
    lowest_monthly_str = str(lowest_tuple_monthly[0])

    # Grab the lowest weekly
    lowest_tuple_weekly = return_lowest_in_timeframe(7,data)
    lowest_weekly_str = str(lowest_tuple_weekly[0])

    # ================= Discord integration ================= 
    # You can remove this below and swap out a different way to show the results
    # For my case its through my personal Discord server. 

    # Open webhook file (secret!)
    webhook_secret_file = open(webhook_file_path, 'r')

    # Grab the url in the file
    webhook_secret = webhook_secret_file.read()

    # Create the webhook from the url
    webhook = Webhook.from_url(webhook_secret, adapter=RequestsWebhookAdapter())

    # Create the embeded object to send to discord
    embed=discord.Embed(title="Flight Prices Update", color=0xff0033)
    embed.set_author(name="FLIGHT WATCH DOG", url="https://matrix.itasoftware.com", icon_url="https://w7.pngwing.com/pngs/205/97/png-transparent-airplane-icon-a5-takeoff-computer-icons-flight-airplane.png")
    embed.add_field(name="Lowest Price Today", value=lowest_today_str, inline=False)
    embed.add_field(name="Lowest Price Weekly", value=lowest_weekly_str, inline=True)
    embed.add_field(name="Lowest Price Monthly", value=lowest_monthly_str, inline=True)
    embed.add_field(name="Lowest Price Overall", value=lowest_overall_str, inline=True)
    embed.set_footer(text="Updated: "+datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    webhook.send(embed=embed)

    #================= ================= ================= 

# End Main




if __name__ == '__main__':
    main()
