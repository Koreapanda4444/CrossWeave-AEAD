#include "crossweave.h"
#include <stdio.h>

int main(void)
{
    uint8_t record[51];
    size_t n;
    while ((n = fread(record, 1, sizeof(record), stdin)) == sizeof(record)) {
        if (record[2] > 1)
            return 1;
        int rc = record[2] ? crossweave_permute_inverse(record + 3, record[0], record[1]) :
                            crossweave_permute(record + 3, record[0], record[1]);
        if (rc != CROSSWEAVE_OK || fwrite(record + 3, 1, 48, stdout) != 48)
            return 1;
    }
    return n != 0 || ferror(stdin) || fflush(stdout) == EOF;
}
