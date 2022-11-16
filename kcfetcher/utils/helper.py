import os
import shutil

from kcapi import OpenID, Keycloak


def find_in_list(objects, **kwargs):
    # objects - list of dict
    # kwargs - key=value, used to find one object
    key = list(kwargs.keys())[0]
    value = kwargs[key]
    for obj in objects:
        if key in obj and obj[key] == value:
            return obj

def minimize_role_representation(full_role, clients):
    """
    This is used to get a minimal role representation.
    It contains just enough data that sub-role of the composite role can be found.
    Or that role referred by client scope mapping can be found.

    For client roles we replace attribute containerId with containerName, value is set to client.clientId.
    For realm roles, containerId already contains realm name, so attribute is just renamed.

    Complete role representation is stored in realm /roles or client/roles/.
    """
    containerId = full_role["containerId"]
    container_name = containerId
    if full_role["clientRole"]:
        container_name = find_in_list(clients, id=containerId)["clientId"]
    return dict(
        name=full_role["name"],
        clientRole=full_role["clientRole"],
        containerName=container_name,
    )


def remove_ids(kc_object={}):
    # simple scalar values are safe to return
    if isinstance(kc_object, (str, bool, int, float)):
        return kc_object

    # each list element needs to be cleaned recursively
    if isinstance(kc_object, list):
        return [remove_ids(obj) for obj in kc_object]

    # each dict element needs to be cleaned recursively
    assert isinstance(kc_object, dict)
    return {key: remove_ids(kc_object[key]) for key in kc_object if key not in ['id', 'flowId']}


def login(endpoint, user, password, read_token_from_file=False):
    token = None
    if not read_token_from_file:
        token = OpenID.createAdminClient(user, password, endpoint).getToken()
    else:
        token = open('./token').read()
    return Keycloak(token, endpoint)


def normalize(identifier=""):
    identifier = identifier.lower()
    bad_chars = '/ =,:*'
    for bad_char in bad_chars:
        identifier = identifier.replace(bad_char, '_')
    return identifier


def make_folder(name):
    if not os.path.isdir(name):
        os.makedirs(name)


def remove_folder(name):
    if os.path.isdir(name):
        shutil.rmtree(name)
