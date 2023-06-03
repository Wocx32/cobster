
from time import sleep
import traceback
import praw
import prawcore
import requests
import sqlite3
import datetime

from lxml import etree

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import config
from applets import applets

import sys
import logging
import logging.config

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})


fmt = '[%(asctime)s] [%(levelname)s] %(message)s'
date_fmt = '%d/%m/%Y:%H:%M:%S %z'
formatter = logging.Formatter(fmt, date_fmt)

logging.basicConfig(
	format=fmt,
	datefmt=date_fmt,
	level=logging.INFO,
	handlers=[
		logging.StreamHandler(sys.stdout)
	]
)

logger = logging.getLogger(__name__)


db = sqlite3.connect(config.database)
db.execute(
    'CREATE TABLE IF NOT EXISTS Post (post_id TEXT NOT NULL, subreddit TEXT NOT NULL, timestamp timestamp NOT NULL)'
)
db.execute(
    'CREATE UNIQUE INDEX IF NOT EXISTS idx_post_id ON Post (post_id)'
)

cur = db.cursor()


reddit = praw.Reddit(
    client_id=config.client_id,
    client_secret=config.client_secret,
    user_agent=config.user_agent
)


session = requests.Session()
retries = Retry(total=7, backoff_factor=0.3)
adapter = HTTPAdapter(max_retries=retries)

session.mount('http://', adapter)
session.mount('https://', adapter)

def get_og_image(url):
    og_image = None
    if not url.startswith('http'):
        return og_image
    
    response = session.get(url)

    # Parse HTML using lxml
    parser = etree.HTMLParser()
    tree = etree.fromstring(response.content, parser)

    # Find the og:image meta tag
    og_image_element = tree.xpath('//meta[@property="og:image"]/@content')
    if og_image_element:
        og_image = og_image_element[0]

    return og_image

def get_hot_reddit_posts(subreddit='all', limit=20, ignored_flairs=[], max_posts=-1):
    subreddit = reddit.subreddit(subreddit)

    posts = {}

    hot_posts = subreddit.hot(limit=limit)
    post_counter = 0
    for post in hot_posts:

        

        if post.link_flair_text is not None and post.link_flair_text in ignored_flairs:
            continue

        cur.execute(
            'SELECT post_id, subreddit, timestamp FROM Post WHERE post_id=(?)', (post.id,)
        )

        if cur.fetchone() is not None:
            continue


        post_url = 'https://reddit.com/' + post.id

        img_url = ''
        link_to = ''
        if post.url.endswith(".jpg") or post.url.endswith(".png") or post.url.endswith('gif'):

            img_url = post.url
        
        else:
            link_to = post.url
            img = get_og_image(link_to)
            if img:
                img_url = img
            
        content = post.selftext
        if not content and link_to:
            content = link_to

        if post.author:
            author = post.author.name
        else:
            author = ''

        posts[post.id] = [post_url, img_url, content, post.title, author]
        post_counter += 1
        if post_counter == max_posts:
            return posts
                
    
    return posts


def execute_webhook(webhook_url, json_content):
    
    header = {
        'content-type': 'application/json'
    }

    req = True
    
    while req:
        req = False
        res = requests.post(webhook_url, headers=header, json=json_content)

        if res.content:
            res_content = res.json()

            if timeout := res_content.get('retry_after'):
                req = True
                logger.warn(f'Rate limited. Retry after: {timeout}')
                sleep(int(timeout))
                



for applet_id, applet in enumerate(applets):

    subreddit = applet.get('subreddit')
    webhook = applet.get('webhook')
    
    if not subreddit:
        logger.error(f'No subreddit provided {{applet: {applet_id}}}')
        continue

    if not webhook:
        logger.error(f'No webhook provided {{applet: {applet_id}}}')
        continue

    limit = applet.get('posts', 10)
    
    try:
        posts = get_hot_reddit_posts(subreddit, limit)
    except prawcore.exceptions.UnavailableForLegalReasons:
        logger.error(f'Subreddit not available for legal reasons {{applet: {applet_id}}}')
        continue
    except Exception as e:
        logger.exception(f'Exception occured in applet: {applet_id}', exc_info=1)

        try:
            tb = "".join(traceback.format_exception(e, value=e, tb=e.__traceback__)).strip()

            json_content = {
                'content': f'```python\nApplet id: {applet_id}\n{tb}```'
            }

            execute_webhook(config.exception_notif_webhook, json_content)
        except:
            pass

        continue

    for post, data in posts.items():

        post_url, img_url, content_, post_title, author = data

        cur.execute(
            'SELECT post_id, subreddit, timestamp FROM Post WHERE post_id=(?)', (post,)
        )

        logger.info(f'Start webhook execution {{applet: {applet_id}}}')

        embed = {
            'author': {
                'name': author
            },
            'title': post_title,
            'url': post_url,
            'description': content_,
            'image': {
                'url': img_url
            }
        }

        json_content = {
            'embeds': [embed]
        }
        
        execute_webhook(webhook, json_content)
        
        cur.execute(
            'INSERT INTO Post (post_id, subreddit, timestamp) VALUES (?, ?, ?)', (post, subreddit, datetime.datetime.now())
        )
        db.commit()
        logger.info(f'Webhook execution succeeded {{applet: {applet_id}}}')

db.close()

