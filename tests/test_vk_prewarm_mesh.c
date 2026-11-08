// Standalone game-free check: cc -std=c11 -Wall -Wextra -Werror -pedantic tests/test_vk_prewarm_mesh.c -o test_vk_prewarm_mesh
#include <assert.h>
#include "../runtime/vk_prewarm_compat.h"

int main(void) {
    for (int supported = 0; supported <= 1; ++supported) {
        for (int mesh = 0; mesh <= 1; ++mesh) {
            for (int task = 0; task <= 1; ++task) {
                const int expected_skip = !supported && (mesh || task);
                assert(vk_prewarm_skip_unsupported_mesh(supported, mesh, task) == expected_skip);
            }
        }
    }
    return 0;
}
