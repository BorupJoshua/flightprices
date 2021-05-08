from time import sleep, strftime
from random import randint
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from datetime import timedelta
from datetime import date
import pandas as pd
import smtplib


# Configuration Options

# List of airports you are willing to depart from
departing_airports = {
    "SGF",
    "BKG",
    "COU",
    "MCI"
}

# Lists of airports you would like to depart back home from
arrival_airports = {
    "NRT",
    "HND"
}

# Number of days to look in the future
# Recommended 293 since the main carriers don't post their prices atleast 330 days in advance, then give 30 days for the month view and an additional 7 days as a buffer.
days_to_look_ahead = 293

# The specific class on the website that represents the lowest fare
lowest_price_class_string = 'und0'

# Chromedriver's path
chromedriver_path = 'chromedriver.exe'

# Number of ADULT travelers, AS A STRING!
num_adults = '8'

# Kayak's url stuff, the first should not change, but the 2nd (kayak_closer) should be copied after the 2nd date in the url.
# TO DO: Create a system to automatically know number of travelers (in my case it's 8)
kayak_before_destination = 'https://www.kayak.com/flights/'
kayak_closer = '-flexible-calendar-10to14/'+num_adults+'adults?sort=bestflight_a&fs=cfc=0;bfc=0'


# Actual page scraping function
# INPUT: Two string IATA Codes
# OUTPUT: Integer to represent the price
def page_scrape(iataFROM, iataTO):

    print('Starting to scrape the results for '+iataFROM+' to '+iataTO)
    # Get the date object of today + days to look at (293 is default)
    future_date = date.today() + timedelta(days=days_to_look_ahead)

    # Add an additional 29 days to mark the end point
    future_date_plus_month = future_date + timedelta(days=29)

    # Convert the date time objects into strings
    date_start = future_date.strftime("%Y-%m-%d")
    date_end = future_date_plus_month = future_date.strftime("%Y-%m-%d")

    # Create the URL we're gonna be looking at, the url that doesn't change and the dates and iata codes
    url = ''+kayak_before_destination+iataFROM+'-'+iataTO+'/'+date_start+'/'+date_end+kayak_closer

    # Create the webdriver and start the chromdriver exe
    driver = webdriver.Chrome(executable_path=chromedriver_path)

    # Open the webpage
    driver.get(url)

    
    print('Opening webpage, waiting to load')
    # Wait for the page to fully populate the results
    sleep(50)

    # Find the element that has the specific class that represents the lowest price, then grab the price value
    day_container = driver.find_element_by_class_name(lowest_price_class_string)
    price_container = day_container.find_element_by_class_name('price')
    price = price_container.text

    # Close the driver as we're done here
    driver.close()

    # Filter out non numeric numbers from the container text
    numeric_filter = filter(str.isdigit, price)
    price_cleaned = "".join(numeric_filter)

    print(price_cleaned)

    # return the price
    return price_cleaned


    

sleep(2)

page_scrape('SGF','NRT')

sleep(2)

page_scrape('COU','NRT')


