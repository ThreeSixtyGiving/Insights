import logging
import sys

import click
from flask import Flask, url_for
from flask.cli import AppGroup
from tqdm import tqdm
import requests_cache

from ..data.registry import process_registry
from ..data.process import get_dataframe_from_url
from ..data.cache import delete_from_cache, get_from_cache, get_cache

requests_cache.install_cache(backend='redis', connection=get_cache())

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
    fileid, filename = get_dataframe_from_url(url)
    click.echo("File loaded")
    click.echo('/file/{}'.format(fileid))

@cli.command('fetchall')
def cli_fetch_all_files():
    reg = process_registry()
    for publisher, files in reg.items():
        cli_header(publisher)
        for file_ in files:
            click.echo(file_["title"])


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
