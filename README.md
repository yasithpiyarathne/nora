# nora
offline wrapper for javascript yarn

usage: nora [-h] {pack,append,lock,add,create} ...

nora offline package manager

positional arguments:
  {pack,append,lock,add,create}
    pack                pack node packages into offline archives
    append              add package reference to package.json
    lock                create/update lock file
    add                 append => lock => yarn add
    create              same as create-*

options:
  -h, --help            show this help message and exit
