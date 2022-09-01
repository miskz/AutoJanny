import os
import json
from time import time
from datetime import datetime

def plugin_config_init(workpath):
    config = os.path.join(workpath, 'plugin', 'config', 'brigade-troller.json')
    with open(config, "r") as jsonfile:
        settings = json.load(jsonfile)
    return settings  

class AutoJannyPlugin:
    
    name = 'Brigade troller'
    description = 'Trolls brigading accounts with kindness. Identifies new or sleeper accounts that brigade a thread with specific flair ID \
        and replies to them with welcome message. Filtering messages via Automod is advise to not disturb users commenting in good faith.'
    
    # valid types are: submission, comment, report
    plugin_type = 'comment'
    priority = 0

    # possible input kwargs are reddit, pushift, youtube, discord, subreddit, submission, comment, workpath. datanbase
    # **_ discards unexpected arguments so that we don't have to store them for separate threads    
    def __init__(self, reddit, pushift, workpath, **_):
        data = []
        self.reddit = reddit
        self.pushift = pushift
        self.settings = plugin_config_init(workpath)
        self.priority = self.settings['priority']
 
    async def run_rules(self, comment, **_):
        stop = False
        activity_found = False
        stop_reason = ''
        results = []
        
        await comment.submission.load()
        if hasattr(comment.submission, 'link_flair_template_id'):
            if comment.submission.link_flair_template_id == self.settings['antibrigade_flair']:
                print('antibrigade flair detected')
                
                subreddit = await self.reddit.subreddit(comment.subreddit.display_name)
                async for submission in subreddit.search(('author:' + comment.author.name).format('user'), time_filter='year'):
                    print('checking posts')
                    results.append(submission.id)
                    
                if results == []:
                    activity_found = False
                    print('found posts')
                    
                if not activity_found:
                    reference_time = time()
                    threshold = time() - self.settings['time_threshold']
                    results = []
                    print('starting comment lookback')
                    author = await self.reddit.redditor(comment.author.name)
                    latest_subreddit_activity = 0
                    oldest_reddit_activity = time()
                    
                    async for subcomment in author.comments.new(limit=100):
                        if reference_time - subcomment.created_utc > 86400:
                            if latest_subreddit_activity < subcomment.created_utc and subcomment.subreddit.display_name == comment.subreddit.display_name:
                                latest_subreddit_activity = subcomment.created_utc
                            elif oldest_reddit_activity > subcomment.created_utc:
                                oldest_reddit_activity = subcomment.created_utc

                    if latest_subreddit_activity > self.settings['time_threshold']:
                        activity_found = True
                        
                    print('oldest reddit activity' + datetime.utcfromtimestamp(oldest_reddit_activity).strftime('%d/%m/%Y'))
                    print('latest subreddit activity' + datetime.utcfromtimestamp(latest_subreddit_activity).strftime('%d/%m/%Y'))
                    
                if latest_subreddit_activity == 0 and oldest_reddit_activity < reference_time - 10:
                    stop_reason = self.settings['no_activity_text']
                elif latest_subreddit_activity == 0:
                    stop_reason = self.settings['no_activity_text']
                elif latest_subreddit_activity < self.settings['time_threshold']:
                    cutoff_date = reference_time - self.settings['time_threshold']
                    stop_reason = self.settings['no_activity_within_threshold'] + datetime.utcfromtimestamp(cutoff_date).strftime('%d/%m/%Y')
                
                if not activity_found:
                    print('no activity found')
                    #reply = await comment.reply(self.settings['reply_header'] + stop_reason + self.settings['reply_footer'])
                    #await reply.mod.distinguish()   
               
        print(self.name + ': processed')
        return stop