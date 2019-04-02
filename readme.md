## Install Dash
This repo uses Dash. See [Dash installation documentation](https://dash.plot.ly/installation)


## Run development version

Run in two different command lines.

```sh
flask run
flask worker start
```

## Configuration variables

The following configuration variables need to be set to get parts of the site
working. You can do this in a development version by including a `.env` file
in the root directory. 

In dokku you can set these variables using the `dokku config:set explorer CONFIG_VAR=value`
command.

```
# flask app
FLASK_APP=index:server
FLASK_ENV=development # if you're developing

# configuration for the newsletter signup box
NEWSLETTER_FORM_ACTION=https://threesixtygiving.us10.list-manage.com/subscribe
NEWSLETTER_FORM_U=216b8b926250184f90c7198e8
NEWSLETTER_FORM_ID=91870dde44

# file from which the 360Giving registry will be loaded
THREESIXTY_STATUS_JSON=https://storage.googleapis.com/datagetter-360giving-output/branch/master/status.json

# configuration for the mapbox map - an access token is needed for the map to work
MAPBOX_ACCESS_TOKEN=token_goes_here
MAPBOX_STYLE=mapbox://styles/davidkane/cjmtr1n101qlz2ruqszjcmhls

# files larger than this limit are not allowed on the site
FILE_SIZE_LIMIT=50000000

# add google analytics tracking ID to use GA
GOOGLE_ANALYTICS_TRACKING_ID=UA-118275561-3
```

### Find your mapbox access token

You'll need to [sign up to mapbox](https://account.mapbox.com/auth/signup/) to create a token.
Once you've created an account you can find and create access tokens
through <https://account.mapbox.com/>.

### Find the newsletter configuration variables

The newsletter section is set up to send variables to a mailchimp signup form.
The different parts needed can be found in the URL that you go to when you visit
the "Join this mailing list" page:

`https://threesixtygiving.us10.list-manage.com/subscribe?u=216b8b926250184f90c7198e8&id=91870dde44`

From the URL above you find the following variables:

- NEWSLETTER_FORM_ACTION = `https://threesixtygiving.us10.list-manage.com/subscribe`
- NEWSLETTER_FORM_U = `216b8b926250184f90c7198e8`
- NEWSLETTER_FORM_ID = `91870dde44`

## Setup on dokku

```bash
# create app
dokku apps:create insights

# add redis cache
sudo dokku plugin:install https://github.com/dokku/dokku-redis.git redis
dokku redis:create insightscache
dokku redis:link insightscache insights

# enable domains
dokku domains:enable insights
dokku domains:add insights example.com

# letsencrypt
dokku config:set --no-restart insights DOKKU_LETSENCRYPT_EMAIL=your@email.tld
dokku letsencrypt insights

# create app storage
mkdir -p /var/lib/dokku/data/storage/insights-uploads
chown -R dokku:dokku /var/lib/dokku/data/storage/insights-uploads
chown -R 32767:32767 /var/lib/dokku/data/storage/insights-uploads
dokku storage:mount insights /var/lib/dokku/data/storage/insights-uploads:/app/uploads
```

## Allow bigger upload file size

By default dokku only allows 2mb file uploads. You can change this by
installing the [Dokku Nginx Max Upload Size](https://github.com/Zeilenwerk/dokku-nginx-max-upload-size) plugin.

```
sudo dokku plugin:install https://github.com/Zeilenwerk/dokku-nginx-max-upload-size.git
dokku config:set insights MAX_UPLOAD_SIZE=20M
```

## Caching

### Caches used

- `requests_cache` for caching URL requests
- `redis_queue` for managing worker process
- `get_from_cache` & `save_to_cache` use both redis and filesystem cache
  to store files & metadata about files

### When is the cache used

#### `tsg_insights\data\process.py`

- save to cache when dataset is loaded from file or URL
- requests_cache used for looking up postcodes, charities & companies

#### redis_queue

- used in worker process for managed the tasks

#### `tsg_insights\data\registry.py`

- used when fetching registry file (can be switched off)
- used when fetching files from registry

