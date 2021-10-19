class nameddic(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)


class MyRepo(nameddic):
    def __init__(self):
        super().__init__()

    def add_tag_class(self, tag, obj):
        if tag not in self:
            self[tag] = [obj]
        else:
            self[tag].append(obj)
