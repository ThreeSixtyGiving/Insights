

## Run development version

```sh
python index.py
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
dokku config:set --no-restart es-postcodes DOKKU_LETSENCRYPT_EMAIL=your@email.tld
dokku letsencrypt explorer
```