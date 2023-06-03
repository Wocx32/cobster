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
exception_notif_webhook = '{webhook to send exception tracebacks to}' # not necessary 
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
# docker
```bash
docker run --name cobster --restart unless-stopped -v cobster-db:/usr/src/app/db -d cobster
```
# TODO

- `shift to docker compose with volume`