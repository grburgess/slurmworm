import pkg_resources
import os
from shutil import copyfile
import yaml


def get_path_of_data_file(data_file):
    file_path = pkg_resources.resource_filename("slurmworm", "data/%s" % data_file)

    return file_path


def get_path_of_data_dir():
    file_path = pkg_resources.resource_filename("slurmworm", "data")

    return file_path


def copy_package_data(data_file):

    data_file_path = get_path_of_data_file(data_file)
    copyfile(data_file_path, "./%s" % data_file)


def get_path_of_user_dir():
    """
    Returns the path of the directory containing the user data (~/.slurmworm)

    :return: an absolute path
    """

    return os.path.abspath(os.path.expanduser("~/.config/slurmworm"))


def get_access_file():
    access_path = os.path.join(get_path_of_user_dir(), "access.yaml")
    with open(access_path) as f:
        # The FullLoader parameter handles the conversion from YAML
        # scalar values to Python the dictionary format
        access = yaml.load(f, Loader=yaml.SafeLoader)

    return access


def get_imap_file():
    imap_path = os.path.join(get_path_of_user_dir(), "imap_monitor.ini")
    
    return imap_path
