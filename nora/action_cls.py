from .cls import NoraFS
import re


class ActionClass:
    fs = NoraFS()

    def pack_packages(self, packages):
        if not len(packages):
            packages = self.fs.package_json.all_packages().keys()
        for pkg in packages:
            nrp = _.fs.pack_package(pkg)
            print(f"package packed '{nrp.id}'")

    @staticmethod
    def append_packages(packages, isDev):
        shape = r'(?P<name>@?[\d\w/\\-]*)(@(?P<version>\d*\.\d*\.\d*))?'
        for pkg in packages:
            name, version = re.match(shape, pkg).groupdict().values()
            if version:
                res = _.fs.get_cached_packege_of_specific_version(
                    name, version)
            else:
                res = _.fs.get_latest_cached_package(name)
            if res:
                with _.fs.package_json as pkg_jsn:
                    if isDev:
                        deps = pkg_jsn['devDependencies']
                    else:
                        deps = pkg_jsn['dependencies']
                    deps[res.title] = res.version
            else:
                print(f'"{pkg}" is not cached')

    def lock(self):
        with self.fs.package_json as pkg_jsn:
            packages = {**pkg_jsn['dependencies'],
                        **pkg_jsn['devDependencies']}.items()
        nrps = [self.fs.get_latest_cached_package(
            pkg[0]) for pkg in packages]
        # print(nrps)
        lock_data = {key: val for nrp in nrps for key, val in nrp.lock.items()}
        with self.fs.yarn_lock as yrn_lk:
            yrn_lk.update(lock_data)

    def add(self, packages, isDev):
        self.append_packages(packages, isDev)
        self.lock()
        self.fs.yarn_comm.offline()


_ = ActionClass()
