import logging
import sys

import click
import pandas as pd
from flask import Flask, current_app
from flask.cli import AppGroup, with_appcontext

from ..data.cache import delete_from_cache, get_cache, get_from_cache, save_to_cache
from ..data.process import get_dataframe_from_url
from ..data.registry import get_reg_file, process_registry

cli = AppGroup("additional_data")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[logging.StreamHandler()],
)


@cli.command("removeall")
@with_appcontext
def cli_remove_all_files():
    cache = get_cache()
    for k in ["charity", "company", "postcode"]:
        keys_to_delete = cache.hlen(k)
        if click.confirm(
            f"This will delete all {keys_to_delete:,.0f} cached {k}. Are you sure you want to continue?"
        ):
            cache.delete(k)
            click.echo(f"Deleted {keys_to_delete:,.0f} keys from {k}")
