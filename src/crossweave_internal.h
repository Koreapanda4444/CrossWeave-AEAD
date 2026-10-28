#ifndef CROSSWEAVE_INTERNAL_H
#define CROSSWEAVE_INTERNAL_H

#include <limits.h>
#include <stdint.h>

_Static_assert(CHAR_BIT == 8, "CrossWeave requires 8-bit bytes");
_Static_assert(sizeof(uint64_t) == 8, "CrossWeave requires uint64_t");

/* Internal lane operations require six lanes and a round in 0..15. */
void cw_even(uint64_t a[6], unsigned round);

static inline uint64_t cw_load64(const uint8_t *p)
{
    uint64_t x = 0;
    for (unsigned i = 0; i < 8; ++i)
        x |= (uint64_t)p[i] << (8u * i);
    return x;
}

static inline void cw_store64(uint8_t *p, uint64_t x)
{
    for (unsigned i = 0; i < 8; ++i)
        p[i] = (uint8_t)(x >> (8u * i));
}

static inline uint64_t cw_rol64(uint64_t x, unsigned n)
{
    n &= 63u;
    return (x << n) | (x >> ((64u - n) & 63u));
}

static inline uint64_t cw_ror64(uint64_t x, unsigned n)
{
    n &= 63u;
    return (x >> n) | (x << ((64u - n) & 63u));
}

#endif
