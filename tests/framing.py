"""Framing encoding checks, not an AEAD implementation or collision proof."""
import itertools
import unittest


def encode(data, full_marker, final_marker):
    full = len(data) // 16
    blocks = [(full_marker, data[16 * i:16 * (i + 1)]) for i in range(full)]
    tail = data[16 * full:]
    blocks.append((final_marker, tail + b'\x80' + bytes(15 - len(tail))))
    return tuple(blocks)


def decode(blocks, full_marker, final_marker):
    if not blocks or blocks[-1][0] != final_marker:
        raise ValueError('missing final block')
    if any(m != full_marker or len(b) != 16 for m, b in blocks[:-1]):
        raise ValueError('invalid complete block')
    padded = blocks[-1][1]
    if len(padded) != 16:
        raise ValueError('invalid final block size')
    unpadded = padded.rstrip(b'\x00')
    if not unpadded or unpadded[-1] != 0x80:
        raise ValueError('invalid delimiter')
    return b''.join(b for _, b in blocks[:-1]) + unpadded[:-1]


class Framing(unittest.TestCase):
    def test_small_alphabet_and_boundary_injectivity(self):
        samples = {bytes(p) for n in range(7)
                   for p in itertools.product((0, 0x80, 0xff), repeat=n)}
        for n in (0, 1, 15, 16, 17, 31, 32, 33, 63, 64, 65):
            samples.update(bytes([v]) * n for v in (0, 0x80, 0xff))
            samples.add(bytes(range(n)))
        for markers in ((0x11, 0x12), (0x21, 0x22)):
            seen = set()
            for data in samples:
                transcript = encode(data, *markers)
                self.assertEqual(decode(transcript, *markers), data)
                self.assertEqual(len(transcript), len(data) // 16 + 1)
                self.assertNotIn(transcript, seen)
                seen.add(transcript)

    def test_partition_and_empty_final_blocks(self):
        seen = set()
        samples = {bytes([v]) * n for n in (0, 1, 15, 16, 17, 32)
                   for v in (0, 0x80, 0xff)}
        for ad, msg in itertools.product(samples, repeat=2):
            transcript = encode(ad, 0x11, 0x12) + encode(msg, 0x21, 0x22)
            self.assertNotIn(transcript, seen)
            seen.add(transcript)
        for n in (0, 16, 32):
            self.assertEqual(encode(bytes(n), 0x21, 0x22)[-1],
                             (0x22, b'\x80' + bytes(15)))

    def test_malformed_sequences(self):
        for blocks in ((), ((0x11, bytes(16)),), ((0x12, bytes(16)),),
                       ((0x12, bytes(15)),), ((0x12, b'\x81' + bytes(15)),),
                       ((0x21, bytes(16)), (0x12, b'\x80' + bytes(15)))):
            with self.assertRaises(ValueError):
                decode(blocks, 0x11, 0x12)


if __name__ == '__main__':
    unittest.main()
