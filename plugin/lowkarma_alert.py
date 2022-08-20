import os
import json
from discord_webhook import DiscordEmbed as dc_embed

def plugin_config_init(workpath):
    config = os.path.join(workpath, 'plugin', 'config', 'lowkarma_alert.json')
    with open(config, "r") as jsonfile:
        settings = json.load(jsonfile)
    return settings

class AutoJannyPlugin:
    
    name = 'Low karma alert'
    description = 'Monitors comments from users that are accumulating negative karma quickly, raises them via Discord webhook'
    
    plugin_type = 'comment'
    priority = 0
 
    def __init__(self, workpath, reddit, discord, **_):
        data = []
        self.settings = plugin_config_init(workpath)
        self.priority = self.settings['priority']
        self.reddit = reddit
        self.discord = discord
    
    async def run_rules(self, comment, **_):
        stop = False
        print('Running comment rule: ' + self.name)
        try:

            await self.reddit.comment(comment.id)
            score_monitored_sub = 0
            score_other = 0

            async for subcomment in comment.author.comments.new(limit=self.settings['comment_lookback']):
                if subcomment.subreddit == comment.subreddit:
                    score_monitored_sub += comment.score
                else:
                    score_other += subcomment.score

            if score_monitored_sub < self.settings['karma_threshold']:
                discord_description = str(f"{self.reddit.comment(subcomment).body}\n\nhttps://reddit.com{reddit.comment(subcomment).permalink}")
                discord_title = str(f"{self.reddit.comment(subcomment).author}\n @ {self.reddit.comment(subcomment).submission.title}")
                discord_embed = dc_embed(title=discord_title,description=discord_description)
                discord_embed.add_embed_field(name='/r/' + comment.subreddit, value=score_monitored_sub)
                discord_embed.add_embed_field(name='Other', value=score_other)
                discord_embed.set_timestamp()
                self.discord.add_embed(discord_embed)
                response = self.discord.execute()
                print('Alerted Discord: ' + response)

        except Exception as zonk:
            print(f"Error in user comment crawl check: {zonk}")
            
        print(self.name + ': processed')
            
        return stop