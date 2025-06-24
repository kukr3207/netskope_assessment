import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SLAConfig:
    def __init__(self, path="sla_config.yaml"):
        self.path = path
        self._load()
        self._start_watcher()

    def _load(self):
        with open(self.path) as f:
            self.data = yaml.safe_load(f)
        print("Loaded SLA config", self.data)

    def _start_watcher(self):
        class ReloadHandler(FileSystemEventHandler):
            def __init__(self, outer): self.outer = outer
            def on_modified(self, event):
                if event.src_path.endswith(self.outer.path):
                    self.outer._load()
        observer = Observer()
        observer.schedule(ReloadHandler(self), path='.', recursive=False)
        observer.daemon = True
        observer.start()

    def get(self, priority, tier):
        return self.data.get(priority, {}).get(tier, {})

config = SLAConfig()