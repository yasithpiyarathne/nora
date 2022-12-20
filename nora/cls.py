from .context import yarn, internet, private_space
from pyarn import lockfile
from pathlib import Path
from typing import NamedTuple
import shutil
import json
import os
import re

tmp_loc = r'C:\TEMP'
# version_simplyfier = (r'(\^|>=|<=)(?P<version>\d*\.\d*\.\d*)', r'\g<version>')


class Yarn:
    def __init__(self):
        pass

    @property
    def is_yarn(self):
        return bool(shutil.which('yarn'))

    def add(self, package):
        with yarn():
            with internet():
                ret = os.system(f'yarn add -s {package}')
                if ret:
                    raise Exception(
                        f'installing "{package}" was not succesfull!')

    def offline(self):
        with yarn():
            os.system('yarn -s --offline')


class File:
    version_simplyfier = (
        r'(\^|>=|<=)(?P<version>\d*\.\d*\.\d*)', r'\g<version>')

    def __init__(self, file_name, parser, formater=None, fix_versions=False):
        if isinstance(file_name, Path):
            self.__file_name = file_name
        else:
            self.__file_name = Path(file_name)
        self.__parser = parser
        self.__formater = formater
        self.fix_versions = fix_versions
        self.filter = None
        self.on_blank_file = '{}'
        self.blank_not_ok = False

    def __repr__(self):
        return f'File({self.__file_name})'

    def __enter__(self):
        self.__cache = self.data
        return self.__cache

    def __exit__(self, type, value, traceback):
        if self.__formater:
            self._write(self.__cache)

    def _read(self):
        self.touch()
        with open(self.file_name) as file:
            data = file.read()

            if (not data) and self.blank_not_ok:

                data = self.on_blank_file
            if self.fix_versions:
                data = re.sub(*self.version_simplyfier, data)
            return data

    def _write(self, data):
        with open(self.__file_name, 'w') as file:
            file.write(self.__formater(data))

    def touch(self):
        self.__file_name.parent.mkdir(exist_ok=True)
        self.__file_name.touch(exist_ok=True)

    @property
    def file_name(self):
        return self.__file_name

    @property
    def data(self):
        data = self.__parser(self._read())
        if self.filter:
            data = self.filter(data)
        return data


class Package_JSON(File):
    def __init__(self):
        super().__init__('package.json', json.loads,
                         lambda data: json.dumps(data, indent=2))
        self.filter = self.__dev_slots
        self.on_blank_file = '{}'
        self.blank_not_ok = True

    @staticmethod
    def __dev_slots(data):
        fields = data.keys()
        if 'dependencies' not in fields:
            data['dependencies'] = {}
        if 'devDependencies' not in fields:
            data['devDependencies'] = {}
        return data

    def all_packages(self):
        with self as pkg_jsn:
            packages = {**pkg_jsn['dependencies'],
                        **pkg_jsn['devDependencies']}
        return packages


class Yarn_Lock(File):

    def __init__(self):

        super().__init__('yarn.lock', self.__lock2dic, self.__dic2lock)
        self.on_blank_file = '# yarn lockfile v1'
        self.blank_not_ok = True
        self.__lock = lockfile.Lockfile('1', {})

    def __lock2dic(self, data):
        return self.__lock.from_str(data).data

    def __dic2lock(self, data):
        self.__lock.data = data
        return self.__lock.to_str()


class nrpObj(NamedTuple):
    path: str
    title: str
    version: str

    @property
    def data(self):
        with open(self.path) as file:
            return json.load(file)

    @property
    def id(self):
        return f'{self.title}@{self.version}'

    @property
    def lock(self):
        return self.data['ref']


class NoraFS:
    __cached_pkg_ext = '.nrp'

    def __init__(self, nora_path=None):
        if not nora_path:
            nora_path = Path.home() / '.nora'
        else:
            nora_path = Path(nora_path)
        self.__nora_path = nora_path
        self.yarn_lock = Yarn_Lock()
        self.yarn_comm = Yarn()
        self.package_json = Package_JSON()

    @property
    def nora_path(self):
        return self.__nora_path

    @property
    def cached_path(self):
        return self.nora_path / 'cached'

    @property
    def pkg_json_path(self):
        return self.nora_path / 'pkg-json'

    @property
    def cached_packages(self):
        nrps = self.cached_path.rglob(f'*{self.__cached_pkg_ext}')

        def about_nrp(nrp_path: Path):
            name = nrp_path.relative_to(self.cached_path)
            title, version = re.match(
                r'(.*)-(\d*\.\d*\.\d*)' + '\\' + self.__cached_pkg_ext, name.as_posix()).groups()

            about = {
                "path": str(nrp_path),
                "title": title,
                "version": version,
            }
            return nrpObj(**about)
        return map(about_nrp, nrps)

    def get_cached_packages(self, packageTitle):
        res = list(
            filter(lambda pkg: pkg.title == packageTitle, self.cached_packages))
        if len(res):
            return sorted(res, key=lambda pkg: pkg.version, reverse=True)
        return None

    def get_latest_cached_package(self, packageTitle):
        pkgs = self.get_cached_packages(packageTitle)
        if pkgs:
            return pkgs[0]
        return None

    def get_cached_packege_of_specific_version(self, packageTitle, version):
        pkgs = self.get_cached_packages(packageTitle)
        return {pkg.version: pkg for pkg in pkgs}.get(version)

    def pack_package(self, package):
        with private_space(dir=tmp_loc):
            self.yarn_comm.add(package)
            with self.package_json as pkg_jsn:
                pkg_jsn_data = pkg_jsn
            with self.yarn_lock as yrn_lk:
                yrn_lk_data = yrn_lk
        dependencies = pkg_jsn_data['dependencies'].items()
        n = len(dependencies)
        if not n:
            raise Exception('no packages found to pack')
        if n > 1:
            raise Exception('multiple packages found to pack')
        package_title = "@".join(list(dependencies)[0])
        installed_version = yrn_lk_data[package_title]['version']
        nrp_name = f"{package}-{installed_version}{self.__cached_pkg_ext}"
        nrp = File(self.cached_path / nrp_name,
                   parser=json.loads, formater=json.dumps)
        nrp.touch()
        nrp.blank_not_ok = True
        with nrp as nrp_data:
            nrp_data['name'] = package
            nrp_data['version'] = installed_version
            nrp_data['ref'] = yrn_lk_data
        return nrpObj(nrp.file_name, package, installed_version)
