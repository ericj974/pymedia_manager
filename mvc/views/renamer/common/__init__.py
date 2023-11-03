from common import nameddic


class MyRepo(nameddic):
    def __init__(self):
        super().__init__()

    def add_tag_class(self, tag, obj):
        if tag not in self:
            self[tag] = [obj]
        else:
            self[tag].append(obj)
