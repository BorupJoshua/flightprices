from time import sleep, strftime
from random import randint
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from datetime import timedelta
from datetime import date
import pandas as pd
import smtplib
import csv
import os.path
import requests
from discord import Webhook, RequestsWebhookAdapter



# Configuration Options

# List of airports you are willing to depart from
departing_airports = {
    "SGF",
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

# Number of days to keep data
days_to_keep_data = 90

# Frequency per day to run the script
number_of_iterations = 4

# The specific class on the website that represents the lowest fare
lowest_price_class_string = 'und0'

# Chromedriver's path
chromedriver_path = 'chromedriver.exe'

# Number of ADULT travelers, AS A STRING!
num_adults = '8'

# CSV Data File Name
csv_file_name = 'historical_data.csv'

# Discord Webhook File
webhook_file_path = 'webhook.txt'

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
    # TO DO: Actually make a holding function to wait until results are fully loaded, python loves to hang on sleep
    sleep(20)

    # Find the element that has the specific class that represents the lowest price, then grab the price value
    day_container = driver.find_element_by_class_name(lowest_price_class_string)
    price_container = day_container.find_element_by_class_name('price')
    price = price_container.text

    # Close the driver as we're done here
    driver.close()

    # Filter out non numeric numbers from the container text
    numeric_filter = filter(str.isdigit, price)
    price_cleaned = int("".join(numeric_filter))

    print(price_cleaned)

    # return the price
    return price_cleaned


# Load Stack from CSV if exists
# Create Empty Stack if it doesnt
def load_stack():
    if not (os.path.exists(csv_file_name)):
        open(csv_file_name, 'a+')
        return []

    data = []

    # Open up file and put data into a stack
    with open(csv_file_name) as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            if len(row) == 0:
                continue
            data.append(tuple(row))

    # Return the stack of tuples
    return data

# Saves the stack
def save_stack(data):

    # Opens the file for writing
    with open(csv_file_name, 'w', newline='') as file:

        # Write every tuple in the data provided
        csv_out = csv.writer(file)
        for row in data:
            csv_out.writerow(row)
        

def clean_stack(timeframe, data):
    
    while (data.size() > (timeframe * number_of_iterations)):
        data.pop(0)

    return data

def return_lowest_in_timeframe(timeframe, dataset):

    new_dataset = clean_stack(timeframe,data)

    return min(data, key = lambda t; t[0])


#Main Driver Function
def main():
    # Load data from file
    data = load_stack()

    # Create variables with dummy values
    lowest_price = 99999999
    flight_pair = ''

    # For every incoming and outgoing pair, scrape the page and compare prices
    for incoming in arrival_airports:
        for outgoing in departing_airports:

            print("Testing "+incoming+" and "+outgoing)

            # Scrape the page
            price = page_scrape(outgoing,incoming)

            # If the price is lower than our current lowest price, that's the new lowest price
            if (price < lowest_price):
                lowest_price = price
                flight_pair = outgoing+'-'+incoming
    
    # Create a new tuple of the lowest price and the flight pair string
    lowest_tuple_today = (lowest_price,flight_pair)

    # Add it to the data stack
    data.append(lowest_tuple_today)

    # Create new data stack that adheres how many data entires we want
    new_data = clean_stack(days_to_keep_data,data)

    # Save the new stack to storage
    save_stack(new_data)

    # Grab the lowest price overall
    lowest_tuple_overall = return_lowest_in_timeframe(days_to_keep_data,data)

    # Grab the lowest monthly
    lowest_tuple_monthly = return_lowest_in_timeframe(30,data)

    # Grab the lowest weekly
    lowest_tuple_weekly = return_lowest_in_timeframe(7,data)
=

    # Discord integration
    webhook_secret_file = open(webhook_file_path, 'r')

    webhook_secret = webhook_secret_file.read()

    message = "LOWEST PRICE CURRENTLY: $"+str(lowest_price)+", AIRPORT PAIR: "+flight_pair

    webhook = Webhook.from_url(webhook_secret, adapter=RequestsWebhookAdapter())
    webhook.send(message)




if __name__ == '__main__':
    main()
