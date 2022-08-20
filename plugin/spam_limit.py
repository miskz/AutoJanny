import os
import json
from thefuzz import fuzz

def plugin_config_init(workpath):
    config = os.path.join(workpath, 'plugin', 'config', 'spam_limit.json')
    with open(config, "r") as jsonfile:
        settings = json.load(jsonfile)
    return settings

class AutoJannyPlugin:
    
    name = 'Spam limit'
    description = 'Enforces submissions per timeframe rules'
    
    plugin_type = 'submission'
    priority = 5
 
    def __init__(self, workpath, reddit, youtube, **_):
        data = []
        self.settings = plugin_config_init(workpath)
        self.priority = self.settings['priority']
        self.reddit = reddit
        self.youtube = youtube
        
    async def action_content(self, submission, report_message=None):
        if self.mode == 'report':
            await submission.report(self.settings['report_newvid'])
        elif self.mode == 'remove':
            await submission.mod.remove()
            await submission.mod.send_removal_message(self.removal_message, type='public')
        else:
            print('No valid content action mode provided.')
        
    async def check_yt_selfpromo(self, submission):
        try:
            youtube_id = self.youtube.get_yt_id(submission.url)
            if youtube_id is not None:
                for match in youtube_id.groups():
                    if match is not None:
                        youtube_id = match
                        video = self.youtube.get_yt_details(self.youtube, youtube_id)
                        print(self.setttings['views'])
                        if (
                            video['views'] < self.settings['views']
                            and video['age'] < self.settings['age']
                        ):
                            self.action_content(submission=submission, report_message=self.settings['report_newvid'])
                            return True
                        else:
                            return False
        except Exception as zonk:
            print(f"Error while doing Youtube promo check: {zonk}")

    async def check_url_selfpromo(self, submission):
        try:
            match = fuzz.token_sort_ratio(submission.author.name.lower(), submission.url.lower())
            if (
                len(submission.author.name) >= 8
                and match > 80
            ):
                self.action_content(submission=submission, report_message=self.settings['report_unameurl'])
                return True
            else:
                return False
        except Exception as zonk:
            print(f"Error while doing URL promo check: {zonk}")

    async def check_yt_continuous_promo(self, submission):
        try:
            youtube_id = self.youtube.get_yt_id(submission.url)
            if youtube_id is not None:
                counter = 0
                channel = ""
                video = self.youtube.get_yt_details(youtube_id)
                channel = video['channel']
                async for post in self.reddit.submission(submission.id).author.submissions.new(limit=10):
                    await post
                    youtube_id = await self.youtube.get_yt_id(post.url)
                    if youtube_id is not None:
                        video = self.youtube.get_yt_details(self.youtube, youtube_id)
                        if channel == video['channel']:
                            counter += 1
                    if counter >= self.settings['repeatvid']:
                        self.action_content(submission=submission, report_message=self.settings['report_repeatvid'])
                        return True
            else:
                return False
        except Exception as zonk:
            print(f'Error while doing continuous spam promo check: {zonk}')

    async def check_continuous_promo(self, submission):
        try:
            # apparently submission can't be used as generator unless initialized again?
            await self.reddit.submission(submission.id)
            counter = 0
            title = ""
            async for post in submission.author.submissions.new(limit=10):
                title = post.title
                if post.title == title:
                    counter =+ 1
            if counter >= self.settings['repeattitle']:
                self.action_content(submission=submission, report_message=self.settings['report_newtitle'])
                return True
            else:
                return False
        except Exception as zonk:
            print(f'Error while doing continuous spam promo check: {zonk}')
        
    async def run_rules(self, submission, **_):
        stop = False
        print('Running submission rule: ' + self.name)
        if await self.check_yt_selfpromo(submission): stop = True
        if ~stop and await self.check_url_selfpromo(submission): stop = True
        if ~stop and await self.check_yt_continuous_promo(submission): stop = True
        if ~stop and await self.check_continuous_promo(submission): stop = True
        print(self.name + ': processed')
        return stop