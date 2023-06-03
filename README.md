# cobster
**Discord webhook poster**

Posts hot posts from specified subreddits using specified webhooks
# config
add in config.py
```python
client_id = '{your reddit client id}'
client_secret = '{your reddit client secret}'
user_agent = '{your app user agent}'

database = '{database path}' # parent folder must exist
```
# applets
add in applets.py
```python
applets = [
    {
        'webhook': '{webhook url}',
        'subreddit': '{subreddit}',
        'posts': '{number to post}' # optional
    },
    {
        ...
    },
    ...
]
```
# usage
```bash
python main.py
```

# TODO
shift to docker compose with volume