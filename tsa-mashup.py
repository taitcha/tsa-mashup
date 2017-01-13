## IMPORT STATEMENTS

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


## CACHING FUNCTIONS
## Useful to use while you're testing your code.

# cached data source file name
cache_fname = "cached_results.txt"

try:
    fobj = open(cache_fname, 'rb')
    saved_cache = pickle.load(fobj)
    fobj.close()
except:
    raise Exception("Make sure you have cached_results.txt in the same directory as this code file.")
    #saved_cache = {}

def requestURL(baseurl, params = {}):
    """
    Returns the full URL for the request.
    :param baseurl: REST API root url
    :param params: Parameters dictionary for REST API
    :return: Returns the base url and parameters formatted as a REST API request
    """
    req = requests.Request(method = 'GET', url = baseurl, params = params)
    prepped = req.prepare()
    return prepped.url

def get_with_caching(base_url, params_diction, cache_diction, cache_fname):
    """
    Returns the cached response if there is an exact URL match in the cached file, otherwise makes new request and caches response.
    :param base_url: REST API root url
    :param params_diction: Parameters dictionary for REST API
    :param cache_diction: Cache dictionary, pickled responses
    :param cache_fname: File name of cached pickled responses
    :return: Returns cached file if available, otherwise returns new API request response
    """
    full_url = requestURL(base_url, params_diction)
    # step 1
    # print "full url: " + full_url
    if full_url in cache_diction:
        # step 2
        # print "retrieving data from the API associated with " + full_url
        return cache_diction[full_url]
    else:
        # step 3
        response = requests.get(base_url, params=params_diction)
        # print "adding saved data to cache file for " + full_url
        # add to the cache and save it permanently
        cache_diction[full_url] = response.text
        fobj = open(cache_fname, "wb")
        pickle.dump(cache_diction, fobj)
        fobj.close()
        return response.text

## REST API & METADATA REQUESTS

def GetTSAWaitTimes(airportCode):
    """
    Returns data from the TSA Wait Times API for a particular airport shortcode.
    :param airportCode: 3-letter shortcode of airport
    :return: Returns the full parsed json data from TSA Wait Times API
    """
    base_url = "http://apps.tsa.dhs.gov/MyTSAWebService/GetTSOWaitTimes.ashx"
    params_tsa_d = {}
    params_tsa_d['ap'] = airportCode
    params_tsa_d['output'] = 'json'
    try:
        ## Uncomment this line if you want to get with caching for testing purposes
        #tsa_result_diction = json.loads(get_with_caching(base_url, params_tsa_d, saved_cache, cache_fname))

        ## Comment out these two lines if you want to enable caching
        results_tsa = requests.get(base_url, params=params_tsa_d)
        tsa_result_diction = json.loads(results_tsa.text)

    except Exception, e:
        print "Error: Unable to load TSA wait times. Please try again."
        # print "Exception: %s" % str(e)
        # sys.exit(1)
        quit()
    return tsa_result_diction

def GetTSAMetadata():
    """Returns the full set of metadata for airports, using the TSAAirport class, from the apcp.xml file.
    In the future, this file should be checked against the checksum file online to ensure it's the latest update.
    :return: Returns the parsed XML data from the TSA metadata file
    """
    airport_fname = "apcp.xml"
    # In future, get from the web to make sure data is fresh
    # http://www.tsa.gov/data/apcp.xml
    # checksum: http://www.tsa.gov/data/apcp.checksum.xml
    try:
        airportTree = ET.parse(airport_fname)
    except Exception, e:
        print "Error: The TSA Airport metadata file apcp.xml could not be found in the program directory. Please upload and try again."
        # print "Exception: %s" % str(e)
        # sys.exit(1)
        quit()
    return airportTree

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
    params_google_d = {}
    params_google_d['units'] = units
    params_google_d['origins'] = origin
    params_google_d['destinations'] = airportCode
    params_google_d['key'] = key
    try:
        ## Uncomment this line if you want to get with caching for testing purposes
        #google_result_diction = json.loads(get_with_caching(base_url, params_google_d, saved_cache, cache_fname))

        ## Comment out these two lines if you want to enable caching
        results_google = requests.get(base_url, params=params_google_d)
        google_result_diction = json.loads(results_google.text)

    except Exception, e:
        print "Error: Unable to load distance to airport from Google Distance Matrix. Please try again."
        # print "Exception: %s" % str(e)
        # sys.exit(1)
        quit()
    return google_result_diction

def LoadTSAMetadata():
    """
    Loads TSAAirports into an airport metadata dictionary
    :return: Returns dictionary of TSA metadata airport instances
    """
    TSAairportTree = GetTSAMetadata()
    TSAairportRoot = TSAairportTree.getroot()
    TSAairportDict = {}
    for airport in TSAairportRoot:
        airportDict = TSAAirport(airport)
        TSAairportDict[airportDict.shortcode] = airportDict
    return TSAairportDict

## TSAAIRPORT CLASS

class TSAAirport:
    """
    Used to create instances of airports containing data from the TSA airport metadata file.
    """
    def __init__(self, airport):
        self.name = airport.find('name').text
        self.shortcode = airport.find('shortcode').text
        self.city = airport.find('city').text
        self.state = airport.find('state').text
        self.latitude = airport.find('latitude').text
        self.longitude = airport.find('longitude').text
        self.utc = airport.find('utc').text
        self.dst = airport.find('dst').text
        self.precheck = airport.find('precheck').text
        self.checkpoints = []
        tmpCheckpoints = airport.find('checkpoints')
        for checkpoint in tmpCheckpoints.findall('checkpoint'):
            checkpointDict = {}
            checkpointDict["id"] = checkpoint.find('id').text
            checkpointDict["longname"] = checkpoint.find('longname').text
            checkpointDict["shortname"] = checkpoint.find('shortname').text
            self.checkpoints.append(checkpointDict)

    def hasTSAPrecheck(self):
        """
        TSA Precheck allows travelers to skip the security checkpoint lines
        :return: Returns True if the airport has TSA Precheck, false otherwise
        """
        return self.precheck == "true"

    def numCheckpoints(self):
        """
        Useful to know the number of checkpoints at the instance airport
        :return: Returns the number of TSA security checkpoints
        """
        return len(self.checkpoints)

## TSAWAITTIMES CLASS

class TSAWaitTimes:
    """
    Combines TSA metadata on checkpoints and TSA wait times
    """
    def __init__(self, airportCode, TSAairportDict):
        TSAdump = GetTSAWaitTimes(airportCode)
        self.airportCode = airportCode
        self.AllWaitTimes = TSAdump
        self.CheckpointWaitTimes = TSAairportDict[airportCode].checkpoints
        self.TSAairportDict = TSAairportDict
        # list comprehension, dump wait times into appropriate security gate buckets
        for checkpoint in self.CheckpointWaitTimes:
            checkpoint["WaitTimes"] = [waitTime for waitTime in self.AllWaitTimes["WaitTimes"] if waitTime["CheckpointIndex"] == checkpoint["id"]]

    def AllCheckpointWaitTimes(self):
        """
        Returns airport security checkpoint wait times as reported by TSA Wait Times REST API
        :return: Returns all wait times, sorted by checkpoint
        """
        return self.CheckpointWaitTimes

    def OneCheckpointWaitTimes(self, chk):
        """
        Returns all wait times for one security checkpoint
        :param chk: The Security Checkpoint ID being passed
        :return: (index starts at zero, TSA IDs start at 1, hence the -1)
        """
        return self.CheckpointWaitTimes[chk-1]

    def AvgAllWaitTime(self, rng=5):
        """
        Averages the last X (rng) wait times regardless of checkpoint. It rounds up to be conservative.
        TSA wait times are in 10-minute increments, so 0 = no wait time, 1 = 1 to 10 minutes wait, etc.
        :param rng: The number of Wait Time records to take into account, starting from the newest. Defaults to last 5 wait times.
        :return: Returns average in seconds.
        """
        tot = 0
        for num in range(rng):
            tot += int(self.AllWaitTimes["WaitTimes"][num]["WaitTime"])
        # Multiply TSA values by 10 minute increments, in seconds (10*60=600)
        newTot = math.ceil(tot / float(rng)) * 600
        return int(newTot)

    def WorstWaitTime(self):
        """
        Provides the worst time in the entire TSA Wait Time response.
        Ties are sorted by newest reported time first.
        :return: Returns a tuple of the datestamp and longest checkpoint wait time.
        """
        unsortedList = {}
        for x in self.AllWaitTimes["WaitTimes"]:
            unsortedList[x["Created_Datetime"]] = x["WaitTime"]
        tmpList = unsortedList.items()
        sortList = sorted(tmpList, key=lambda k: k[1], reverse=True)
        return (sortList[0][0], int(sortList[0][1]) * 600)

    def AvgOneWaitTime(self, chk, rng=5):
        """
        Averages the last rng wait times for chk checkpoint. Rounds up to be conservative.
        Takes into account there may not be enough wait times for that checkpoint listed, and averages the amount it gets.
        :param chk: The Security Checkpoint ID being passed
        :param rng: The number of Wait Time records to take into account, starting from the newest. Defaults to last 5 wait times.
        :return: Returns average in seconds.
        """
        tot = 0
        count = 0

        for num in range(rng):
            try:
                tot += int(self.CheckpointWaitTimes[chk-1]["WaitTimes"][num]["WaitTime"])
                count += 1
            except:
                # print "Not enough wait times reported by TSA for that checkpoint"
                pass
        # Multiply TSA values by 10 minute increments, in seconds (10*60=600)
        newTot = math.ceil(tot / float(count)) * 600
        return int(newTot)

    def slowestWaitTimeNow(self, rng=5):
        """
        Checks the newest wait time for each checkpoint and provides the slowest one.
        :param rng: The number of Wait Time records to take into account, starting from the newest. Defaults to last 5 wait times.
        :return: Returns slowest current wait time in seconds.
        """
        numCheckpoints = self.TSAairportDict[self.airportCode].numCheckpoints()
        try:
            slowestTime = self.CheckpointWaitTimes[0]["WaitTimes"][0]["WaitTime"]
            for checkpoint in range(numCheckpoints):
                if self.CheckpointWaitTimes[checkpoint]["WaitTimes"][0]["WaitTime"] > slowestTime:
                    slowestTime = self.CheckpointWaitTimes[checkpoint]["WaitTimes"][0]["WaitTime"]
        except:
            # print "one or more checkpoints did not have any wait times reported"
            slowestTime = 0
        return int(slowestTime) * 600


## AIRPORT CLASS

class Airport:
    """
    Combines TSA Airport metadata data with TSA wait times
    """
    def __init__(self, airportCode, TSAairportDict):
        self.airportCode = airportCode
        self.name = TSAairportDict[airportCode].name
        self.shortcode = TSAairportDict[airportCode].shortcode
        self.city = TSAairportDict[airportCode].city
        self.state = TSAairportDict[airportCode].state
        self.latitude = TSAairportDict[airportCode].latitude
        self.longitude = TSAairportDict[airportCode].longitude
        self.utc = TSAairportDict[airportCode].utc
        self.precheck = TSAairportDict[airportCode].precheck
        self.checkpoints = TSAWaitTimes(airportCode, TSAairportDict)

## GOOGLEDISTANCE CLASS

class GoogleDistance:
    """
    Used to create instances of trip distances from origin address to airport with Google Distance Matrix API.
    """
    def __init__(self, origin, airportCode, key, units="imperial"):
        self.origin = origin
        self.airportCode = airportCode
        self.key = key
        self.units = units

        try:
            self.DistanceDict = GetDistance(origin, airportCode, key)
            self.durationText = self.DistanceDict["rows"][0]["elements"][0]["duration"]["text"]
            self.durationValue = self.DistanceDict["rows"][0]["elements"][0]["duration"]["value"]
            self.distanceText = self.DistanceDict["rows"][0]["elements"][0]["distance"]["text"]
            self.distanceValue = self.DistanceDict["rows"][0]["elements"][0]["distance"]["value"]
        # except KeyError, e:
        except:
            print "The entered origin or destination does not exist. Please try again."
            # print 'KeyError - error message: "%s"' % str(e)
            self.durationText = ""
            self.durationValue = 0
            self.distanceText = ""
            self.distanceValue = 0

        self.status = self.DistanceDict["status"]
        self.originAddress = self.DistanceDict["origin_addresses"][0]
        self.destinationAddress = self.DistanceDict["destination_addresses"][0]

    def __str__(self):
        returnStr = "Origin: " + self.originAddress +  "\nDestination: " + self.destinationAddress + "\nDuration: " + self.durationText + "\nDistance: " + self.distanceText
        return returnStr

    def PessimisticDuration(self):
        #just for laughs
        return int(self.durationValue * 1.25)


## TRIP CLASS
class Trip:
    """
    Creates a master class of the trip, including airport, security wait times, and distance with traffic data
    """
    def __init__(self, origin, airportCode, key, TSAairportDict, units="imperial"):
        self.origin = origin
        self.airportCode = airportCode
        self.key = key
        self.units = units
        self.TSAairportDict = TSAairportDict

        try:
            self.airport = Airport(airportCode, TSAairportDict)
        except KeyError, e:
            print "The entered airport shortcode does not exist. Please try again."

        try:
            self.distance = GoogleDistance(origin, airportCode, key)
        except KeyError, e:
            print "The entered origin or destination does not exist. Please try again."
            # print 'KeyError - error message: "%s"' % str(e)
        except AttributeError, e:
            pass


## GETUSERINPUT FUNCTION

def GetUserInput():
    """
    Requests trip variables from user.
    :return: Returns user responses (destination shortcode, departure address, has TSA precheck, international flight, checkedBags, returning a rentalCar)
    """
    while True:
        trip_destination = raw_input("Enter your destination airport shortcode (3 letters): \n>>")
        if len(trip_destination) == 3:
            break
        else:
            print "The shortcode must be 3 letters, please try again."

    trip_departure = raw_input("Enter your departure address: \n>>")

    while True:
        tmp_input = raw_input("Do you have TSA Precheck? (Enter y/n): \n>>")
        if (tmp_input.upper() == "Y"):
            trip_precheck = True
            break
        elif (tmp_input.upper() == "N"):
            trip_precheck = False
            break
        else:
            print "Please enter 'y' or 'n'."

    while True:
        tmp_input = raw_input("Is this an international flight? (Enter y/n): \n>>")
        if (tmp_input.upper() == "Y"):
            trip_international = True
            break
        elif (tmp_input.upper() == "N"):
            trip_international = False
            break
        else:
            print "Please enter 'y' or 'n'."

    while True:
        tmp_input = raw_input("Will you be checking bags? (Enter y/n): \n>>")
        if (tmp_input.upper() == "Y"):
            trip_checkedBags = True
            break
        elif (tmp_input.upper() == "N"):
            trip_checkedBags = False
            break
        else:
            print "Please enter 'y' or 'n'."

    while True:
        tmp_input = raw_input("Will you be returning a rental car? (Enter y/n): \n>>")
        if (tmp_input.upper() == "Y"):
            trip_rentalCar = True
            break
        elif (tmp_input.upper() == "N"):
            trip_rentalCar = False
            break
        else:
            print "Please enter 'y' or 'n'."

    while True:
        tmp_input = raw_input("Are you a pessimist? (Enter y/n): \n>>")
        if (tmp_input.upper() == "Y"):
            trip_pessimistic = True
            break
        elif (tmp_input.upper() == "N"):
            trip_pessimistic = False
            break
        else:
            print "Please enter 'y' or 'n'."

    return (trip_destination, trip_departure, trip_precheck, trip_international, trip_checkedBags, trip_rentalCar, trip_pessimistic)

def CalcBuffer(UserTrip, trip_precheck, trip_international, trip_checkedBags, trip_rentalCar):
    """
    Calculates the total buffer based on user responses.
    :param trip_precheck: If the user has TSA Precheck
    :param trip_international: If it's an international flight (otherwise, assume domestic)
    :param trip_checkedBags: If the user will be checking in bags
    :param trip_rentalCar: If the user will be returning a rental car
    :return: Return total trip buffer in seconds (time to allow besides trip time and security checkpoint delays)
    """
    ## All default buffer values expressed in seconds
    domestic_buffer = 4500
    international_buffer = 10800
    checkedBags_buffer = 900
    returnRentalCar_buffer = 1800

    total_buffer = 0
    if trip_precheck:
        if UserTrip.airport.precheck == "false":
            total_buffer += UserTrip.airport.checkpoints.slowestWaitTimeNow()
    else:
        total_buffer += UserTrip.airport.checkpoints.slowestWaitTimeNow()

    if trip_international:
        total_buffer += international_buffer
    else:
        total_buffer += domestic_buffer

    if trip_checkedBags:
        total_buffer += checkedBags_buffer

    if trip_rentalCar:
        total_buffer += returnRentalCar_buffer

    return total_buffer


## MAIN PROGRAM LOOP

def Main1():
    """
    Central program loop.
    :return: end of program
    """
    # Set the Google Distance Matrix API Key
    google_key = None  # paste your Google API key here
    if not google_key:
        google_key = raw_input(
            "Enter your Google API key, or paste it in the .py file to avoid this prompt in the future: \n>>")

    # Load the TSA Airport Metadata into a dictionary
    TSAairportDict = LoadTSAMetadata()

    # Uncomment to set values without going through interface raw_input requests for testing
    # trip_destination = "DCA"
    # trip_departure = "Washington,DC"
    # trip_precheck = True
    # trip_international = False
    # trip_checkedBags = False
    # trip_rentalCar = False
    # trip_pessimistic = True

    print "\n*********\n"

    print "Welcome to flightCALC"
    print "This program calculates when you should leave to catch your flight based on real-time conditions."

    print "\n*********\n"

    # Comment out below to request values from user rather than using preset values above, for testing
    trip_destination, trip_departure, trip_precheck, trip_international, trip_checkedBags, trip_rentalCar, trip_pessimistic = GetUserInput()

    print "\n*********\n"

    # Create a trip instance
    try:
        UserTrip = Trip(trip_departure, trip_destination, google_key, TSAairportDict)
    except AttributeError, e:
        pass

    # Set total buffer time based on user variables
    total_time = 0
    total_buffer = CalcBuffer(UserTrip, trip_precheck, trip_international, trip_checkedBags, trip_rentalCar)

    if trip_pessimistic:
        total_traveltime = UserTrip.distance.PessimisticDuration()
    else:
        total_traveltime = UserTrip.distance.durationValue

    total_time = total_buffer + total_traveltime

    print "Departing from:", UserTrip.origin
    print "Going to:", UserTrip.airport.name
    print "\n"

    # Set response based on total time accrued
    if total_time > 3600:
        total_hours = total_time / 3600
        total_min = (total_time % 3600) / 60
        print "Leave for the airport {} hours and {} minutes before the scheduled departure.".format(total_hours, total_min)
    elif total_time > 60:
        total_min = total_time / 60
        print "Leave for the airport {} minutes before the scheduled departure.".format(total_min)
    else:
        print "Total time is less than a minute. Did you put the airport as your departure address?"

    # Print additional information
    print "\n"
    print "This estimate was calculated based on current traffic conditions and TSA checkpoint wait times."
    print "Travel time:", UserTrip.distance.durationValue / 60, "minutes."
    print "Checkpoint wait time:", UserTrip.airport.checkpoints.slowestWaitTimeNow() / 60, "minutes."
    print "Average wait time:", UserTrip.airport.checkpoints.AvgAllWaitTime() / 60, "minutes."
    worstWaitDate, worstWaitTot  = UserTrip.airport.checkpoints.WorstWaitTime()
    print "Slowest wait time reported:", int(worstWaitTot) / 60, "minutes, at", worstWaitDate
    print "Buffer time:", total_buffer / 60, "minutes."
    print "\n"
    print UserTrip.distance

    print "\n*********\n"

    return

# Calls the main program loop to start the program
Main1()