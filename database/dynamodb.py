import os
import boto3
from boto3.dynamodb.conditions import Attr
import json
import pandas
from decimal import Decimal
import time

def plugin_config_init(workpath):
    config = os.path.join(workpath, 'config', 'dynamodb.json')
    with open(config, "r") as jsonfile:
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
                        'AttributeName': 'id',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'author',
                        'KeyType': 'RANGE'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'author',
                        'AttributeType': 'S'
                    }       
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            print("DynamoDB: Creating comment table")
            waiter = self.client.get_waiter('table_exists')
            waiter.wait(TableName=self.comment_table_name)
            print("DynamoDB: Table created")     
        except:
            self.comment_table = self.dynamodb.Table(self.comment_table_name)
            print("DynamoDB: Connected to existing comments table")
            
        try:
            self.submission_table = self.client.create_table(
                TableName=self.submission_table_name,
                KeySchema=[
                    {
                        'AttributeName': 'id',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'author',
                        'KeyType': 'RANGE'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'author',
                        'AttributeType': 'S'
                    }     
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 2,
                    'WriteCapacityUnits': 2
                }
            )
            print("DynamoDB: Creating submission table")
            waiter = self.client.get_waiter('table_exists')
            waiter.wait(TableName=self.submission_table_name)
            print("DynamoDB: Table created")     
        except:
            self.submission_table = self.dynamodb.Table(self.submission_table_name)
            print("DynamoDB: Connected to existing submissions table")
            
    def add_comment(self, comment):
        self.comment_table.put_item(
            Item={
                'id': comment.id,
                'author': comment.author.name,
                'created_utc': Decimal(comment.created_utc),
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
                'created_utc': Decimal(submission.created_utc),
                'title': submission.title,
                'url': submission.url,
                'selftext': [submission.selftext],
            }
        )
        
    def get_comments(self, author, timeframe=31556926):
        comment_scan = self.comment_table.scan(FilterExpression=Attr('author').eq(author) & Attr('created_utc').gte(Decimal(time.time() - timeframe)))
        comments = pandas.DataFrame(comment_scan['Items'])
        return comments
        
    def get_submissions(self, author, timeframe=31556926):
        submission_scan = self.submission_table.scan(FilterExpression=Attr('author').eq(author) & Attr('created_utc').gte(Decimal(time.time() - timeframe)))
        submissions = pandas.DataFrame(submission_scan['Items'])
        return submissions

