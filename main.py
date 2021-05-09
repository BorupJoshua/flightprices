from time import sleep, strftime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
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
            if len(row) == 0:
                continue
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

    return min(dataset, key=operator.itemgetter(0))
# End return_lowest_in_timeframe

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
    lowest_today_str = str(lowest_tuple_today[0])+" ("+lowest_tuple_today[1]+")"

    # Add it to the data stack
    data.append(lowest_tuple_today)

    # Create new data stack that adheres how many data entires we want
    new_data = clean_stack(days_to_keep_data,data)

    # Save the new stack to storage
    save_stack(new_data)

    # Grab the lowest price overall
    lowest_tuple_overall = return_lowest_in_timeframe(days_to_keep_data,data)
    lowest_overall_str = str(lowest_tuple_overall[0])+" ("+lowest_tuple_overall[1]+")"

    # Grab the lowest monthly
    lowest_tuple_monthly = return_lowest_in_timeframe(30,data)
    lowest_monthly_str = str(lowest_tuple_monthly[0])+" ("+lowest_tuple_monthly[1]+")"

    # Grab the lowest weekly
    lowest_tuple_weekly = return_lowest_in_timeframe(7,data)
    lowest_weekly_str = str(lowest_tuple_weekly[0])+" ("+lowest_tuple_weekly[1]+")"

    # Discord integration

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


# End Main




if __name__ == '__main__':
    main()
