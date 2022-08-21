import os
import json
import pmaw
from time import time

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
        reference_time = time()
        
        results = []
        subreddit = await self.reddit.subreddit(comment.subreddit.display_name)
        async for submission in subreddit.search(('author:' + comment.author.name).format('user'), time_filter='month'):
            results.append(submission.id)
            
        if results != []:
            activity_found = True
        
        submission = await comment.submission.load()
        if comment.submission.link_flair_template_id == self.settings['antibrigade-flair'] and not activity_found:
            comments = await self.pushift.search_comments(author=comment.author.name, subreddit=comment.subreddit.display_name)
            max_response_cache = 1
            cache = []
            for subcomment in comments:
                if (
                    subcomment.submission.id != comment.submission.id
                    or reference_time - subcomment.created_utc > 86400
                ):
                    cache.append(subcomment)
                if len(cache) >= max_response_cache:
                    timediff = reference_time - subcomment.created_utc
                    break

            if len(cache) < 1:
                stop_reason = self.settings['no-activity-text']
                activity_found = False
            elif timediff > self.settings['time_threshold']:
                stop_reason = self.settings['no-recent-activity-text'] + str(int(timediff // 86400)) + self.settings['time-unit']
                activity_found = False
            else:
                activity_found = True

        if not activity_found:
            reply = comment.reply(self.settings['reply-header'] + stop_reason + self.settings['reply-footer'])
            reply.mod.distinguish()   
        
        print(self.name + ': processed')
        return stop