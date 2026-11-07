#!/usr/bin/env python3
"""
Audit 16 KB Page Alignment (Android 15) for all shared libraries (.so).
"""
import glob
import os
import struct
import sys

def audit_so(path: str) -> int:
    with open(path, "rb") as f:
        data = f.read(64)
        if data[:4] != b"\x7fELF":
            return 0
        e_phoff = struct.unpack("<Q", data[32:40])[0]
        e_phentsize = struct.unpack("<H", data[54:56])[0]
        e_phnum = struct.unpack("<H", data[56:58])[0]
        f.seek(e_phoff)
        max_align = 0
        for _ in range(e_phnum):
            ph = f.read(e_phentsize)
            p_type, _, _, _, _, _, _, p_align = struct.unpack("<IIQQQQQQ", ph[:56])
            # PT_LOAD = 1
            if p_type == 1 and p_align > max_align:
                max_align = p_align
        return max_align

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "./aar_extracted"
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")

    so_files = glob.glob(os.path.join(target_dir, "**", "*.so"), recursive=True)
    if not so_files:
        print(f"Error: No .so files found in {target_dir} to audit!")
        sys.exit(1)

    all_aligned = True
    table_rows = []
    print("\n=== Android 15 (16 KB Page Alignment) Audit ===")
    for path in sorted(so_files):
        norm_path = path.replace("\\", "/")
        max_align = audit_so(path)
        is_ok = max_align >= 0x4000
        if not is_ok:
            all_aligned = False
        status_icon = "✅ 16 KB (0x4000)" if is_ok else "❌ NOT ALIGNED"
        table_rows.append(f"| `{norm_path}` | `0x{max_align:x}` ({max_align} B) | {status_icon} |")
        print(f"[{'PASS' if is_ok else 'FAIL'}] {norm_path}: max PT_LOAD align = 0x{max_align:x} ({max_align} bytes)")

    if summary_path and os.path.exists(os.path.dirname(summary_path) or "."):
        summary_content = (
            "\n### 🛡️ Android 15 (16 KB Page Alignment) Audit\n"
            "| Library | Max PT_LOAD Align | Status |\n"
            "| :--- | :--- | :--- |\n" + "\n".join(table_rows) + "\n"
        )
        try:
            with open(summary_path, "a", encoding="utf-8") as f_sum:
                f_sum.write(summary_content)
        except Exception as e:
            print(f"Warning: Could not write to step summary: {e}")

    if not all_aligned:
        print("\nError: One or more native libraries violate 16 KB page alignment!")
        sys.exit(1)

    print("\nAll native libraries passed 16 KB page alignment audit!")

if __name__ == "__main__":
    main()
