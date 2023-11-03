import unittest
from pathlib import Path

from common.comment import UserComment
from common.db import TagDBItem
from mvc.controllers.main import MainController
from mvc.models.main import MainModel
from resources import test_controller, test_db_tags

default_pics_folder = Path(test_controller.__file__).parent
default_db_tags_folder = Path(test_db_tags.__file__).parent


class MainControllerTest(unittest.TestCase):

    def test_update_dirpath(self):
        # Create a mock model
        model = MainModel()
        controller = MainController(model)

        # Create a mock event
        event = default_pics_folder

        # Update the dirpath
        controller.update_dirpath(event)

        # Assert that the model's dirpath has been updated
        self.assertEqual(model.dirpath, event)

        # Assert that the controller has added the event's path to its file watcher
        self.assertTrue(str(event) in controller._watcher.directories())

    def test_set_media_path(self):
        # Create a mock model
        model = MainModel()
        controller = MainController(model)

        # Create a mock path
        path = default_pics_folder / "pic1.jpg"

        # Set the media path
        controller.set_media_path(path)

        # Assert that the model's media path has been updated
        self.assertEqual(model.media_path, path)

        # Assert that the controller has added the path to its file watcher
        self.assertTrue(str(path) in controller._watcher.files())

    def test_set_db_tags_path(self):
        # Create a mock model
        model = MainModel()
        controller = MainController(model)

        # Create a mock path
        path = default_db_tags_folder

        # Set the db tags path
        controller.set_db_tags_path(path)

        # Assert that the model's db tags path has been updated
        self.assertEqual(model._db_tags.dirpath, path)

    def test_add_tag_to_db(self):
        # Create a mock model
        model = MainModel()
        controller = MainController(model)

        # Create a mock tag
        tag = TagDBItem("tag_name")

        # Add the tag to the db
        controller.add_tag_to_db(tag)

        # Assert that the tag has been added to the model's db tags
        self.assertIn(tag, model._db_tags.db)

    def test_update_media_comment(self):
        # Create a mock model
        model = MainModel()
        controller = MainController(model)

        # Update the dirpath
        controller.update_dirpath(default_pics_folder)

        # Set the model's media path
        model.media_path = default_pics_folder / "pic1.jpg"

        # Create a mock comment
        comment = UserComment()

        # Update the media comment
        controller.update_media_comment(comment)

        # Assert that the model's media comment has been updated
        self.assertEqual(model.media_comment, comment)

    def test_next_media(self):
        # Create a mock model
        model = MainModel()
        controller = MainController(model)

        # Update the dirpath
        controller.update_dirpath(default_pics_folder)

        # Set the model's media path
        model.media_path = default_pics_folder / "pic1.jpg"

        # Get the next media
        controller.select_next_media()

        # Assert that the next media is the second file in the model's files list
        self.assertEqual(model.media_path, default_pics_folder / "pic2.jpg")

    def test_prev_media(self):
        # Create a mock model
        model = MainModel()
        controller = MainController(model)

        # Update the dirpath
        controller.update_dirpath(default_pics_folder)

        # Set the model's media path
        model.media_path = default_pics_folder / "pic2.jpg"

        # Get the previous media
        controller.select_prev_media()

        # Assert that the next media is the second file in the model's files list
        self.assertEqual(model.media_path, default_pics_folder / "pic1.jpg")
