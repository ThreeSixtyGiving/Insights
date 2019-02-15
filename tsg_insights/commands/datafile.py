import logging
import sys

import click
from flask import Flask, url_for
from flask.cli import AppGroup
from tqdm import tqdm
import requests
import pandas as pd

from ..data.registry import process_registry
from ..data.process import get_dataframe_from_url
from ..data.cache import delete_from_cache, get_from_cache, get_cache

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
def cli_fetch_file(url):
    fileid, filename, headers = get_dataframe_from_url(url)
    click.echo("File loaded")
    click.echo('/file/{}'.format(fileid))


@cli.command('fetchall')
@click.argument('output', type=click.Path())
def cli_fetch_all_files(output):
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
            if file_['file_size'] < 50000000:
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
def cli_remove_file(fileid):
    delete_from_cache(fileid)


@cli.command('preview')
@click.argument('fileid')
def cli_preview_file(fileid):
    df = get_from_cache(fileid)

    cli_header("Columns")
    click.echo(df.columns.tolist())

    cli_header("Preview")
    click.echo(df)
