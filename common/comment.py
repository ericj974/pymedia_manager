import json
from abc import abstractmethod
from pathlib import Path

import piexif

from common.exif import set_user_comment, get_exif, save_exif


class Entity(object):

    @staticmethod
    @abstractmethod
    def type():
        raise NotImplementedError()

    @abstractmethod
    def to_dict(self):
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def from_dict(dic):
        raise NotImplementedError()


class CommentEntity(Entity):

    @staticmethod
    def type():
        return 'comment'

    def __init__(self, content: str):
        self.data = content

    def to_dict(self):
        return {'type': CommentEntity.type(), 'data': self.data}

    @staticmethod
    def from_dict(dic):
        return CommentEntity(dic['data'])


class TagEntity(Entity):
    @staticmethod
    def type():
        return 'tag'

    def __init__(self, name: str):
        self.name: str = name

    def __lt__(self, other):
        return self.lower().__lt__(other.lower())

    def __eq__(self, other):
        return self.lower().__eq__(other.lower())

    def __hash__(self):
        return self.lower().__hash__()

    def lower(self):
        return self.name.lower()

    def to_dict(self):
        return {'type': self.type(), 'name': self.name}

    @staticmethod
    def from_dict(dic):
        return TagEntity(dic['name'])


class PersonEntity(TagEntity):
    @staticmethod
    def type():
        return 'person'

    def __init__(self, name: str, location: tuple):
        super(PersonEntity, self).__init__(name)
        self.location = location  # (Top, Left, Bottom, Right)

    def to_dict(self):
        return {'type': self.type(), 'name': self.name, 'location': f"{self.location}"}

    @staticmethod
    def from_dict(dic):
        return PersonEntity(name=dic['name'], location=eval(dic['location']))


class UserComment(object):

    def __init__(self, entities: list[Entity] = None):
        entities = entities if entities else []
        # Only one CommentEntity allowed in the list
        comment_entity_list = [i for i in entities if i.type == CommentEntity.type]
        assert len(comment_entity_list) <= 1, "Only one Comment entity allowed"

        self._entity_comment: CommentEntity = comment_entity_list[0] if comment_entity_list else None
        self.entities: list[Entity] = entities if entities else []

    @property
    def persons(self) -> list[PersonEntity]:
        return [i for i in self.entities if i.type == PersonEntity.type]

    @property
    def tags(self) -> list[TagEntity]:
        return [i for i in self.entities if i.type == TagEntity.type]

    @property
    def comment(self) -> CommentEntity:
        return self._entity_comment

    def add_entity(self, entity: Entity):
        # Ensure unique name
        if isinstance(entity, PersonEntity):
            _temp = [person.name for person in self.persons]
            if entity.name in _temp:
                return
        self.entities.append(entity)

    def to_dict(self):
        return [i.to_dict() for i in self.entities]

    @staticmethod
    @abstractmethod
    def from_dict(user_comment_dic):
        raise NotImplementedError()

    @staticmethod
    def entities_from_dict(user_comment_dic):
        entities = []
        for tmp in user_comment_dic:
            if tmp['type'] == CommentEntity.type():
                entity = CommentEntity.from_dict(tmp)
                entities.append(entity)
            elif tmp['type'] == TagEntity.type():
                entity = TagEntity.from_dict(tmp)
                entities.append(entity)
            elif tmp['type'] == PersonEntity.type():
                entity = PersonEntity.from_dict(tmp)
                entities.append(entity)
        return entities

    @abstractmethod
    def save_comment(self, file):
        """
        Save the user comment to the file
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def load_from_file(file):
        """
        Load the user comment portion from the metadata
        """
        raise NotImplementedError()


class ImageUserComment(UserComment):
    def __init__(self, entities: list[Entity] = None):
        super().__init__(entities)

    def update_exif(self, exif_dict):
        set_user_comment(exif_dict, self.to_dict())

    def save_comment(self, file):
        exif_dic = get_exif(file)
        self.update_exif(exif_dic)
        save_exif(exif_dict=exif_dic, path=file)

    @staticmethod
    def load_from_file(path: Path):
        exif_dict = get_exif(path)
        if piexif.ExifIFD.UserComment in exif_dict["Exif"]:
            try:
                user_comment_dic = piexif.helper.UserComment.load(exif_dict["Exif"][piexif.ExifIFD.UserComment])
                user_comment_dic = json.loads(user_comment_dic)
                return ImageUserComment.from_dict(user_comment_dic)
            except:
                return ImageUserComment()
        return ImageUserComment()

    @staticmethod
    def from_dict(user_comment_dic):
        return ImageUserComment(UserComment.entities_from_dict(user_comment_dic))


class VideoUserComment(UserComment):
    def __init__(self, entities: list[Entity] = None):
        super().__init__(entities)

    def update_exif(self, exif_dict):
        set_user_comment(exif_dict, self.to_dict())

    def save_comment(self, file):
        return
        exif_dic = get_exif(file)
        self.update_exif(exif_dic)
        save_exif(exif_dict=exif_dic, path=file)

    @staticmethod
    def load_from_file(file):
        # TODO: Update this
        return VideoUserComment()

    @staticmethod
    def from_dict(user_comment_dic):
        return VideoUserComment(UserComment.entities_from_dict(user_comment_dic))
