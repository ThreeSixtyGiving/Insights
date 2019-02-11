## Install Dash
This repo uses Dash. See [Dash installation documentation](https://dash.plot.ly/installation)


## Run development version

Run in two different command lines.

```sh
python index.py
python worker.py
```

## Get mapbox to work

For the maps to show you need to have a mapbox personal access token set to the
`MAPBOX_ACCESS_TOKEN` environmental variable. On dokku this would be something
like:

```bash
dokku config:set explorer MAPBOX_ACCESS_TOKEN="insert_access_token_here"
```


## Setup on dokku

```bash
# create app
dokku apps:create explorer

# add redis cache
sudo dokku plugin:install https://github.com/dokku/dokku-redis.git redis
dokku redis:create explorercache
dokku redis:link explorercache explorer

# enable domains
dokku domains:enable explorer
dokku domains:add explorer example.com

# letsencrypt
dokku config:set --no-restart explorer DOKKU_LETSENCRYPT_EMAIL=your@email.tld
dokku letsencrypt explorer

# create app storage
mkdir -p /var/lib/dokku/data/storage/explorer-uploads
chown -R dokku:dokku /var/lib/dokku/data/storage/explorer-uploads
chown -R 32767:32767 /var/lib/dokku/data/storage/explorer-uploads
dokku storage:mount explorer /var/lib/dokku/data/storage/explorer-uploads:/app/uploads
```

## Get newsletter section to appear

Add the following environmental variables

```
NEWSLETTER_FORM_ACTION=https://threesixtygiving.us10.list-manage.com/subscribe
NEWSLETTER_FORM_U=216b8b926250184f90c7198e8
NEWSLETTER_FORM_ID=91870dde44
```