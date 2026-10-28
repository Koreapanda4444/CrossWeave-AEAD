"""Compare native C with a separate mathematical code path, both directions."""
import random
import subprocess
import sys
from oracle import permutation


def run(driver):
    rng = random.Random(0x63726f7373776561)
    sources = [bytes(48), b'\xff' * 48, bytes(range(48))]
    sources += [rng.randbytes(48) for _ in range(32)]
    cases = [(data, first, count, inv) for data in sources for first in range(17)
             for count in range(17 - first) for inv in (False, True)]
    for bit in range(384):
        data = (1 << bit).to_bytes(48, 'little')
        cases.extend((data, 0, count, inv) for count in (12, 16) for inv in (False, True))
    payload = b''.join(bytes((first, count, inv)) + data for data, first, count, inv in cases)
    result = subprocess.run([driver], input=payload, capture_output=True, check=True).stdout
    if len(result) != 48 * len(cases):
        raise AssertionError('unexpected C driver output size')
    for index, (data, first, count, inv) in enumerate(cases):
        expected = permutation(data, first, count, inverse=inv)
        if result[48 * index:48 * (index + 1)] != expected:
            raise AssertionError((index, data.hex(), first, count, inv))
    print(f'C versus independent oracle: {len(cases)} interval/direction cases passed')


if __name__ == '__main__':
    run(sys.argv[1])
