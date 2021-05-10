# flightprices
FlightPrices is a Python Script to Pull prices from a service that uses the ITA Matrix system.  It will store the lowest price into a CSV file and keep it for, by default, 90 days, or 90 days * 6 times.

Not included in this repo is the chromedriver, which you can download at https://chromedriver.chromium.org, and then place the .exe file into the same directory as the python script.

The current implementation will post the results onto Discord via a webhook which you will also have to provide yourself.  Simply create a .txt file and insert the webhook url into the file, then update the configs on the python script.


