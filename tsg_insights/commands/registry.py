import click
from flask import Flask
from flask.cli import AppGroup, with_appcontext

from ..data.registry import get_registry, process_registry

cli = AppGroup('registry')

@cli.command('update')
@click.option('--skip-cache/--use-cache', default=True, help='whether to use a cached version if available')
@with_appcontext
def cli_update_register(skip_cache):
    reg = get_registry(skip_cache=skip_cache)
    processed = process_registry(reg)
    click.echo("Registry loaded{}. Contains {:,.0f} files from {:,.0f} publishers".format(
        "" if skip_cache else " (from cache)", len(reg), len(processed)
    ))
