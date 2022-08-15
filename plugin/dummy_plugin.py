import os
import json
from queue import PriorityQueue
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
    
    def __init__(self, workpath):
        data = []
        self.priority = plugin_config_init(workpath)
    def run_rules(*args):
        for arg in args:
            match arg:
                case asyncpraw.Reddit():
                    reddit = arg
                case psaw.PushshiftAPI():
                    pushift = arg
                case googleapiclient.discovery.Resource():
                    youtube = arg
                case discord_webhook.DiscordWebhook():
                    discord = arg
                case asyncpraw.models.reddit.subreddit.Subreddit():
                    subreddit = arg
                case asyncpraw.models.reddit.submission.Submission():
                    submission = arg
                case asyncpraw.models.reddit.comment.Comment():
                    comment = arg
                case str():
                    workpath = arg
                case _:
                    print('I don''t know this kind of argument, dude: ' + arg)