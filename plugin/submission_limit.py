import os
import json
import time

def plugin_config_init(workpath):
    config = os.path.join(workpath, 'plugin', 'config', 'submission_limit.json')
    with open(config, "r") as jsonfile:
        settings = json.load(jsonfile)
    return settings

class AutoJannyPlugin:
    
    name = 'Submission limit'
    description = 'Enforces submissions per timeframe rules'
    
    plugin_type = 'submission'
    priority = 0
 
    def __init__(self, workpath, reddit, database, **_):
        data = []
        self.settings = plugin_config_init(workpath)
        self.priority = self.settings['priority']
        self.reddit = reddit
        self.database = database
    
    async def run_rules(self, submission, **_):
        result = 0
        stop = False
        print('Running submission rule: ' + self.name)
        if self.settings['mode'] != 'reddit':
            result = len(self.database.search_submissions(submission.author.name, self.settings['timeframe_seconds']))
        elif self.settings['mode'] != 'db' and result <= 5:
            for post in submission.author.submissions.new():
                if post.created_utc > time.time() - self.settings['timeframe_seconds']:
                    result+= 1
                else:
                    break
                
        if result > 5:
            stop = True
            submission.mod.remove()
            submission.mod.send_removal_message(self.settings['removal_message'], type='public')
            
        print(self.name + ': processed')
            
        return stop