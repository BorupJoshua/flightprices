from time import sleep, strftime
from random import randint
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import smtplib


# Configuration Options

days_to_look_ahead = 293

lowest_price_class_string = 'und0'

chromedriver_path = 'chromedriver.exe'



kayak_before_destination = 'https://www.kayak.com/flights/'
kayak_closer = '-flexible-calendar-10to14/8adults?sort=bestflight_a&fs=cfc=0;bfc=0'


def page_scrape(iataFROM, iataTO):

    date_start = '2022-03-01'
    date_end = '2022-03-30' 

    url = ''+kayak_before_destination+iataFROM+'-'+iataTO+'/'+date_start+'/'+date_end+kayak_closer

    
    driver = webdriver.Chrome(executable_path=chromedriver_path)
    driver.get(url)

    sleep(10)

    day_container = driver.find_element_by_class_name(lowest_price_class_string)
    price_container = day_container.find_element_by_class_name('price')
    price = price_container.text

    numeric_filter = filter(str.isdigit, price)
    price_cleaned = "".join(numeric_filter)

    print(price_cleaned)
    
    driver.close()


    

sleep(2)

page_scrape('SGF','NRT')


