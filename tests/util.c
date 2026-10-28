#include "crossweave_internal.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>

int main(void)
{
    uint8_t unaligned[10] = {0xee, 0xef, 0xcd, 0xab, 0x89,
                            0x67, 0x45, 0x23, 0x01, 0xdd};
    uint8_t out[10] = {0};
    const uint64_t word = UINT64_C(0x0123456789abcdef);
    assert(cw_load64(unaligned + 1) == word);
    cw_store64(out + 1, word);
    assert(memcmp(out + 1, unaligned + 1, 8) == 0);
    assert(out[0] == 0 && out[9] == 0);
    assert(cw_rol64(word, 8) == UINT64_C(0x23456789abcdef01));
    assert(cw_ror64(word, 8) == UINT64_C(0xef0123456789abcd));
    for (unsigned bit = 0; bit < 64; ++bit) {
        uint64_t x = UINT64_C(1) << bit;
        for (unsigned n = 0; n <= 256; ++n) {
            assert(cw_rol64(x, n) == (UINT64_C(1) << ((bit + n) % 64)));
            assert(cw_ror64(cw_rol64(x, n), n) == x);
            assert(cw_rol64(cw_ror64(x, n), n) == x);
        }
    }
    assert(cw_rol64(word, UINT_MAX) == cw_rol64(word, 63));
    assert(cw_ror64(word, UINT_MAX) == cw_ror64(word, 63));
    puts("C11 unaligned LE and rotation checks passed");
    return 0;
}
