import argparse
import json
from routing import hns


def load(file):
    with open(file) as json_file:
        data = json.load(json_file)
        return data


def main():
    parser = argparse.ArgumentParser(description='Run Hostname Domain Server')
    parser.add_argument('--ip', type=str, default="127.0.0.1")
    parser.add_argument('--port', type=int, default=8888)
    args = parser.parse_args()
    try:
        h = hns.HNS(args.ip, args.port)
        h.run()
    except Exception as err:
        print(err)
        return 1


if __name__ == '__main__':
    main()
