"""
config class for dwcom
"""
import atexit
import os
import sys
import types
from conf import conf
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

_STASH_KEY = '_dwcom_singleton_config'

def get_or_create():
    """Return the singleton Config instance, creating it on first call.
    On plugin reload, the same observer keeps running and the config is refreshed.
    """
    stash = sys.modules.get(_STASH_KEY)
    if stash is not None:
        stash.instance.reloadConf()
        return stash.instance
    instance = Config()
    stash = types.ModuleType(_STASH_KEY)
    stash.instance = instance
    sys.modules[_STASH_KEY] = stash
    return instance

class Config:
    def __init__(self):
        self.serverConfigs = conf.servers()
        self.watcher = ConfigWatcher('ttcom.conf', self.reloadConf)
        self.observer = Observer()
        self.observer.schedule(self.watcher, '.', recursive=False)
        self.observer.start()
        atexit.register(self.close)

    def get(self, serverName: str, itemName: str):
        serverConfig = self.serverConfigs.get(serverName)
        if serverConfig is None: return None
        try:
            return self._convertConfigValue(serverConfig[itemName])
        except KeyError:
            return None

    @staticmethod
    def _convertConfigValue(configValue: str):
        if configValue.isnumeric() and configValue != '1' and configValue != '0': return float(configValue)
        match configValue.lower():
            case 'y' | 'yes' | '1' | 'true': return True
            case 'n' | 'no' | '0' | 'false': return False
            case _: return configValue

    def reloadConf(self):
        self.serverConfigs = conf.servers()

    def close(self):
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join(timeout=2)
        sys.modules.pop(_STASH_KEY, None)

    def __del__(self):
        self.close()

class ConfigWatcher(FileSystemEventHandler):
    def __init__(self, configPath, reloadFunc):
        self.configPath = os.path.abspath(configPath)
        self.reloadFunc = reloadFunc

    def on_modified(self, event):
        if event.is_directory: return
        if os.path.abspath(event.src_path) != self.configPath: return
        self.reloadFunc()
