from .context import executable, yarn
from .action_cls import _
import argparse
import os

parser = argparse.ArgumentParser(
    description="nora offline package manager", prog="nora")
subparsers = parser.add_subparsers(dest="action", required=True)
sp_pack = subparsers.add_parser(
    "pack", help="pack node packages into offline archives")
sp_pack.add_argument('packages', help='package name',
                     nargs='*')
sp_append = subparsers.add_parser(
    'append', help="add package reference to package.json")
sp_append.add_argument(
    '-d', '--dev', help="add as a development dependancy", action="store_true")
sp_append.add_argument('packages', help='package name', nargs='+')

sp_lock = subparsers.add_parser('lock', help='create/update lock file')

sp_add = subparsers.add_parser('add', help='append => lock => yarn add')
sp_add.add_argument('packages', help='package name', nargs='*')
sp_add.add_argument(
    '-d', '--dev', help="add as a development dependancy", action="store_true")
sp_create = subparsers.add_parser('create', help='same as create-*')
sp_create.add_argument('programme', help='programme name')
sp_create.add_argument(
    'options', help='options to be passed', nargs=argparse.REMAINDER)


def process(args=None):
    args = parser.parse_args(args)
    match args.action:
        case 'pack':
            _.pack_packages(args.packages)
        case 'append':
            _.append_packages(args.packages, args.dev)
        case 'lock':
            _.lock()
        case 'add':
            if args.packages:
                _.add(args.packages, args.dev)
            else:
                with yarn():
                    os.system('yarn -s --offline')

        case 'create':
            name = f'create-{args.programme}'
            with executable(name):
                os.system(f'{name} {" ".join(args.options)}')
