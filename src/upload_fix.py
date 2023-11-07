from fbchat import _util, _exception


def upload(self, files, voice_clip=False):
    """Upload files to Facebook.

    `files` should be a list of files that requests can upload, see
    `requests.request <https://docs.python-requests.org/en/master/api/#requests.request>`_.

    Return a list of tuples with a file's ID and mimetype.
    """
    file_dict = {"upload_{}".format(i): f for i, f in enumerate(files)}

    data = {"voice_clip": voice_clip}

    j = self._payload_post(
        "https://upload.facebook.com/ajax/mercury/upload.php", data, files=file_dict
    )

    if len(j["metadata"]) != len(files):
        raise _exception.FBchatException(
            "Some files could not be uploaded: {}, {}".format(j, files)
        )

    if isinstance(j["metadata"], list):
        return [
            (data[_util.mimetype_to_key(data["filetype"])], data["filetype"])
            for data in j["metadata"]
        ]

    return [
        (data[_util.mimetype_to_key(data["filetype"])], data["filetype"])
        for _, data in j["metadata"].items()
    ]