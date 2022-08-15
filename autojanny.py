import os
import sys
import operator
import importlib
import json
import praw
import psaw
import googleapiclient.discovery
import googleapiclient.errors
from google.oauth2 import service_account
from discord_webhook import DiscordWebhook as dc_webhook

def workpath_init():
    try:
        workpath = sys.argv[1]
    except:
        print('Warning: No working directory specified, using current one.')
        workpath = os.getcwd()
    return workpath

def plugin_init():
    submission_plugins = []
    comment_plugins = []
    report_plugins = []
    plugin_dir = os.path.join(workpath, 'plugin')
    plugin_files = next(os.walk(plugin_dir))[2]
    for plugin_file in plugin_files:
        plugin_path = 'plugin.' + plugin_file[:-3]
        if "__" not in plugin_path:
            try:
                plugin = getattr(importlib.import_module(plugin_path), 'AutoJannyPlugin')
                match plugin.plugin_type:
                    case 'submission':
                        submission_plugins.append(plugin)
                    case 'comment':
                        comment_plugins.append(plugin)
                    case 'report':
                        report_plugins.append(plugin)
            except:
                print(plugin_path + 'does not appear to be a valid plugin')
    submission_plugins.sort(key = operator.attrgetter('priority'))
    comment_plugins.sort(key = operator.attrgetter('priority'))
    report_plugins.sort(key = operator.attrgetter('priority'))
    return submission_plugins, comment_plugins, report_plugins
                
def reddit_init():
    config = os.path.join(workpath, 'config', 'reddit.json')
    with open(config, "r") as jsonfile:
        reddit_config = json.load(jsonfile)
    reddit = praw.Reddit(client_id=reddit_config['client_id'],
                         client_secret=reddit_config['client_secret'],
                         user_agent=reddit_config['user_agent'],
                         password=reddit_config['password'],
                         username=reddit_config['username'])
    pushift = psaw.PushshiftAPI(reddit)
    subreddit = reddit_config['subreddit']
    return reddit, pushift, subreddit

def youtube_init():
    config = os.path.join(workpath, 'config', 'service_key.json')
    credentials = service_account.Credentials.from_service_account_file(config)
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)
    return youtube

def discord_init():
    config = os.path.join(workpath, 'config', 'discord.json')
    with open(config, "r") as jsonfile:
        discord_config = json.load(jsonfile)    
    discord = dc_webhook(url=discord_config['webhook_url'],
                         username=discord_config['webhook_user'])
    return discord

workpath = workpath_init()
youtube = youtube_init()
discord = discord_init()
reddit, pushift, monitored_sub = reddit_init()
submission_plugins, comment_plugins, report_plugins = plugin_init()

for plugin in submission_plugins:
    plugin.run_rules(reddit, youtube)
    