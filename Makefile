CC = cc
AR = ar
PYTHON = python3
BUILD = build
CPPFLAGS += -Iinclude -Isrc
CFLAGS = -O2 -std=c11 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror

.PHONY: all check sanitize clean
all: $(BUILD)/util

$(BUILD):
	mkdir -p $@

$(BUILD)/util: tests/util.c src/crossweave_internal.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $< $(LDFLAGS) -o $@

check: all
	$(BUILD)/util
	$(PYTHON) tests/framing.py
	$(PYTHON) tests/constants.py

sanitize:
	$(MAKE) BUILD=build-sanitize CFLAGS='-O1 -g -std=c11 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror -fsanitize=address,undefined -fno-omit-frame-pointer' LDFLAGS='-fsanitize=address,undefined' check

clean:
	rm -rf build build-sanitize
