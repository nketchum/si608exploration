import requests
import pandas as pd

api_key = "tBAlcLuvA82i6bNebj5J179qUaNzOkA3g5loPecg"
url = "https://api.congress.gov/v3/"

def get_bill_cosponsors(bill_type, bill_number, congress):
    endpoint = f"bill/{congress}/{bill_type}/{bill_number}/cosponsors"
    params = {
        "api_key": api_key
    }
    response = requests.get(url + endpoint, params=params)
    #return response.json()['cosponsors']
    try:
        cosponsors = response.json()['cosponsors']
        df_cosponsors = pd.DataFrame(cosponsors, columns=['firstName', 'lastName', 'party'])
        df_cosponsors['type'] = 'cosponsor'
        df_cosponsors['bill'] = bill_type + bill_number
        return df_cosponsors
    except:
        return pd.DataFrame()


def get_bill_sponsors(bill_type, bill_number, congress):
    endpoint = f"bill/{congress}/{bill_type}/{bill_number}"
    params = {
        "api_key": api_key
    }
    try:
        response = requests.get(url + endpoint, params=params)
        sponsors = response.json()['bill']['sponsors']
        df_sponsors = pd.DataFrame(sponsors, columns=['firstName', 'lastName', 'party'])
        df_sponsors['type'] = 'sponsor'
        df_sponsors['bill'] = bill_type + bill_number
        return df_sponsors
    except:
        return pd.DataFrame()


def get_bill_info(bill_type, bill_number, congress):
    df_cosponsors = get_bill_cosponsors(bill_type, bill_number, congress)
    df_sponsors = get_bill_sponsors(bill_type, bill_number, congress)
    df = pd.concat([df_cosponsors, df_sponsors])
    return df