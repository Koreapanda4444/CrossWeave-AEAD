"""Bounded public-permutation experiments; no security-strength certification."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import random
import resource
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
SEED = 0x63726f7373776561
MASK = (1 << 64) - 1


def rol(x, n):
    return ((x << n) | (x >> (64 - n))) & MASK


def pack(words):
    return b''.join(x.to_bytes(8, 'little') for x in words)


def unpack(data):
    return [int.from_bytes(data[i:i + 8], 'little') for i in range(0, 48, 8)]


def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


class Oracle:
    def __init__(self, driver):
        self.driver = driver
        self.queries = 0
        self.calls = 0
        self.peak_payload = 0

    def run(self, states, first, count):
        payload = b''.join(bytes((first, count, 0)) + x for x in states)
        self.queries += len(states)
        self.calls += 1
        self.peak_payload = max(self.peak_payload, len(payload))
        raw = subprocess.run([self.driver], input=payload, capture_output=True, check=True).stdout
        if len(raw) != len(states) * 48:
            raise AssertionError('truncated native oracle response')
        return [raw[i:i + 48] for i in range(0, len(raw), 48)]


def experiment(driver):
    start = time.perf_counter()
    rng = random.Random(SEED)
    native = Oracle(driver)
    structured = {bytes(48), b'\xff' * 48, bytes(range(48))}
    structured.update((1 << i).to_bytes(48, 'little') for i in range(384))
    structured.update(bytes([x]) * 48 for x in (1, 0x55, 0xaa, 0x80))
    structured = sorted(structured)
    random_states = [rng.randbytes(48) for _ in range(1024)]
    states = structured + random_states
    fixed = []
    for count in (1, 2, 3, 4, 12, 16):
        out = native.run(states, 0, count)
        twice = native.run(out, 0, count)
        fixed.append({'rounds': count, 'states': len(states),
                      'fixed_points': sum(a == b for a, b in zip(states, out)),
                      'cycles_of_length_at_most_two': sum(a == b for a, b in zip(states, twice))})

    sym_states = random_states[:128]
    transforms = [('bit_rotation', n) for n in range(1, 64)] + \
                 [('lane_rotation', n) for n in range(1, 6)] + [('complement', 0)]

    def transform(data, kind, n):
        words = unpack(data)
        if kind == 'bit_rotation':
            return pack(rol(x, n) for x in words)
        if kind == 'lane_rotation':
            return pack(words[n:] + words[:n])
        return bytes(x ^ 255 for x in data)

    symmetry = []
    for count in (1, 2, 4, 12, 16):
        base = native.run(sym_states, 0, count)
        rows = []
        for kind, n in transforms:
            out = native.run([transform(x, kind, n) for x in sym_states], 0, count)
            matches = sum(y == transform(p, kind, n) for p, y in zip(base, out))
            rows.append({'transform': kind, 'amount': n, 'matches': matches})
        symmetry.append({'rounds': count, 'states_per_transform': len(sym_states),
                         'transforms': len(rows), 'maximum_matches': max(x['matches'] for x in rows),
                         'nonzero_matches': [x for x in rows if x['matches']]})

    differential = []
    diff_states = random_states[:16]
    for count in (1, 2, 3, 4, 12, 16):
        base = native.run(diff_states, 0, count)
        weights = []
        highest = 0
        minimum_case = None
        for bit in range(384):
            delta = (1 << bit).to_bytes(48, 'little')
            out = native.run([xor(x, delta) for x in diff_states], 0, count)
            differences = [xor(p, y) for p, y in zip(base, out)]
            if bytes(48) in differences:
                raise AssertionError('a nonzero difference disappeared in a permutation')
            highest = max(highest, max(Counter(differences).values()))
            for sample, difference in enumerate(differences):
                weight = int.from_bytes(difference, 'little').bit_count()
                if not weights or weight < min_weight:
                    min_weight = weight
                    minimum_case = {'input_bit': bit, 'sample': sample,
                                    'input': diff_states[sample].hex(), 'difference': difference.hex()}
                weights.append(weight)
        differential.append({'rounds': count, 'input_differences': 384,
                             'pairs_per_difference': len(diff_states), 'pairs': len(weights),
                             'minimum_weight': min(weights), 'maximum_weight': max(weights),
                             'mean_weight': round(sum(weights) / len(weights), 6),
                             'largest_identical_output_count_per_difference': highest,
                             'minimum_case': minimum_case})

    # Proven one-round dependency distinguisher, for delta in input lane 0.
    # Output lanes 0,3,5 have zero difference; lane 4 has ROL(delta,43).
    checks = 0
    witness = None
    deltas = (1, 1 << 31, 1 << 63, MASK)
    for first in range(16):
        base = native.run(random_states[:32], first, 1)
        for alpha in deltas:
            changed = [xor(x, pack([alpha, 0, 0, 0, 0, 0])) for x in random_states[:32]]
            out = native.run(changed, first, 1)
            for sample, (a, b) in enumerate(zip(base, out)):
                d = unpack(xor(a, b))
                assert d[0] == d[3] == d[5] == 0 and d[4] == rol(alpha, 43)
                checks += 1
                if witness is None:
                    witness = {'first_round': first, 'input': random_states[sample].hex(),
                               'input_delta': pack([alpha, 0, 0, 0, 0, 0]).hex(),
                               'output_delta': xor(a, b).hex()}

    targets = ['src/crossweave_p384.c', 'src/crossweave_internal.h',
               'src/crossweave_constants.h', 'include/crossweave.h', 'docs/spec_ko.md',
               'tests/stage_vectors.h', 'tests/permutation_vectors.h', 'tests/oracle.py',
               'tests/oracle_driver.c', 'research/early_gate.py']
    fingerprints = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in targets}
    full_round_flags = [x for x in fixed if x['rounds'] in (12, 16) and
                        (x['fixed_points'] or x['cycles_of_length_at_most_two'])]
    full_round_flags += [x for x in symmetry if x['rounds'] in (12, 16) and x['maximum_matches']]
    full_round_flags += [x for x in differential if x['rounds'] in (12, 16) and
                        x['largest_identical_output_count_per_difference'] > 1]
    result = {'seed': SEED, 'round_start': 0, 'fingerprints': fingerprints,
              'fixed_point_search': fixed, 'commutation_search': symmetry,
              'single_bit_differentials': differential,
              'one_round_distinguisher': {'checks': checks, 'oracle_queries_per_attack': 2,
                                         'random_permutation_pass_probability': '2^128/(2^384-1)',
                                         'witness': witness},
              'full_round_flags_in_bounded_search': full_round_flags,
              'oracle_queries': native.queries, 'native_processes': native.calls,
              'largest_native_input_bytes': native.peak_payload}
    measurements = {'elapsed_seconds': round(time.perf_counter() - start, 6),
                    'python_max_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    'largest_child_max_rss_kib': resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                    'python': platform.python_version(), 'platform': platform.platform()}
    if full_round_flags:
        raise RuntimeError('Investigate full-round candidates before continuing: ' + json.dumps(result))
    return {'observations': result, 'measurements': measurements}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('driver')
    parser.add_argument('--write', type=Path)
    parser.add_argument('--check', type=Path)
    args = parser.parse_args()
    report = experiment(args.driver)
    if args.check and json.loads(args.check.read_text())['observations'] != report['observations']:
        raise SystemExit('Gate observations or target fingerprints changed; investigate and rerun analysis')
    if args.write:
        args.write.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
