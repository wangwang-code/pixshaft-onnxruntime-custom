#!/usr/bin/env python3
"""
Patch script for ONNX Runtime source tree before Android AAR compilation.
- Injects -D__ONNX_NO_DOC_STRINGS into vcpkg triplet and ONNX build configs
  to eliminate ~322 KB of unused English operator docstrings.
- Injects -fno-asynchronous-unwind-tables into vcpkg CXX flags
  to strip bloated unwind tables from protobuf, re2, and other static dependencies.
"""

import os
import sys

def patch_vcpkg_helpers(ort_root: str):
    vcpkg_helpers_path = os.path.join(ort_root, "tools", "python", "util", "vcpkg_helpers.py")
    if not os.path.isfile(vcpkg_helpers_path):
        print(f"[WARN] {vcpkg_helpers_path} not found, skipping vcpkg_helpers patch.")
        return False

    with open(vcpkg_helpers_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Inject release flags for vcpkg ports: -fno-asynchronous-unwind-tables and -D__ONNX_NO_DOC_STRINGS
    target1 = 'cflags_release = ["-DNDEBUG", "-O3"]'
    replacement1 = 'cflags_release = ["-DNDEBUG", "-O3", "-fno-asynchronous-unwind-tables", "-D__ONNX_NO_DOC_STRINGS"]'
    if target1 in content:
        content = content.replace(target1, replacement1)
        print("[PATCH] Successfully injected unwind tables & docstring flags into vcpkg cflags_release.")
    else:
        print("[INFO] target1 not found or already patched in vcpkg_helpers.py")

    # 2. Inject ONNX-specific flags into triplet
    target2 = '"-DONNX_DISABLE_STATIC_REGISTRATION=ON"'
    replacement2 = '"-DONNX_DISABLE_STATIC_REGISTRATION=ON",\n        "-D__ONNX_NO_DOC_STRINGS=ON"\n    )\n    f.write(r"""    string(APPEND VCPKG_CXX_FLAGS " -D__ONNX_NO_DOC_STRINGS")'
    if target2 in content and '__ONNX_NO_DOC_STRINGS' not in content:
        content = content.replace(target2, replacement2, 1)
        print("[PATCH] Successfully injected -D__ONNX_NO_DOC_STRINGS into ONNX port triplet config.")
    else:
        print("[INFO] target2 already patched or not found.")

    with open(vcpkg_helpers_path, "w", encoding="utf-8") as f:
        f.write(content)

    return True

def patch_cmake_deps(ort_root: str):
    cmake_deps_path = os.path.join(ort_root, "cmake", "external", "onnxruntime_external_deps.cmake")
    if not os.path.isfile(cmake_deps_path):
        print(f"[WARN] {cmake_deps_path} not found, skipping cmake_deps patch.")
        return False

    with open(cmake_deps_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Ensure add_compile_definitions("__ONNX_NO_DOC_STRINGS") is present globally in external deps
    global_def = 'add_compile_definitions("__ONNX_NO_DOC_STRINGS")\n'
    if '__ONNX_NO_DOC_STRINGS' not in content:
        content = global_def + content
        with open(cmake_deps_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("[PATCH] Injected global __ONNX_NO_DOC_STRINGS definition into onnxruntime_external_deps.cmake.")
    else:
        print("[INFO] __ONNX_NO_DOC_STRINGS already present in onnxruntime_external_deps.cmake.")

    return True

def main():
    ort_root = sys.argv[1] if len(sys.argv) > 1 else "onnxruntime"
    print(f"Applying build optimizations patch to ORT source at: {ort_root}")
    patch_vcpkg_helpers(ort_root)
    patch_cmake_deps(ort_root)
    print("Patching complete.")

if __name__ == "__main__":
    main()
