import os
import json
import time

def plugin_config_init(workpath):
    config = os.path.join(workpath, 'config', 'submission_limit.json')
    with open(config, "r") as jsonfile:
        plugin_config = json.load(jsonfile)
    return plugin_config['priority'], plugin_config['submissions_no'], plugin_config['timeframe_seconds'], \
        plugin_config['mode'], plugin_config['removal_message']

class AutoJannyPlugin:
    
    name = 'Submission limit'
    description = 'Enforces submissions per timeframe rules'
    
    plugin_type = 'submission'
    priority = 0
 
    def __init__(self, workpath, reddit, database, **_):
        data = []
        self.priority, self.submission_no, self.timeframe_seconds, self.mode, self.removal_message = plugin_config_init(workpath)
        self.reddit = reddit
        self.database = database
    
    async def run_rules(self, submission, **_):
        result = 0
        stop = False
        print('running rule ' + self.name)
        if self.mode != 'reddit':
            result = len(self.database.search_submissions(submission.author.name, self.timeframe_seconds))
        elif self.mode != 'db' and result <= 5:
            for post in submission.author.submissions.new():
                if post.created_utc > time.time() - self.timeframe_seconds:
                    result+= 1
                else:
                    break
                
        if result > 5:
            stop = True
            submission.mod.remove()
            submission.mod.send_removal_message(self.removal_message, type='public')
            
        print(self.name + ': processed')
            
        return stop