from types import SimpleNamespace

class InputsProxy(SimpleNamespace):
    def __init__(self):
        super().__init__()
        self._values = {}

    def set_name(self, name):
        self._values[name] = None
        setattr(self, name, None)

    def set_names(self, names):
        for name in names:
            self.set_name(name)

    def set_value(self, name, value):
        self._values[name] = value
        setattr(self, name, value)

    def to_dict(self):
        return self._values.copy()

    def from_dict(self, d):
        if not isinstance(d, dict):
            raise TypeError(f"Expected dict in from_dict, got {type(d).__name__}")
        self._values = d.copy()
        for key, value in d.items():
            setattr(self, key, value)

    def to_list(self):
        return list(self._values.keys())

    def __getitem__(self, key):
        return self._values.get(key)

    def __getattr__(self, name):
        # fallback for missing attributes
        if name in self._values:
            return self._values[name]
        return super().__getattribute__(name)
