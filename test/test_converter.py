import json
import unittest

from convert import Converter


def pretty_print(o):
    print(json.dumps(o, indent=2))


class TestConverter(unittest.TestCase):

    def test_from_file(self):
        template = '{</servers>ss=[{n=(./name)}]datetime=(/time)x=(&32;&92;)}'
        with open('./1.json', 'r') as f:
            data = json.load(f)
            conv = Converter(template)
            dest = conv.convert(data)
            pretty_print(dest)

    def test_deep_recur(self):
        template = '{</servers>ss=[{n=(./name)d=[<./disks>{u=(./uuid)t=(./type)clone=(True)}]}]datetime=(/time)}'
        with open('./2.json', 'r') as f:
            data = json.load(f)
            conv = Converter(template)
            dest = conv.convert(data)
            pretty_print(dest)


if __name__ == '__main__':
    unittest.main()
