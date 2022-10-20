import json
import pandas as pd
import requests
import time
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

with open('data.json', "r") as f:
    data = json.loads(f.read())
  
def get_strava_tokens():
    response = requests.post(
                    url = 'https://www.strava.com/oauth/token',
                    data = {'client_id': data['client_id'],
                            'client_secret': data['client_secret'],
                            'code': data['access_code'],
                            'grant_type': 'authorization_code'
                            })
                            
    strava_tokens = response.json()
    
    with open('strava_tokens.json', 'w') as outfile:
        json.dump(strava_tokens, outfile)
    return strava_tokens


def get_activities():
    with open('strava_tokens.json') as json_file:
        strava_tokens = json.load(json_file)
        
    if strava_tokens['expires_at'] < time.time():
        strava_tokens = get_strava_tokens()
        
    page = 1
    url = "https://www.strava.com/api/v3/activities"
    access_token = strava_tokens['access_token']
    
    activities = pd.DataFrame(
        columns = ["id",
                    "name",
                    "start_date_local",
                    "type",
                    "distance",
                    "moving_time",
                    "elapsed_time",
                    "total_elevation_gain",
                    "average_speed",
                    "max_speed",
                    ])

    while True:
        r = requests.get(url + '?access_token=' + access_token + '&per_page=200' + '&page=' + str(page))
        r = r.json()
        
        if not r:
            break
        
        for x in range(len(r)):
            activities.loc[x + (page-1)*200,'id'] = r[x]['id']
            activities.loc[x + (page-1)*200,'name'] = r[x]['name']
            activities.loc[x + (page-1)*200,'start_date_local'] = r[x]['start_date_local'].split('T')[0]
            activities.loc[x + (page-1)*200,'type'] = r[x]['type']
            activities.loc[x + (page-1)*200,'distance'] = r[x]['distance']
            activities.loc[x + (page-1)*200,'moving_time'] = r[x]['moving_time']
            activities.loc[x + (page-1)*200,'elapsed_time'] = r[x]['elapsed_time']
            activities.loc[x + (page-1)*200,'average_speed'] = r[x]['average_speed']
            activities.loc[x + (page-1)*200,'max_speed'] = r[x]['max_speed']
            
        page += 1

    activities.to_csv('strava_activities.csv')
    activities = activities[(activities['type'] == 'Run') & (activities['distance'] > 4900)]
    activities = activities.reset_index()
    activities['moving_time'] = activities["moving_time"]/60
    activities['moving_time'] = activities['moving_time'].apply(lambda x:round(x,2))
    activities = activities.round(2)

    fig = plt.figure(figsize=(20, 10))
    fig.subplots_adjust(hspace=0.5)
    gs = GridSpec(nrows=1, ncols=1)
    fig.suptitle(f'Recent Runs', fontsize=16)

    ax0 = fig.add_subplot(gs[0, 0])
    bars = ax0.bar(activities["start_date_local"], activities["moving_time"])
    ax0.bar_label(bars)
    ax0.set_title('5k+ Runs')
    ax0.set_xlabel('Date')
    ax0.set_ylabel('Time in Minutes')
    
    plt.xticks(rotation=90)
    fig.savefig(f'all_runs.png')
    plt.show()

    # Make chart showoing best races by pace
    # Fix x label and date


get_activities()
