import os
import json
import re
import datefinder
from datetime import datetime, timezone
from time import time
from thefuzz import fuzz

def plugin_config_init(workpath):
    config = os.path.join(workpath, 'plugin', 'config', 'submission_limit.json')
    with open(config, "r") as jsonfile:
        plugin_config = json.load(jsonfile)
    return plugin_config['priority'], plugin_config['submissions_no'], plugin_config['timeframe_seconds'], \
        plugin_config['mode'], plugin_config['removal_message']

class AutoJannyPlugin:
    
    name = 'Submission limit'
    description = 'Enforces submissions per timeframe rules'
    
    plugin_type = 'submission'
    priority = 0
 
    def __init__(self, workpath, reddit, pushift, youtube, **_):
        data = []
        self.priority, self.submission_no, self.timeframe_seconds, self.mode, self.removal_message = plugin_config_init(workpath)
        self.reddit = reddit
        self.pushift = pushift
        self.youtube = youtube

    def get_youtube_id(self, submission):
        youtube_id = re.search('(?:v=|.be/|shorts/|embed/)(.{11})', submission.url)
        for match in youtube_id.groups():
            if match is not None:
                youtube_id = match
        return youtube_id

    def get_yt_details(self, youtube_id):
        try:
            request = self.youtube.videos().list(part="snippet,statistics", id=youtube_id)
            details = request.execute()
            # returns lots of details with inconsistent variables by default, cleanup needed
            details = details["items"][0]
            datematches = datefinder.find_dates(details["snippet"]["publishedAt"])
            for datematch in datematches:
                publisheddate = datematch
            age = datetime.now(timezone.utc) - publisheddate
            details = {
                'title': details["snippet"]["title"],
                'channel': details["snippet"]["channelTitle"],
                'description': details["snippet"]["description"],
                'views': int(details["statistics"]["viewCount"]),
                'published': publisheddate,
                'age': age.days
            }
            return details
        except Exception as zonk:
            print(f"Error while getting Youtube video details: {zonk}")
    
    def run_rules(self, submission, **_):
        stop = False
        print('running rule ' + self.name)

            
        print(self.name + ': processed')
            
        return stop