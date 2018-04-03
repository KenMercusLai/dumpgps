#!/usr/bin/env python
import click
try:
    from .dumpgps import list_files
except ImportError:
    from dumpgps import list_files


@click.command()
@click.argument('dir_name')
@click.argument('file_name')
@click.option('--recursive', is_flag=True)
def main(dir_name='.', file_name='output.csv', recursive=False):
    list_files(dir_name, file_name, recursive)


if __name__ == '__main__':
    main()
