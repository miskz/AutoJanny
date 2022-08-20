import os
import json

def plugin_config_init(workpath):
    config = os.path.join(workpath, 'plugin', 'config', 'dummy_plugin.json')
    with open(config, "r") as jsonfile:
        settings = json.load(jsonfile)
    return settings['priority']   

class AutoJannyPlugin:
    
    name = 'Dummy Plugin'
    description = 'Dummy plugin to use as a template and for development.'
    
    # valid types are: submission, comment, report
    plugin_type = 'comment'
    priority = 0

    # possible input kwargs are reddit, pushift, youtube, discord, subreddit, submission, comment, workpath. datanbase
    # **_ discards unexpected arguments so that we don't have to store them for separate threads    
    def __init__(self, workpath, **_):
        data = []
        self.priority = plugin_config_init(workpath)

    async def run_rules(self, comment, **_):
        stop = False
        print(self.name + ': processed')
        return stop
