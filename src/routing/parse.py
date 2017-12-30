import json


def parse(data):
    """ Parse raw data to a json-type dict
      Args: raw data
    """
    return json.loads(data.decode())
