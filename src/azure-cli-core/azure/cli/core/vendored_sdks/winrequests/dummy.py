class Dummy:
    def __getattr__(self, name):
        return Dummy()

    def __getitem__(self, name):
        return Dummy()
