## Install Dash
This repo uses Dash. See [Dash installation documentation](https://dash.plot.ly/installation)


## Run development version

Run in two different command lines.

```sh
python index.py
python worker.py
```

## Configuration variables

The following configuration variables need to be set to get parts of the site
working. You can do this in a development version by including a `.env` file
in the root directory. 

In dokku you can set these variables using the `dokku config:set explorer CONFIG_VAR=value`
command.

```
# configuration for the newsletter signup box
NEWSLETTER_FORM_ACTION=https://threesixtygiving.us10.list-manage.com/subscribe
NEWSLETTER_FORM_U=216b8b926250184f90c7198e8
NEWSLETTER_FORM_ID=91870dde44

# file from which the 360Giving registry will be loaded
THREESIXTY_STATUS_JSON=https://storage.googleapis.com/datagetter-360giving-output/branch/master/status.json

# configuration for the mapbox map - an access token is needed for the map to work
MAPBOX_ACCESS_TOKEN=token_goes_here
MAPBOX_STYLE=mapbox://styles/davidkane/cjmtr1n101qlz2ruqszjcmhls
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