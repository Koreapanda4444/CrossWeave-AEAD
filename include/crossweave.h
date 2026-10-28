#ifndef CROSSWEAVE_H
#define CROSSWEAVE_H

#include <stddef.h>
#include <stdint.h>

#define CROSSWEAVE_STATE_BYTES 48u
#define CROSSWEAVE_RATE_BYTES 16u
#define CROSSWEAVE_CAPACITY_BYTES 32u
#define CROSSWEAVE_KEY_BYTES 16u
#define CROSSWEAVE_NONCE_BYTES 16u
#define CROSSWEAVE_TAG_BYTES 16u
#define CROSSWEAVE_MAX_INPUT_BYTES ((size_t)16777216)

enum crossweave_status {
    CROSSWEAVE_OK = 0,
    CROSSWEAVE_ERR_INPUT = -1,
    CROSSWEAVE_ERR_AUTH = -2,
    CROSSWEAVE_ERR_MEMORY = -3
};

#ifdef __cplusplus
extern "C" {
#endif

/* In-place 48-byte LE state, with no alignment requirement. NULL is invalid.
 * first_round <= 16, round_count <= 16-first_round; zero rounds is identity.
 * Invalid arguments return ERR_INPUT without changing a non-NULL state.
 * These public, unkeyed functions do not provide AEAD encryption. */
int crossweave_permute(uint8_t *state, unsigned first_round, unsigned round_count);
int crossweave_permute_inverse(uint8_t *state, unsigned first_round,
                              unsigned round_count);
int crossweave_p12(uint8_t *state);
int crossweave_p16(uint8_t *state);
int crossweave_p12_inverse(uint8_t *state);
int crossweave_p16_inverse(uint8_t *state);

#ifdef __cplusplus
}
#endif

#endif
