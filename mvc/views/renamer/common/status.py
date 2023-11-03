from mvc.views.renamer import Status


class StatusPhoto(Status):
    exif_only = 'Only Exif'
    filename_exact_only = 'Only Filename'
    conflict_exif_filename = 'Conflict exif / filename'
