import logging
import sys

import click
from flask import Flask, url_for, current_app
from flask.cli import AppGroup, with_appcontext
from tqdm import tqdm
import requests
import pandas as pd

from ..data.registry import process_registry, get_reg_file
from ..data.process import get_dataframe_from_url
from ..data.cache import delete_from_cache, get_from_cache, get_cache, get_filename, save_to_cache

cli = AppGroup('data')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.StreamHandler()
    ])


def cli_header(title:str):
    click.echo("")
    click.echo(title)
    click.echo("".join(["=" for x in title]))


@cli.command('fetch')
@click.argument('url')
@with_appcontext
def cli_fetch_file(url):
    if url.startswith("http"):
        fileid, filename, headers = get_dataframe_from_url(url)
    # otherwise assume it's a registry ID
    else:
        file_url, file_type = get_reg_file(url)
        fileid, filename, headers = get_dataframe_from_url(file_url)

    click.echo("File loaded")
    click.echo('/file/{}'.format(fileid))


@cli.command('fetchall')
@click.argument('output', type=click.Path())
@click.option('--file-limit', default=None, type=int, help='maximum file size to import')
@with_appcontext
def cli_fetch_all_files(output, file_limit):

    if not file_limit:
        file_limit = current_app.config.get("FILE_SIZE_LIMIT")
    if file_limit:
        click.echo("Skipping files larger than {:,.0f} bytes".format(file_limit))

    reg = process_registry()
    results = {}
    for publisher, files in list(reg.items()):
        cli_header(publisher)
        for file_ in files:
            click.echo("{} ({})".format(file_['title'], file_["file_size"]))
            click.echo(file_['download_url'])
            error = None
            fileid = None
            headers = None
            if file_['file_size'] < file_limit:
                try:
                    fileid, filename, headers = get_dataframe_from_url(file_["download_url"])
                except Exception as e:
                    error = str(e)
            else:
                error = "Skipped due to file size ({})".format(file_['file_size'])

            results[file_["identifier"]] = {
                "publisher": publisher,
                "fileid": fileid,
                "headers": headers,
                "error": error,
                **file_
            }
    
            result_df = pd.DataFrame(results).T
            result_df.index.rename("FileIdentifier", inplace=True)
            if output.endswith(".json"):
                result_df.to_json(output)
            elif output.endswith(".xlsx"):
                result_df.to_excel(output)
            else:
                result_df.to_csv(output)
            


@cli.command('remove')
@click.argument('fileid')
@with_appcontext
def cli_remove_file(fileid):
    delete_from_cache(fileid)


@cli.command('removeall')
@with_appcontext
def cli_remove_all_files():
    click.confirm('This will delete all cached data. Are you sure you want to continue?', abort=True)
    cache = get_cache()
    for k, c in cache.hscan_iter("files"):
        click.echo("Deleting file: {}".format(k))
        delete_from_cache(k)


@cli.command('redistofile')
@with_appcontext
def cli_redistofile():
    cache = get_cache()
    for k, c in cache.hscan_iter("files"):
        k = k.decode("utf8")
        df = get_from_cache(k, cache_type='redis')
        if df is not None:
            save_to_cache(k, df, cache_type='filesystem')


@cli.command('filetoredis')
@with_appcontext
def cli_redistofile():
    cache = get_cache()
    for k, c in cache.hscan_iter("files"):
        k = k.decode("utf8")
        df = get_from_cache(k, cache_type='filesystem')
        if df is not None:
            save_to_cache(k, df, cache_type='redis')


@cli.command('preview')
@click.argument('fileid')
@click.option('--field')
@with_appcontext
def cli_preview_file(fileid, field=None):
    df = get_from_cache(fileid)

    cli_header("Columns")
    click.echo(df.columns.tolist())

    cli_header("Preview")
    if field:
        click.echo(df[field].to_frame())
    else:
        click.echo(df)
