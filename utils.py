import re


def semver_sort(items: list) -> list:
    pattern = re.compile(r"""([^\-.0-9]+)?[\-.]?(\d+)?\.?(\d+)?\.?(\d+)?[\-.]?(.*)?""")

    def key_func(x: str):
        m = pattern.match(x)
        return [m.group(1) or '', int(m.group(2) or '0'), int(m.group(3) or '0'), int(m.group(4) or '0'),
                m.group(5) or '~']

    return sorted(items, key=key_func)
