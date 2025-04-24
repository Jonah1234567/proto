class OutputsProxy:
    def __init__(self):
        self._data = {}

    def __setattr__(self, name, value):
        if name == "_data":
            super().__setattr__(name, value)
        else:
            self._data[name] = value

    def to_dict(self):
        return self._data
