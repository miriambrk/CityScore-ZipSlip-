# Dependencies
import requests as req
import json
import zipcodes
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import http.client
from datetime import datetime
import time as time

# Use the google API to get a list of points of interest
def barfinder(lat, lng):
    # Google API Key
    gkey = "AIzaSyC3VaB3zuIfUjWkuK4rkhpBbt8EZCakNO4"

    # types of points of interest we care about
    target_types = ["liquor_store", "gym", "park", "shopping_mall", "grocery_or_supermarket", "movie_theater"]
    
    #create a blank dictionary to store results
    results = {}
    
    # loop through each target type and gather the number of each nearby
    for target in target_types:
        
        # set default values
        count = 0
        x = True
        
        # while loop that uses google radar to gather our numbers
        while x == True:
            
            # take in latitude and longitude, set the search radius to 5 miles (8k meters)
            target_area = {"lat": lat, "lng": lng}
            target_radius = 8000

            # create the target urls and use requests to gather the necessary data
            target_url = "https://maps.googleapis.com/maps/api/place/radarsearch/json" \
                "?types=%s&location=%s,%s&radius=%s&key=%s" % (
                    target, target_area["lat"], target_area["lng"], target_radius,
                    gkey)

            places_data = req.get(target_url).json()

            # use the len function to find the count of results
            numbers = len(places_data["results"])

            # use a series of if statments to check if we returned results. Run a second time if no results showed up as a check
            if numbers > 0:
                results[target.replace("_", " ").title()] = numbers
                x = False
            elif count == 1:
                x = False
            else:
                count += 1
    
    # return the results
    return results

#---------------------------------------------------------------#
# pie plot of all of the points of interest as percentage of points of interest
def pie_plot(rst):
    # create a dataframe
    pie_df = pd.DataFrame.from_dict(rst, orient = 'index')

    # get the sum of points of interest
    tot_results = pie_df.sum()

    # turn the data frame into percentages
    pie_df = (pie_df/tot_results)*100

    # make the graph labels
    labels = pie_df.index

    fig = plt.figure(figsize = [10,10])
    plt.pie(pie_df, shadow=True, startangle=140, labels = labels, autopct="%1.1f%%", pctdistance = .95)

    plt.axis("equal")
    plt.title("% of Points of Interest")
    plt.savefig("test.png")
    plt.show()


#---------------------------------------------------------------#

# Function requires a latitude and longitude value
# Call this function to generate census population data for 2010 - 2016
def cen_block_query(lat,lng):
    # Queries Census for county/State associated to Lat/Long
    # API Info (No Key Required):  https://www.fcc.gov/general/census-block-conversions-api
    cen_block_url = ('http://data.fcc.gov/api/block/find?format=json&latitude=%s&longitude=%s&showall=true' % (lat, lng))
    lat_lon_county = req.get(cen_block_url).json()
    county_name = lat_lon_county['County']['name']
    state_name = lat_lon_county['State']['name']
    county_census_pop = pd.read_csv('Resources/co-est2016-alldata.csv',\
                                encoding="ISO-8859-1").apply(lambda x: x.astype(str).str.lower())
    # Match County and State name to retrieve population information from 2010 through 2016
    for index, row in county_census_pop.iterrows():
        if str.lower(county_name) in row['CTYNAME'] and row['STNAME'] == str.lower(state_name):
            years = ['2010','2011','2012','2013','2014','2015','2016']
            pops = []
            pops.append(int(row['POPESTIMATE2010']))
            pops.append(int(row['POPESTIMATE2011']))
            pops.append(int(row['POPESTIMATE2012']))
            pops.append(int(row['POPESTIMATE2013']))
            pops.append(int(row['POPESTIMATE2014']))
            pops.append(int(row['POPESTIMATE2015']))
            pops.append(int(row['POPESTIMATE2016']))           
            pop_dict = {'Years': years, 'Population': pops}
            # Return a dataframe with population value for each year
            pop_est = pd.DataFrame(pop_dict)
        else:
            next    
    return pop_est, county_name, state_name

#---------------------------------------------------------------#
# call this function to present a line graph of population change
def census_plot(pop_est,county_name,state_name):
    pop_len = len(pop_est['Population'])
    _2010 = pop_est['Population'][1]
    _2016 = pop_est['Population'][pop_len -1]
    if _2010 < _2016:
        #
        diff_ = (round(((_2016 - _2010)/ _2016) * 100))
        diff_str = "Note:\nIncrease of population by\n" + str(diff_) + "% from 2010 to 2016"
    elif _2010 > _2016:
        diff_ = (round(((_2010 - _2016)/ _2010) * 100))
        diff_str = "Note:\nDecrease of population by\n" + str(diff_) + "% from 2010 to 2016"
    else:
        diff_str = "Note:\nPopulation estimated as\nthe same from 2010 to 2016"
    ax = pop_est.plot(figsize = (8,6),color='blue', legend=False, marker = '*',markersize=15)
    ax.set_xticklabels(pop_est['Years'], fontsize=13, rotation=45)
    plt.grid()
    plt.figtext(0.91,0.45,diff_str,fontsize=12)
    plt.title("Census Population Estimates (%s County, %s)"%(county_name,state_name), fontsize = 14)
    plt.ylabel("Population", fontsize=14)
    return plt.show()

#---------------------------------------------------------------#
# Call this function to capture a DF that includes yearly changes in population
def population_df_generator(pop_est):
    pop_len = len(pop_est['Population'])
    pop_diff = [0]
    pop_diff_prcnt = [0]
    for x in range(pop_len-1):
        diff = (pop_est['Population'][x+1] - pop_est['Population'][x])
        pop_diff.append(diff)
        diff_prcnt = round(((diff/ pop_est['Population'][x]) * 100),2)
        pop_diff_prcnt.append(diff_prcnt)
    census_pop_master_df = pop_est
    census_pop_master_df['Difference'] = pop_diff
    census_pop_master_df['Percent Change'] = pop_diff_prcnt
    return census_pop_master_df

#---------------------------------------------------------------#
# Function to store Zillow home values and monthly rental prices for 2013-2017 quarters
# Function requires a zip code string; returns data frame

def get_home_data(zip):
    zip_code = int(zip)
    
    #create lists for the Zillow data 
    home_values=[]
    monthly_rentals=[]
    periods = []
    years=["2013","2014","2015","2016","2017"]
    months=["03","06","09","12"]
    
    
    ## Zillow Home Value Index (ZHVI) is a time series tracking the monthly median home value
    # get the data just for the input zip code
    all_homes = pd.read_csv("Resources/Zip_Zhvi_AllHomes.csv")
    zc_all_homes = all_homes[all_homes["RegionName"] == zip_code].iloc[0]

    ## Zillow Rental Index (ZRI) is a time series tracking the monthly median rental
    all_rental_homes = pd.read_csv("Resources/Zip_Zri_AllHomes.csv")
    zc_all_rental_homes = all_rental_homes[all_rental_homes["RegionName"] == zip_code].iloc[0]
    
    #get the home value and monthly rental data for the years/months specified above
    for y in years:
        for m in months:
            col_name = "%s-%s" % (y,m)

            try:
                #get the data for this column name
                home_value = zc_all_homes[col_name]
                rent = zc_all_rental_homes[col_name]
                home_values.append(home_value)
                monthly_rentals.append(rent)
                periods.append(col_name)
                #print(col_name, home_value, rent)
            except:
                print("no value for: %s" % col_name)
                    
    #store rent and house prices into a DF
    zillow_df=pd.DataFrame({"period": periods, 
                        "home_value": home_values,
                        "monthly_rent": monthly_rentals})
    return zillow_df, periods

#---------------------------------------------------------------#
# Function to plot Zillow home values and monthly rental prices for 2013-2017 quarters
# Function requires a DF with the Zillow info and the zip code (string)
def plot_homes(df, zip, periods):
    #plot the home values 
    x_ticks = periods
    x_axis = np.arange(1,20,1)
    y_axis = df['home_value']
    plt.xticks(x_axis, x_ticks, rotation='vertical')
    plt.legend
    plt.plot(x_axis, y_axis)
    plt.ylabel("Home Prices ($)")
    plt.title("%s Home Sales 2013-2017" % zip)
    #save the plot??
    plt.show()
    
    #plot the monthly rentals
    x_ticks = periods
    x_axis = np.arange(1,20,1)
    y_axis = df['monthly_rent']
    plt.xticks(x_axis, x_ticks, rotation='vertical')
    plt.legend
    plt.plot(x_axis, y_axis)
    plt.xlabel("Recent Quarters")
    plt.ylabel("Montly Rents ($)")
    plt.title("%s Monthly Rents 2013-2017" % zip)
    plt.show()

#---------------------------------------------------------------#
# Function to store various information about a location, such as walkability score, market health index, schools
# Function requires a zip code string, latitude and longitude; returns ?
def get_zip_factors (zip, lat, lng):
    #1) Market Health Index: 
    # This index indicates the current health of a given region’s housing market relative to other markets nationwide. 
    # It is calculated on a scale of 0 to 10, with 0 = the least healthy markets and 10 = the healthiest markets.
    market_health_index = pd.read_csv("Resources/MarketHealthIndex_Zip.csv",encoding="ISO-8859-1")
    zip_market_health = market_health_index[market_health_index["RegionName"] == int(zip)].iloc[0]
    market_health = zip_market_health['MarketHealthIndex']
    print("Market Health: %s" % market_health)
    
    #2) ##get walkability, transit and bike scores from Walk Score once I have an API.
    walk_api_key = "ca8240c847695f334874949c406f04aa"
    walk_url = "http://api.walkscore.com/score?format=json&"
    # Build query URL
    query_url = walk_url  + "&lat=" + str(lat) + "&lon=" + str(lng) + "&transit=1&bike=1" + "&wsapikey=" + walk_api_key
    walk_response = req.get(query_url).json()

    # Get the neighborhood data from the response
    walk_score = walk_response['walkscore']
    walk_description=walk_response['description']
    try:    
        bike_score = walk_response['bike']['score']
        bike_description = walk_response['bike']['description']
    except:
        print("no bike score")
        bike_score = 0
        bike_description = ""
    print("Walkability and Bikability Scores: %s: %s, %s: %s" % (walk_score, walk_description, bike_score, bike_description))


#---------------------------------------------------------------# 
#Get school data from OnBoard
# Function requires latitude and longitude; returns ?
def get_school_data(lat, lng):
    import http.client 

    #Onboard API Key
    onboard_api_key = "727ca1bf9168cb8329806cb7e0eef3f6"

    conn = http.client.HTTPSConnection("search.onboard-apis.com") 
    school_url = "/propertyapi/v1.0.0/school/snapshot?"
    headers = { 
        'accept': "application/json", 
        'apikey': "727ca1bf9168cb8329806cb7e0eef3f6", 
        } 

    point = "latitude=" + str(lat) + "&longitude=" + str(lng) + "&radius=5"
    query_url = school_url + point

    conn.request("GET", query_url, headers=headers) 

    res = conn.getresponse()
    resp = json.loads(res.read())
    resp
    
    #loop through and count up private and public schools
    total = resp['status']['pagesize']
    print(total)
    for i in range(0, total):    
        print("Type: %s, Name: %s" % (resp['school'][i]['School']['Filetypetext'], resp['school'][i]['School']['InstitutionName']))
        #print(resp['school'][i]['School']['InstitutionName'])


#---------------------------------------------------------------#
#Query Community API and return the results as JSON object 'resp'

#API URL: https://developer.onboard-apis.com/docs
#---------------------------------------------------------------#


def get_community_data(target_zip):

   #Onboard API Key
    onboard_api_key = "727ca1bf9168cb8329806cb7e0eef3f6"

    conn = http.client.HTTPSConnection("search.onboard-apis.com")
    headers = {
        'accept': "application/json",
        'apikey': "727ca1bf9168cb8329806cb7e0eef3f6",
        } 

    community_url = "/communityapi/v2.0.0/Area/Full/?"
    queries="AreaId=ZI"+target_zip
    query_url = community_url + queries
    conn.request("GET", query_url, headers=headers) 
    res = conn.getresponse()
    resp = json.loads(res.read())
    return resp


#---------------------------------------------------------------#
# Extract age demographics from the 'resp' JSON object
# Provides a pie chart
#---------------------------------------------------------------#
def age_demographics_zip(resp,target_zip):
    resp_keys = list(resp['response'].keys())
    if 'result' not in resp_keys: #check if there is data in 'resp' 
        result = 2       
        print('No results to graph. This zip code may not be valid.')

    else: # If there are results in the 'resp' 
        age_columns = ['age00_04','age05_09','age10_14','age15_19','age20_24','age25_29','age30_34','age35_39','age40_44',
                    'age45_49','age50_54','age55_59','age60_64','age65_69','age70_74','age75_79','age80_84','agegt85']
        labels = []
        age_groups = []
        age_group_values = []
        county_name = resp['response']['result']['package']['item'][0]['countyname']
        for x in age_columns:
            group_name = x
            age_groups.append(x)
            route = resp['response']['result']['package']['item'][0][x]
            age_group_values.append(int(route))
            label = x.replace('age','').replace('_','-').replace('gt85',' >=85') #format labels
            labels.append(label)

        # Create DF with summarized age groups
        age_by_zip = {"Groups": age_groups, "Count": age_group_values}
        age_by_zip_df = pd.DataFrame(age_by_zip)
        _0_09 = age_by_zip_df[0:2]['Count'].sum()
        _10_19 = age_by_zip_df[2:4]['Count'].sum()
        _20_29 = age_by_zip_df[4:6]['Count'].sum()
        _30_39 = age_by_zip_df[6:8]['Count'].sum()
        _40_49 = age_by_zip_df[8:10]['Count'].sum()
        _50_59 = age_by_zip_df[10:12]['Count'].sum()
        _60_69 = age_by_zip_df[12:14]['Count'].sum()
        _70_plus = age_by_zip_df[14:18]['Count'].sum()
        grp_sum_lables = ['1-9','10-19','20-29','30-39','40-49','50-59','60-69','>= 70']
        grp_sums = [_0_09,_10_19,_20_29,_30_39,_40_49,_50_59,_60_69,_70_plus]
        grp_dict = {'Groups':grp_sum_lables,'Count':grp_sums}
        grouped_age_df = pd.DataFrame(grp_dict)
        # Determine max value amongst age groups and set this to explode in pie chart
        max_age = grouped_age_df['Count'].idxmax(axis=0, skipna=True)
        explode_params = [0,0,0,0,0,0,0,0,]
        explode_params[max_age] = 0.2
        # Plot pie chart 
        fig = plt.figure(figsize = [10,10])
        plt.pie(grouped_age_df['Count'], shadow=True, startangle=140,explode = explode_params,labels = grouped_age_df['Groups'],autopct="%1.1f%%", pctdistance = .65)
        plt.title("Age Groups for zip code %s\nin %s" %(target_zip,county_name))
    #     plt.savefig("Age_Demographics_PieChar.png")
        return plt.show()
    