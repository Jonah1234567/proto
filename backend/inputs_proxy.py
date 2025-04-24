class InputsProxy:
    def __init__(self, data):
        self._data = data

    def __getattr__(self, name):
        return self._data[name]

    def __getitem__(self, name):
        return self._data[name]
