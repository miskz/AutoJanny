import asyncpraw
import psaw
import googleapiclient.discovery
import discord_webhook

class AutoJannyPlugin:
    
    name = 'Dummy Plugin'
    description = 'Dummy plugin to use as a template and for development.'
    priority = 0
    
    # valid types are: submission, comment, report
    plugin_type = 'submission'
    
    def __init__(self):
        data = []
    def run_rules(*args):
        for arg in args:
            print(arg)
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
        print('plugin loaded with arguments')