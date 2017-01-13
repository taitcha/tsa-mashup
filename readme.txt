TSA-Mashup Readme

***

AUTHOR

Tait Chamberlain
tachambe@umich.edu
http://www.taitcha.net

***

DESCRIPTION

This project combines the TSA Security Checkpoint Wait Times API and Google Maps Distance Matrix API to estimate when you should leave for the airport. It calls Google to calculate predicted travel time based on start address and airport, checks current TSA checkpoint wait times at that airport, and provides an estimated travel time based on both factors, as well as user variables such as whether they have TSA Precheck and are pessimistic. It has some useful classes for anyone looking to play around with TSA SCWT API data in their own projects.

***

REQUIREMENTS

In order to run the code as-is, you’ll need to get your own Google Maps Distance Matrix API Key, which you can apply for here: https://developers.google.com/maps/documentation/distance-matrix/

Written for Python 2.7.10

***

FILES INCLUDED

tsa-mashup.py
This file is the main program.

cached_results.txt
Stores the cached pickled responses for running the program offline. Responses from both Google and the TSA APIs are returned in JSON.

apcp.xml
Stores the TSA Airport metadata necessary to make sense of the data returned from the TSA Security Checkpoint Wait Times API. The program parses the XML and loads up a dictionary of TSAairport class instances to combine with returned API data.

readme.txt
Readme file for the program.

***

PACKAGES NEEDED

# Unittest used for testing purposes
import unittest
# Json used to parse REST API request results
import json
# Requests used to pull REST API results
import requests
# Pickle used for caching REST API request results
import pickle
# ET used for parsing TSA Metadata XML
import xml.etree.ElementTree as ET
# Math used for rounding up
import math
# String used for uppercase conversions
import string

***

APIS USED

The MyTSA Web Service API
def GetTSAWaitTimes(airportCode):
    """
    Returns data from the TSA Wait Times API for a particular airport shortcode.
    :param airportCode: 3-letter shortcode of airport
    :return: Returns the full parsed json data from TSA Wait Times API
    """
    base_url = "http://apps.tsa.dhs.gov/MyTSAWebService/GetTSOWaitTimes.ashx"
Documentation: https://www.dhs.gov/mytsa-api-documentation
Needs the airport metadata contained here to make sense of things: http://www.tsa.gov/data/apcp.xml
Note: It returns the last 25 wait times, but these can be for any checkpoint and are not necessarily reported regularly. Also, the wait times are in 10-minute increments, with 0 indicating no wait, and 1 indicating 1-10 minute wait, etc. They do not make this very clear. Valid parameters include ap (airport), output (json), st (state), pc (TSA PreCheck line), al (airline). The airport parameter is required.

Google Distance Matrix API
def GetDistance(origin, airportCode, key, units="imperial"):
    """
    Gets and returns the processed json response from the Google Distance Matrix API
    :param origin: Where the trip to the airport starts
    :param airportCode: 3-letter shortcode of airport
    :param key: Google API key
    :param units: Measurement return from Google API, can also be metric
    :return: Returns the processed json response
    """
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
Documentation: https://developers.google.com/maps/documentation/distance-matrix/
Requires a key which I've already secured, and allows up to 2500 requests per month for free, which should be sufficient for the project. Required parameters are origins, destinations, and key (API key). There are many optional parameters, including transit_mode and traffic_model.
Note that distances are returned in meters and trip times in seconds, regardless of imperial or metric parameters (this only affects the text values returned).

***

LICENSE

BSD 2