class OutputsProxy:
    def __init__(self):
        self._values = {}

    def set_name(self, name):
        self._values[name] = None  # or a default value
        setattr(self, name, None)


    def set_names(self, names):
        for name in names:
            self._values[name] = None  # or a default value
            setattr(self, name, None)

    def __getattr__(self, name):
        return self._values.get(name)

    def __getitem__(self, key):
        return self._values.get(key)

    def set_value(self, name, value):
        self._values[name] = value
        setattr(self, name, value)

    def __setattr__(self, name, value):
        if name in ("_values",):
            super().__setattr__(name, value)
        else:
            self._values[name] = value
            super().__setattr__(name, value)

    def to_dict(self):
        return self._values.copy()
    
    def from_dict(self, d):
        if not isinstance(d, dict):
            raise TypeError(f"Expected dict in from_dict, got {type(d).__name__}: {d}")
        self._values = d.copy()  # No need to wrap again in dict()
        for key, value in self._values.items():
            setattr(self, key, value)

    def to_list(self):
        return list(self._values.keys())
