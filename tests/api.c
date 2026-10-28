#include "crossweave.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>

static uint64_t rng = UINT64_C(0x63726f7373776561);
static uint64_t next_word(void)
{
    uint64_t z = (rng += UINT64_C(0x9e3779b97f4a7c15));
    z = (z ^ (z >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
    z = (z ^ (z >> 27)) * UINT64_C(0x94d049bb133111eb);
    return z ^ (z >> 31);
}

int main(void)
{
    const unsigned bad[][2] = {{17, 0}, {0, 17}, {16, 1}, {UINT_MAX, 0},
                              {0, UINT_MAX}, {1, UINT_MAX}, {UINT_MAX, UINT_MAX}};
    uint8_t original[50], a[50], b[50];
    assert(crossweave_p12(NULL) == CROSSWEAVE_ERR_INPUT);
    assert(crossweave_p16(NULL) == CROSSWEAVE_ERR_INPUT);
    assert(crossweave_p12_inverse(NULL) == CROSSWEAVE_ERR_INPUT);
    assert(crossweave_p16_inverse(NULL) == CROSSWEAVE_ERR_INPUT);
    for (unsigned sample = 0; sample < 64; ++sample) {
        memset(original, 0xa5, sizeof(original));
        for (unsigned i = 1; i <= 48; ++i)
            original[i] = (uint8_t)next_word();
        for (size_t i = 0; i < sizeof(bad) / sizeof(bad[0]); ++i) {
            memcpy(a, original, sizeof(a));
            assert(crossweave_permute(a + 1, bad[i][0], bad[i][1]) == CROSSWEAVE_ERR_INPUT);
            assert(memcmp(a, original, sizeof(a)) == 0);
            assert(crossweave_permute_inverse(a + 1, bad[i][0], bad[i][1]) == CROSSWEAVE_ERR_INPUT);
            assert(memcmp(a, original, sizeof(a)) == 0);
        }
        for (unsigned first = 0; first <= 16; ++first) {
            for (unsigned count = 0; count <= 16 - first; ++count) {
                assert(crossweave_permute(NULL, first, count) == CROSSWEAVE_ERR_INPUT);
                assert(crossweave_permute_inverse(NULL, first, count) == CROSSWEAVE_ERR_INPUT);
                memcpy(a, original, sizeof(a));
                assert(crossweave_permute(a + 1, first, count) == CROSSWEAVE_OK);
                assert(a[0] == 0xa5 && a[49] == 0xa5);
                if (count == 0)
                    assert(memcmp(a, original, sizeof(a)) == 0);
                assert(crossweave_permute_inverse(a + 1, first, count) == CROSSWEAVE_OK);
                assert(memcmp(a, original, sizeof(a)) == 0);
                assert(crossweave_permute_inverse(a + 1, first, count) == CROSSWEAVE_OK);
                assert(crossweave_permute(a + 1, first, count) == CROSSWEAVE_OK);
                assert(memcmp(a, original, sizeof(a)) == 0);
            }
        }
        memcpy(a, original, sizeof(a));
        memcpy(b, original, sizeof(b));
        assert(crossweave_p12(a + 1) == CROSSWEAVE_OK);
        assert(crossweave_permute(b + 1, 0, 12) == CROSSWEAVE_OK);
        assert(memcmp(a, b, sizeof(a)) == 0);
        assert(crossweave_p12_inverse(a + 1) == CROSSWEAVE_OK);
        assert(memcmp(a, original, sizeof(a)) == 0);
        memcpy(b, original, sizeof(b));
        assert(crossweave_p16(a + 1) == CROSSWEAVE_OK);
        assert(crossweave_permute(b + 1, 0, 16) == CROSSWEAVE_OK);
        assert(memcmp(a, b, sizeof(a)) == 0);
        assert(crossweave_p16_inverse(a + 1) == CROSSWEAVE_OK);
        assert(memcmp(a, original, sizeof(a)) == 0);
    }
    puts("API: 64 states x all 153 round intervals, inverse and error atomicity passed");
    return 0;
}
