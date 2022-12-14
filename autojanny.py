import os
import sys
import operator
import importlib
import asyncio
import json
import re
from datetime import datetime, timezone
import datefinder
import asyncpraw
import pmaw
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

def reddit_init():
    config = os.path.join(workpath, 'config', 'reddit.json')
    with open(config, "r") as jsonfile:
        reddit_config = json.load(jsonfile)
    reddit = asyncpraw.Reddit(client_id=reddit_config['client_id'],
                         client_secret=reddit_config['client_secret'],
                         user_agent=reddit_config['user_agent'],
                         password=reddit_config['password'],
                         username=reddit_config['username'])
    pushift = pmaw.PushshiftAPI(reddit)
    subreddit = reddit_config['subreddit']
    return reddit, pushift, subreddit

def youtube_init():
    config = os.path.join(workpath, 'config', 'service_key.json')
    credentials = service_account.Credentials.from_service_account_file(config)
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)
    return youtube

def get_yt_id(url):
    youtube_id = re.search('(?:v=|.be/|shorts/|embed/)(.{11})', url)
    if youtube_id is not None:
        for match in youtube_id.groups():
            if match is not None:
                youtube_id = match
    return youtube_id

def get_yt_details(youtube, youtube_id):
    try:
        request = youtube.videos().list(part="snippet,statistics", id=youtube_id)
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

def discord_init():
    config = os.path.join(workpath, 'config', 'discord.json')
    with open(config, "r") as jsonfile:
        discord_config = json.load(jsonfile)    
    discord = dc_webhook(url=discord_config['webhook_url'],
                         username=discord_config['webhook_user'])
    return discord

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
                plugin = plugin(workpath=workpath, reddit=reddit, youtube=youtube, discord=discord, database=database, pushift=pushift)
                match plugin.plugin_type:
                    case 'submission':
                        submission_plugins.append(plugin)
                    case 'comment':
                        comment_plugins.append(plugin)
                    case 'report':
                        report_plugins.append(plugin)
            except Exception as zonk:
                print('Error loading plugin: ' + zonk)
                print(plugin_path + ' does not appear to be a valid plugin')
    submission_plugins.sort(key = operator.attrgetter('priority'))
    comment_plugins.sort(key = operator.attrgetter('priority'))
    report_plugins.sort(key = operator.attrgetter('priority'))
    print('Reddit plugins loaded')
    print('??? Submissions: ', [plugin.name for plugin in submission_plugins])
    print('??? Comments: ', [plugin.name for plugin in comment_plugins])
    print('??? Reports: ', [plugin.name for plugin in report_plugins])
    return submission_plugins, comment_plugins, report_plugins

def database_init():
    database_plugins = []
    database_dir = os.path.join(workpath, 'database')
    plugin_files = next(os.walk(database_dir))[2]
    for plugin_file in plugin_files:
        plugin_path = 'database.' + plugin_file[:-3]
        if "__" not in plugin_path:
            try:
                plugin = getattr(importlib.import_module(plugin_path), 'AutoJannyDatabase')
                plugin = plugin(workpath)
                database_plugins.append(plugin)
            except:
                print(plugin_path + ' does not appear to be a valid database plugin')
    if len(database_plugins) == 1:
        print('Database plugin loaded: ' + database_plugins[0].name)
        return database_plugins[0]
    else:
        print('None or more than one DB plugins detected, make up your mind, dude.') 

async def submission_loop(monitored_sub):
    subreddit = await reddit.subreddit(monitored_sub)
    async for submission in subreddit.stream.submissions(skip_existing=True):
        print('New submission: ' + submission.permalink)
        database.add_submission(submission)
        for plugin in submission_plugins:
            stop = await plugin.run_rules(monitored_sub=monitored_sub, submission=submission)
            if stop: break
            
async def comment_loop(monitored_sub):
    subreddit = await reddit.subreddit(monitored_sub)
    async for comment in subreddit.stream.comments(skip_existing=True):
        print('New comment: ' + comment.permalink)
        database.add_comment(comment)
        for plugin in comment_plugins:
            stop = await plugin.run_rules(monitored_su=monitored_sub, comment=comment)
            if stop: break
            
async def report_loop(monitored_sub):
    subreddit = await reddit.subreddit(monitored_sub)
    async for report in subreddit.mod.stream.reports(skip_existing=True, only = "submissions"):
        print('New report: ' + report.permalink)
        for plugin in report_plugins:
            stop = await plugin.run_rules(monitored_sub=monitored_sub, report=report)
            if stop: break   
            
async def edited_loop(monitored_sub):
    subreddit = await reddit.subreddit(monitored_sub)
    async for edit in subreddit.mod.stream.edited(skip_existing=True):
        print('New edited content: ' + edit.permalink)
        try:
            database.update_comment(author=edit.author.name, created_utc=edit.created_utc, body=edit.body)
        except:
            database.update_submission(author=edit.author.name, created_utc=edit.created_utc, selftext=edit.selftext)

async def main():
    await asyncio.gather(submission_loop(monitored_sub), 
                         comment_loop(monitored_sub),
                         report_loop(monitored_sub),
                         edited_loop(monitored_sub))

if __name__ == "__main__":
    workpath = workpath_init()
    youtube = youtube_init()
    youtube.get_yt_id = get_yt_id
    youtube.get_yt_details = get_yt_details
    discord = discord_init()
    reddit, pushift, monitored_sub = reddit_init()
    database = database_init()
    database.table_init()
    submission_plugins, comment_plugins, report_plugins = plugin_init()
    # will throw deprecation warning but fix requires changes to asyncpraw itself
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    