#include "crossweave_internal.h"
#include "stage_vectors.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    for (size_t n = 0; n < sizeof(stage_vectors) / sizeof(stage_vectors[0]); ++n) {
        uint64_t a[6];
        memcpy(a, stage_vectors[n].input, sizeof(a));
        cw_even(a, stage_vectors[n].round);
        assert(memcmp(a, stage_vectors[n].even, sizeof(a)) == 0);
        cw_even(a, stage_vectors[n].round);
        assert(memcmp(a, stage_vectors[n].input, sizeof(a)) == 0);
        cw_even(a, stage_vectors[n].round);
        cw_odd(a, stage_vectors[n].round);
        assert(memcmp(a, stage_vectors[n].odd, sizeof(a)) == 0);
        cw_add_constants(a, stage_vectors[n].round);
        assert(memcmp(a, stage_vectors[n].added, sizeof(a)) == 0);
        cw_shuffle(a);
        assert(memcmp(a, stage_vectors[n].shuffled, sizeof(a)) == 0);
        cw_unshuffle(a);
        assert(memcmp(a, stage_vectors[n].added, sizeof(a)) == 0);
        cw_add_constants(a, stage_vectors[n].round);
        cw_odd(a, stage_vectors[n].round);
        cw_even(a, stage_vectors[n].round);
        assert(memcmp(a, stage_vectors[n].input, sizeof(a)) == 0);
    }
    for (unsigned bit = 0; bit < 384; ++bit) {
        uint64_t a[6] = {0}, original[6];
        a[bit / 64] = UINT64_C(1) << (bit % 64);
        memcpy(original, a, sizeof(a));
        cw_shuffle(a);
        cw_unshuffle(a);
        assert(memcmp(a, original, sizeof(a)) == 0);
        cw_unshuffle(a);
        cw_shuffle(a);
        assert(memcmp(a, original, sizeof(a)) == 0);
    }
    puts("Frozen C intermediate vectors passed");
    return 0;
}
