from multiprocessing.spawn import get_command_line
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
import pandas
from decimal import Decimal
import time

def plugin_config_init(workpath):
    config = os.path.join(workpath, 'config', 'dynamodb.json')
    with open(config, 'r') as jsonfile:
        backend_config_init = json.load(jsonfile)
        aws_access_key_id = backend_config_init['aws_access_key_id']
        aws_secret_access_key = backend_config_init['aws_secret_access_key']
        region = backend_config_init['region']
        comment_table_name = backend_config_init['comment_table']
        submission_table_name = backend_config_init['submission_table']
    return aws_access_key_id, aws_secret_access_key, region, comment_table_name, submission_table_name
 
class AutoJannyDatabase:
    
    name = 'DynamoDB'
    description = 'Database backend utilizing AWS DynamoDB NoSQL service'
    
    def __init__(self, workpath):
        data = []
        aws_access_key_id, aws_secret_access_key, region, self.comment_table_name, self.submission_table_name = plugin_config_init(workpath)
        self.client = boto3.client('dynamodb', region_name=region, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        self.dynamodb = boto3.resource('dynamodb', region_name=region, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        
    def table_init(self):
        
        try:
            self.comment_table = self.client.create_table(
                TableName=self.comment_table_name,
                KeySchema=[
                    {
                        'AttributeName': 'author',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'created_utc',
                        'KeyType': 'RANGE'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'author',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'created_utc',
                        'AttributeType': 'N'
                    }       
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            print('DynamoDB: Creating comment table')
            waiter = self.client.get_waiter('table_exists')
            waiter.wait(TableName=self.comment_table_name)
            print('DynamoDB: Table created and connected to')     
        except:
            self.comment_table = self.dynamodb.Table(self.comment_table_name)
            print('DynamoDB: Connected to existing comments table')
            
        try:
            self.submission_table = self.client.create_table(
                TableName=self.submission_table_name,
                KeySchema=[
                    {
                        'AttributeName': 'author',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'created_utc',
                        'KeyType': 'RANGE'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'author',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'created_utc',
                        'AttributeType': 'N'
                    }     
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 2,
                    'WriteCapacityUnits': 2
                }
            )
            print('DynamoDB: Creating submission table')
            waiter = self.client.get_waiter('table_exists')
            waiter.wait(TableName=self.submission_table_name)
            print('DynamoDB: Table created and connected to')     
        except:
            self.submission_table = self.dynamodb.Table(self.submission_table_name)
            print('DynamoDB: Connected to existing submissions table')
            
    def add_comment(self, comment):
        self.comment_table.put_item(
            Item={
                'id': comment.id,
                'author': comment.author.name,
                'created_utc': int(comment.created_utc),
                'link_id': comment.link_id,
                'parent_id': comment.parent_id,
                'body': [comment.body]
            }
        )
        
    def add_submission(self, submission):
        self.submission_table.put_item(
            Item={
                'id': submission.id,
                'author': submission.author.name,
                'created_utc': int(submission.created_utc),
                'title': submission.title,
                'url': submission.url,
                'selftext': [submission.selftext],
            }
        )
    
    def search_comments(self, author, timeframe=31556926):
        filtering_exp = Key('author').eq(author) & Key('created_utc').gte(int(time.time() - timeframe))
        comments = self.comment_table.query(KeyConditionExpression=filtering_exp)
        return comments
    
    def get_comment(self, author=None, created_utc=None, id=None, **_):
        if created_utc is not None:
            filtering_exp = Key('author').eq(author) & Key('created_utc').eq(created_utc)
            comment = self.comment_table.query(KeyConditionExpression=filtering_exp)
        elif created_utc is None and author is not None and id is not None:
            filtering_exp = Key('author').eq(author) & Attr('id').eq(id)
            comment = self.comment_table.scan(FilterExpression=filtering_exp)
        elif author is None and id is not None:
            filtering_exp = Attr('id').eq(id)
            comment = self.comment_table.scan(FilterExpression=filtering_exp)
        else:
            print('Need to provide at least author&created_utc / author&id / id')
        return comment['Items']
    
    def search_submissions(self, author, timeframe=31556926):
        filtering_exp = Key('author').eq(author) & Key('created_utc').gte(int(time.time() - timeframe))
        submissions = self.submission_table.query(KeyConditionExpression=filtering_exp)
        return submissions
    
    def get_submission(self, author=None, created_utc=None, id=None, **_):
        if created_utc is not None:
            filtering_exp = Key('author').eq(author) & Key('created_utc').eq(created_utc)
            submission = self.submission_table.query(KeyConditionExpression=filtering_exp)
        elif created_utc is None and author is not None and id is not None:
            filtering_exp = Key('author').eq(author) & Attr('id').eq(id)
            submission = self.submission_table.scan(FilterExpression=filtering_exp)
        elif author is None and id is not None:
            filtering_exp = Attr('id').eq(id)
            submission = self.submission_table.scan(FilterExpression=filtering_exp)
        else:
            print('Need to provide at least author&created_utc / author&id / id')
        return submission['Items']
    
    def update_comment(self, author, created_utc, body):
        comment = self.get_comment(author=author, created_utc=created_utc)
        if comment != []:
            comment_body = comment[0]['body']
            comment_body.append(body)
            self.comment_table.update_item(
                Key={
                    'author': author,
                    'created_utc': created_utc
                },
                UpdateExpression= 'set #body = :body',
                ExpressionAttributeNames={
                    '#body': 'body'
                },
                ExpressionAttributeValues={
                    ':body': comment_body
                },
                ReturnValues='UPDATED_NEW'
            )
        else:
            print('Tried to update comment that''s not in the DB, aborting.')
    
    def update_submission(self, author, created_utc, selftext):
        submission = self.get_comment(author=author, created_utc=created_utc)
        if submission != []:
            submission_selftext = submission[0]['selftext']
            submission_selftext.append(selftext)
            self.comment_table.update_item(
                Key={
                    'author': author,
                    'created_utc': created_utc
                },
                UpdateExpression= 'set #selftext = :selftext',
                ExpressionAttributeNames={
                    '#selftext': 'selftext'
                },
                ExpressionAttributeValues={
                    ':selftext': submission_selftext
                },
                ReturnValues='UPDATED_NEW'
            )
        else:
            print('Tried to update submission that''s not in the DB, aborting.')
