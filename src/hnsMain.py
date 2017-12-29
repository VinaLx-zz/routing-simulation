import argparse
import json


def load(file):
    with open(file) as json_file:
        data = json.load(json_file)
        return data


def main():
    parser = argparse.ArgumentParser(description='Run Hostname Domain Server')
    parser.add_argument('--config', type=str, default="hns_config.txt")
    args = parser.parse_args()
    try:
        data = load(args.config)
        print(data)
    except Exception as err:
        print(err)
        return 1

if __name__ == '__main__':
    main()
