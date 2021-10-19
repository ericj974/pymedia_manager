class ClassWithTag(object):
    # Class level
    tag = ''

    def __init__(self, ext):
        self.ext = ext

    # register to the repo under one or several tags
    @classmethod
    def register_tag(cls, repo_parsers):
        repo_parsers.add_tag_class(tag=cls.tag, obj=cls)
