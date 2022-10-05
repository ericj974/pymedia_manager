FILE_EXTENSION_PHOTO_JPG = ['jpg', 'jpeg']
FILE_EXTENSION_PHOTO_HEIF = ['heic']
FILE_EXTENSION_VIDEO = ['avi', 'mts', 'mp4', 'mov', 'wmv']
FILE_EXTENSION_PHOTO = FILE_EXTENSION_PHOTO_JPG + FILE_EXTENSION_PHOTO_HEIF + ['png'] + ['bmp']
FILE_EXTENSION_MEDIA = FILE_EXTENSION_PHOTO_JPG + FILE_EXTENSION_VIDEO
ALL_FILE_EXTENSIONS = FILE_EXTENSION_PHOTO_JPG + FILE_EXTENSION_PHOTO_HEIF + FILE_EXTENSION_VIDEO

# Photo extensions allowed
FILE_EXTENSION_PHOTO_JPG.extend([extension.upper() for extension in FILE_EXTENSION_PHOTO_JPG])

# Photo heif extension allowed
FILE_EXTENSION_PHOTO_HEIF.extend([extension.upper() for extension in FILE_EXTENSION_PHOTO_HEIF])

# Video extension allowed
FILE_EXTENSION_VIDEO.extend([extension.upper() for extension in FILE_EXTENSION_VIDEO])