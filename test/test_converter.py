import json
import unittest

from convert import Converter


def show_case(i, o, desc=None):
    if isinstance(desc, str):
        print('\n-----\n<<Description:>>\n', desc, '\n')
    print('<<Input Template:>>\n', i, '\n')
    print('<<Output JSON:>>\n', json.dumps(o, indent=2))


class TestConverter(unittest.TestCase):
    """
    Purpose to show usages :) without assertions.
    """

    def test_raw_template(self):
        template = '{name=(foo)age=(99)boy=(True)tools=(None)}'
        raw = Converter(template).convert(None)
        show_case(template, raw, 'Without source, it can be standalone raw JSON.')

    def test_raw_escape(self):
        template = '{x=(&123;&123;&60;&40;foo&41;&62;&125;&125;)y=(&32;)z=(&9;&10;&13;&92;)i=(\\)j=(\\&61;True)}'
        raw = Converter(template).convert(None)
        show_case(template, raw, 'All escaped char showcase.')

    def test_from_file(self):
        template = '{</servers>ss=[{n=(./name)}]datetime=(/time)x=(&32;&92;)}'
        with open('./1.json', 'r') as f:
            data = json.load(f)
            conv = Converter(template)
            dest = conv.convert(data)
            show_case(template, dest, 'Simple case show how to extract data from source /servers.')

    def test_deep_recur(self):
        template = '{</servers>\n' \
                   '    ss=[{n=(./name)\n' \
                   '        d=[<./disks>{\n' \
                   '            u=(./uuid)\n' \
                   '            t=(./type)\n' \
                   '            clone=(True)\n' \
                   '        }]\n' \
                   '    }]\n' \
                   '    datetime=(/time)\n' \
                   '}'
        with open('./2.json', 'r') as f:
            data = json.load(f)
            conv = Converter(template)
            dest = conv.convert(data)
            show_case(template, dest, 'More complex demo illustrates recursive expression.\n In additionally, '
                                      'you can write your template formattly, not just in one line.')


if __name__ == '__main__':
    unittest.main()
