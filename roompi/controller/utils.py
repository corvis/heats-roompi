import os


def resolve_path(path, context=""):
    """
    Returns absolute path for given path argument.
    In case if given path is already absolute - returns it as it is.
    Otherwise - transforms to absolute relaying on the context parameter which should be directory path.
    In case if context is not set it considers workdir to be the context
    :param path:
    :param context:
    :return:
    """
    if os.path.isabs(path):
        return path
    else:
        return os.path.join(context, os.path.realpath(path))