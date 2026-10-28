#include "crossweave_internal.h"
#include "crossweave_constants.h"

static uint64_t mix(uint64_t x, uint64_t y, unsigned round, unsigned lane)
{
    return cw_rol64(x, (7u * lane + 3u * round) % 63u + 1u) ^
           cw_rol64(y, (13u * lane + 5u * round) % 63u + 1u) ^
           (x & cw_rol64(y, 11u)) ^ (x + y);
}

void cw_even(uint64_t a[6], unsigned round)
{
    for (unsigned i = 0; i < 6; i += 2)
        a[i] ^= mix(a[(i + 1u) % 6u], a[(i + 5u) % 6u], round, i);
}

void cw_odd(uint64_t a[6], unsigned round)
{
    for (unsigned i = 1; i < 6; i += 2)
        a[i] ^= mix(a[(i + 1u) % 6u], a[(i + 5u) % 6u], round, i);
}

void cw_add_constants(uint64_t a[6], unsigned round)
{
    a[0] ^= cw_rc[round][0];
    a[3] ^= cw_rc[round][1];
}
