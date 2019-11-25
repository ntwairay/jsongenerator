import os, uuid, json
from jsonmerge import merge, Merger

schema = {
    "properties": {
        "ConnectorGallery": {
            "type": "array",
            "mergeStrategy": "arrayMergeById",
            "mergeOptions": {"idRef": "Id"}
        }
    }
}

base_path = './json/base.json'
head_path = './json/head.json'


def merge_head_to_base (base, head):
    merger = Merger(schema)
    result = merger.merge(base, head)
    return result

def main():
    with open(base_path) as json_file:
        base = json.load(json_file)

    with open(head_path) as json_file:
        head = json.load(json_file)

    with open('result.json', 'w') as outfile:
        result = merge_head_to_base(base, head)
        json.dump(result, outfile)

if __name__ == '__main__':
    main()