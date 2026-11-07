#!/usr/bin/env python3
"""
Losslessly strips unused C/C++ header files from Android AAR archive.
Pixiv-Shaft consumes ONNX Runtime purely through Kotlin/Java JNI bindings.
C/C++ headers in `headers/` take up ~890 KB uncompressed space and ~164 KB in archive,
and are completely unused in an Android runtime AAR package.

Performs byte-level zero-recompression stripping to keep native ELF compression intact.
"""

import os
import sys
import struct
import zipfile


def strip_headers(aar_path: str):
    if not os.path.exists(aar_path):
        print(f"Error: AAR file not found at {aar_path}", file=sys.stderr)
        sys.exit(1)

    initial_size = os.path.getsize(aar_path)
    print(f"Inspecting AAR: {aar_path} ({initial_size:,} bytes)")

    has_headers = False
    with zipfile.ZipFile(aar_path, "r") as zin:
        for name in zin.namelist():
            if name.startswith("headers/") or name == "headers":
                has_headers = True
                break

    if not has_headers:
        print("No headers/ directory found inside AAR. Nothing to strip.")
        return

    tmp_dst = aar_path + ".tmp_stripped"
    with open(aar_path, "rb") as f_in, open(tmp_dst, "wb") as f_out:
        with zipfile.ZipFile(aar_path, "r") as zin:
            entries = [
                item for item in zin.infolist()
                if not (item.filename.startswith("headers/") or item.filename == "headers")
            ]

        # Copy local file headers and raw compressed data
        new_records = []
        for item in entries:
            f_in.seek(item.header_offset)
            local_hdr = f_in.read(30)
            sig, ver, flag, method, mtime, mdate, crc, comp_size, uncomp_size, name_len, extra_len = struct.unpack(
                "<IHHHHHIIIHH", local_hdr
            )
            name_and_extra = f_in.read(name_len + extra_len)
            comp_data = f_in.read(comp_size)

            new_offset = f_out.tell()
            f_out.write(local_hdr)
            f_out.write(name_and_extra)
            f_out.write(comp_data)
            new_records.append((item, new_offset))

        # Write Central Directory Headers
        cd_offset = f_out.tell()
        for item, new_offset in new_records:
            name_bytes = item.filename.encode("utf-8")
            extra_bytes = item.extra or b""
            comment_bytes = item.comment or b""
            time_field = item.date_time[3] << 11 | item.date_time[4] << 5 | (item.date_time[5] // 2)
            date_field = (item.date_time[0] - 1980) << 9 | item.date_time[1] << 5 | item.date_time[2]
            cd_hdr = struct.pack(
                "<IHHHHHHIIIHHHHHII",
                0x02014B50,
                item.create_version,
                item.extract_version,
                item.flag_bits,
                item.compress_type,
                time_field,
                date_field,
                item.CRC,
                item.compress_size,
                item.file_size,
                len(name_bytes),
                len(extra_bytes),
                len(comment_bytes),
                0,
                item.internal_attr,
                item.external_attr,
                new_offset,
            )
            f_out.write(cd_hdr)
            f_out.write(name_bytes)
            f_out.write(extra_bytes)
            f_out.write(comment_bytes)

        # Write End of Central Directory (EOCD)
        cd_size = f_out.tell() - cd_offset
        eocd = struct.pack(
            "<IHHHHIIH",
            0x06054B50,
            0,
            0,
            len(new_records),
            len(new_records),
            cd_size,
            cd_offset,
            0,
        )
        f_out.write(eocd)

    # Validate output archive integrity
    with zipfile.ZipFile(tmp_dst, "r") as ztest:
        bad_file = ztest.testzip()
        if bad_file:
            os.remove(tmp_dst)
            print(f"Error: Stripped AAR validation failed at {bad_file}!", file=sys.stderr)
            sys.exit(1)

    os.replace(tmp_dst, aar_path)
    final_size = os.path.getsize(aar_path)
    reduction = initial_size - final_size
    print(f"Successfully stripped C/C++ headers without recompression!")
    print(f"Size before: {initial_size:,} bytes")
    print(f"Size after:  {final_size:,} bytes")
    print(f"Net savings: {reduction:,} bytes ({reduction / 1024:.2f} KB)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path-to-aar>")
        sys.exit(1)
    strip_headers(sys.argv[1])
