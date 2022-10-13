from abc import abstractmethod


class MediaWithMetadata(object):

    @abstractmethod
    def open_media(self, file, **kwargs):
        """

        :param file:
        :return:
        """

    @abstractmethod
    def save_media(self, file, **kwargs):
        """ Save the media """
        pass

    @abstractmethod
    def load_comment(self):
        """
        Update the comments
        :return: user_comment:  comment in the following dic form
        {
            'comments': Comments,
            'tags': list of tags in a single string format with whitespace as separator
        }
        """

    @abstractmethod
    def save_comment(self, user_comment, file=None):
        """
        If handled by the file format, save user_comment in the media file metadata
        :param user_comment:  comment in the following dic form
        {
            'comments': Comments,
            'tags': list of tags in a single string format with whitespace as separator
        }
        :return: None
        """

