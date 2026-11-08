#pragma once

// Pipeline-key seeds may have been recorded on a mesh-capable GPU. Do not
// attempt to prebuild task/mesh stages on a device without VK_EXT_mesh_shader.
static inline int vk_prewarm_skip_unsupported_mesh(int has_mesh_shader, int is_mesh, int has_task) {
    return !has_mesh_shader && (is_mesh || has_task);
}
