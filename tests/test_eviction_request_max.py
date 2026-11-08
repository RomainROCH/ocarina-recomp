"""Compile vk_texture_vram_short from the actual source in a standalone C fixture.

Usage: python tests/test_eviction_request_max.py [--cc clang]
No Vulkan SDK, game content or binaries required.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import tempfile


def extract(src: str, signature: str) -> str:
    pos = src.index(signature)
    first = src.index('{', pos)
    depth = 1
    end = first + 1
    while depth:
        if end >= len(src):
            raise ValueError('Unterminated function')
        depth += (src[end] == '{') - (src[end] == '}')
        end += 1
    return src[pos:end]


HARNESS = r'''
#include <stdint.h>
#include <assert.h>
#include <pthread.h>
#include <stdio.h>
#define MIB (UINT64_C(1) << 20)
#define EVICT_MIN_BYTES (64 * MIB)
static uint64_t evict_want;
SOURCE_FUNCTION
static void *request(void *arg) {
    vk_texture_vram_short(*(const uint64_t*)arg);
    return NULL;
}
static uint64_t consume(void) {
    return __atomic_exchange_n(&evict_want, 0, __ATOMIC_RELAXED);
}
int main(void) {
    vk_texture_vram_short(512 * MIB);
    vk_texture_vram_short(64 * MIB);
    assert(consume() == 512 * MIB);
    vk_texture_vram_short(64 * MIB);
    vk_texture_vram_short(512 * MIB);
    assert(consume() == 512 * MIB);
    vk_texture_vram_short(1);
    assert(consume() == 64 * MIB);
    vk_texture_vram_short(384 * MIB);
    vk_texture_vram_short(128 * MIB);
    assert(consume() == 384 * MIB);
    pthread_t threads[8];
    const uint64_t amounts[8] = {72*MIB, 640*MIB, 80*MIB, 96*MIB,
                                 512*MIB, 256*MIB, 1024*MIB, 128*MIB};
    for (int i = 0; i < 8; ++i)
        assert(pthread_create(&threads[i], NULL, request, (void*)&amounts[i]) == 0);
    for (int i = 0; i < 8; ++i)
        assert(pthread_join(threads[i], NULL) == 0);
    assert(consume() == 1024 * MIB);
    vk_texture_vram_short(160 * MIB);
    assert(consume() == 160 * MIB);
    assert(consume() == 0);
    puts("PASS: largest outstanding VRAM shortage survives smaller and parallel requests");
}
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--cc', default='cc')
    args = parser.parse_args()
    src = (Path(__file__).resolve().parents[1] / 'runtime/vk_texture.c').read_text(encoding='utf-8')
    function = extract(src, 'void vk_texture_vram_short(uint64_t bytes)')
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / 'eviction_max.c'
        exe = Path(folder) / 'eviction_max'
        source.write_text(HARNESS.replace('SOURCE_FUNCTION', function), encoding='utf-8')
        subprocess.run([args.cc, '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                        '-pthread', '-fsanitize=undefined', '-fno-sanitize-recover=all',
                        str(source), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)


if __name__ == '__main__':
    main()
