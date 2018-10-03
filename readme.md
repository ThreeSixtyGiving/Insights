

## Run development version

```sh
python index.py
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
```