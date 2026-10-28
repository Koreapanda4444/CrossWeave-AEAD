"""Independent, slow mathematical oracle for tests; not a shipping library.

FIPS 202 Keccak-f[1600]/SHAKE256, with generated round/rotation constants.
No C implementation, hashlib output, or generated CrossWeave table is imported.
"""
MASK = (1 << 64) - 1


def rol(x, n):
    n %= 64
    return ((x << n) | (x >> ((64 - n) % 64))) & MASK


def keccak(state):
    rho = [0] * 25
    x, y = 1, 0
    for t in range(24):
        rho[x + 5 * y] = (t + 1) * (t + 2) // 2 % 64
        x, y = y, (2 * x + 3 * y) % 5
    lfsr = 1
    for _ in range(24):
        c = [state[x] ^ state[x + 5] ^ state[x + 10] ^
             state[x + 15] ^ state[x + 20] for x in range(5)]
        d = [c[(x - 1) % 5] ^ rol(c[(x + 1) % 5], 1) for x in range(5)]
        a = [v ^ d[i % 5] for i, v in enumerate(state)]
        b = [0] * 25
        for y in range(5):
            for x in range(5):
                b[y + 5 * ((2 * x + 3 * y) % 5)] = rol(a[x + 5 * y], rho[x + 5 * y])
        state = [b[x + 5 * y] ^ ((~b[(x + 1) % 5 + 5 * y]) &
                 b[(x + 2) % 5 + 5 * y]) for y in range(5) for x in range(5)]
        rc = 0
        for j in range(7):
            if lfsr & 1:
                rc ^= 1 << ((1 << j) - 1)
            lfsr = ((lfsr << 1) ^ (0x71 if lfsr & 0x80 else 0)) & 255
        state[0] ^= rc
    return state


def shake256(data, length):
    rate = 136
    padded = bytearray(data)
    padded.append(0x1f)
    padded.extend(bytes((-len(padded)) % rate))
    padded[-1] ^= 0x80
    state = [0] * 25
    for offset in range(0, len(padded), rate):
        for i in range(rate // 8):
            state[i] ^= int.from_bytes(padded[offset + 8 * i:offset + 8 * (i + 1)], 'little')
        state = keccak(state)
    out = bytearray()
    while len(out) < length:
        out.extend(b''.join(x.to_bytes(8, 'little') for x in state[:rate // 8]))
        if len(out) < length:
            state = keccak(state)
    return bytes(out[:length])


def round_constants():
    return [[int.from_bytes(shake256(f'cw-p384/round-{r}/lane-{j}'.encode('ascii'), 8),
                            'little') for j in (0, 3)] for r in range(16)]


def mix(x, y, r, i):
    return (rol(x, (7 * i + 3 * r) % 63 + 1) ^
            rol(y, (13 * i + 5 * r) % 63 + 1) ^
            (x & rol(y, 11)) ^ ((x + y) & MASK))


def stages(words, r, constants):
    # Snapshot each parity: this independently expresses the bipartite update.
    even = [v ^ mix(words[(i + 1) % 6], words[(i - 1) % 6], r, i)
            if i % 2 == 0 else v for i, v in enumerate(words)]
    odd = [v ^ mix(even[(i + 1) % 6], even[(i - 1) % 6], r, i)
           if i % 2 else v for i, v in enumerate(even)]
    added = odd.copy()
    added[0] ^= constants[r][0]
    added[3] ^= constants[r][1]
    shuffled = [rol(added[p], n) for p, n in
                zip((2, 5, 1, 4, 0, 3), (1, 7, 19, 31, 43, 57))]
    return even, odd, added, shuffled
