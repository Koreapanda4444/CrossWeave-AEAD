#include "crossweave.h"
#include "crossweave_internal.h"
#include "permutation_vectors.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void store(uint8_t a[48], const uint64_t words[6])
{
    for (unsigned i = 0; i < 6; ++i)
        cw_store64(a + 8u * i, words[i]);
}

int main(void)
{
    for (size_t v = 0; v < sizeof(permutation_vectors) / sizeof(permutation_vectors[0]); ++v) {
        uint8_t a[48], expected[48], original[48];
        store(original, permutation_vectors[v].input);
        memcpy(a, original, 48);
        for (unsigned r = 0; r < 16; ++r) {
            assert(crossweave_permute(a, r, 1) == CROSSWEAVE_OK);
            store(expected, permutation_vectors[v].after[r]);
            assert(memcmp(a, expected, 48) == 0);
        }
        for (unsigned r = 16; r > 0; --r) {
            assert(crossweave_permute_inverse(a, r - 1, 1) == CROSSWEAVE_OK);
            store(expected, r == 1 ? permutation_vectors[v].input :
                  permutation_vectors[v].after[r - 2]);
            assert(memcmp(a, expected, 48) == 0);
        }
        memcpy(a, original, 48);
        assert(crossweave_p12(a) == CROSSWEAVE_OK);
        store(expected, permutation_vectors[v].after[11]);
        assert(memcmp(a, expected, 48) == 0);
        assert(crossweave_p12_inverse(a) == CROSSWEAVE_OK);
        assert(memcmp(a, original, 48) == 0);
        assert(crossweave_p16(a) == CROSSWEAVE_OK);
        store(expected, permutation_vectors[v].after[15]);
        assert(memcmp(a, expected, 48) == 0);
        assert(crossweave_p16_inverse(a) == CROSSWEAVE_OK);
        assert(memcmp(a, original, 48) == 0);
    }
    puts("C KAT: P12/P16 and every intermediate round in both directions passed");
    return 0;
}
