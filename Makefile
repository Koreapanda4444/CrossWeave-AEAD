CC = cc
AR = ar
PYTHON = python3
BUILD = build
CPPFLAGS += -Iinclude -Isrc
CFLAGS = -O2 -std=c11 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror

.PHONY: all check research sanitize clean
all: $(BUILD)/libcrossweave.a $(BUILD)/util $(BUILD)/stages $(BUILD)/api $(BUILD)/kat $(BUILD)/oracle_driver

$(BUILD):
	mkdir -p $@

$(BUILD)/util: tests/util.c src/crossweave_internal.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $< $(LDFLAGS) -o $@

$(BUILD)/stages: tests/stages.c tests/stage_vectors.h src/crossweave_p384.c src/crossweave_internal.h src/crossweave_constants.h include/crossweave.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) tests/stages.c src/crossweave_p384.c $(LDFLAGS) -o $@

$(BUILD)/crossweave_p384.o: src/crossweave_p384.c src/crossweave_internal.h src/crossweave_constants.h include/crossweave.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

$(BUILD)/libcrossweave.a: $(BUILD)/crossweave_p384.o
	$(AR) rcs $@ $<

$(BUILD)/api: tests/api.c include/crossweave.h $(BUILD)/libcrossweave.a
	$(CC) $(CPPFLAGS) $(CFLAGS) $< $(BUILD)/libcrossweave.a $(LDFLAGS) -o $@

$(BUILD)/kat: tests/kat.c tests/permutation_vectors.h src/crossweave_internal.h $(BUILD)/libcrossweave.a
	$(CC) $(CPPFLAGS) $(CFLAGS) $< $(BUILD)/libcrossweave.a $(LDFLAGS) -o $@

$(BUILD)/oracle_driver: tests/oracle_driver.c include/crossweave.h $(BUILD)/libcrossweave.a
	$(CC) $(CPPFLAGS) $(CFLAGS) $< $(BUILD)/libcrossweave.a $(LDFLAGS) -o $@

check: all
	$(BUILD)/util
	$(BUILD)/stages
	$(BUILD)/api
	$(BUILD)/kat
	$(PYTHON) tests/framing.py
	$(PYTHON) tests/constants.py
	$(PYTHON) tests/vectors.py
	$(PYTHON) tests/differential.py $(BUILD)/oracle_driver

sanitize:
	$(MAKE) BUILD=build-sanitize CFLAGS='-O1 -g -std=c11 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror -fsanitize=address,undefined -fno-omit-frame-pointer' LDFLAGS='-fsanitize=address,undefined' check

research: $(BUILD)/oracle_driver
	$(PYTHON) research/early_gate.py $(BUILD)/oracle_driver --check docs/early_gate.json

clean:
	rm -rf build build-sanitize
