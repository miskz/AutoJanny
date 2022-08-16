import os
import json
import asyncio
import asyncpraw
import psaw
import googleapiclient.discovery
import discord_webhook

def plugin_config_init(workpath):
    config = os.path.join(workpath, 'config', 'dummy_plugin.json')
    with open(config, "r") as jsonfile:
        plugin_config = json.load(jsonfile)
    return plugin_config['priority']   

class AutoJannyPlugin:
    
    name = 'Dummy Plugin'
    description = 'Dummy plugin to use as a template and for development.'
    
    # valid types are: submission, comment, report
    plugin_type = 'comment'
    priority = 0

    # **_ discards unexpected arguments so that we don't have to store them for separate threads    
    def __init__(self, workpath, reddit, **_):
        data = []
        self.priority = plugin_config_init(workpath)
        self.reddit = reddit
    
    # possible input kwargs are reddit, pushift, youtube, discord, subreddit, submission, comment, workpath

    async def run_rules(self, comment):
        stop = True
        print(self.name + ': processed')
        return stop