#!/usr/bin/env python3
"""Pack, unpack and verify Xiaomi Mi Walkie-Talkie 1S ("seal") firmware files.

A firmware file (e.g. ``seal_0.16.8-nlt_hw4.bin``) is a plain concatenation of
sections. Each section is a 24-byte little-endian header followed by its body:

    offset size  field
    0x00   4     magic        always 0x0000005A
    0x04   1     header_crc8  CRC-8 over the other 23 header bytes (see below)
    0x05   1     index        section number: 0, 1, 2, ...
    0x06   2     hw           hardware revision the file is built for (3, 4, 5)
    0x08   2     ver_patch    version is "0.<ver_minor>.<ver_patch>"
    0x0A   2     ver_minor
    0x0C   4     body_crc32   standard CRC-32 (zlib) of the body
    0x10   4     body_len     body length in bytes
    0x14   2     type         3 = main MCU program (STM32, ARM Thumb)
                              2 = Bluetooth chip patch (Broadcom BCM20703A2)
                              1 = voice prompts (8-bit audio)
    0x16   2     unknown      always 5 in known files; preserved as-is

header_crc8 is CRC-8 with polynomial 0x31, reflected input/output, initial
value 0x5A and no final XOR (the Dallas/Maxim CRC-8 with a different init),
computed over header bytes 0x00-0x03 followed by 0x05-0x17.

When flashing, the phone app additionally sends a CRC-32 of the whole file,
which it computes itself, so nothing else needs fixing after a repack.

Commands:
    info   FILE              show sections and check every checksum
    unpack FILE DIR          write each section body plus manifest.json to DIR
    pack   DIR OUT [--hw N]  rebuild a firmware file from an unpacked DIR,
                             recomputing all checksums

No third-party dependencies; Python 3.8+.
"""

import argparse
import json
import os
import struct
import sys
import zlib

MAGIC = 0x5A
HEADER = struct.Struct("<IBBHHHIIHH")
HEADER_SIZE = HEADER.size  # 24
assert HEADER_SIZE == 0x18

TYPE_NAMES = {3: "mcu", 2: "bluetooth", 1: "voice"}
TYPE_DESCRIPTIONS = {
    3: "main MCU program (STM32, ARM Thumb)",
    2: "Bluetooth chip patch (Broadcom BCM20703A2)",
    1: "voice prompts (8-bit audio)",
}


class FirmwareError(Exception):
    pass


def _reflect8(value):
    result = 0
    for _ in range(8):
        result = (result << 1) | (value & 1)
        value >>= 1
    return result


def _crc8_table():
    # Reflected (LSB-first) form of polynomial 0x31 is 0x8C.
    table = []
    for byte in range(256):
        crc = byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8C if crc & 1 else crc >> 1
        table.append(crc)
    return table


_CRC8_TABLE = _crc8_table()
_CRC8_INIT = _reflect8(0x5A)  # init 0x5A expressed in the reflected domain


def crc8(data):
    """CRC-8, poly 0x31, refin/refout, init 0x5A, xorout 0."""
    crc = _CRC8_INIT
    for byte in data:
        crc = _CRC8_TABLE[crc ^ byte]
    return crc


def header_crc8(header):
    """Checksum stored at header byte 0x04, computed over the other 23 bytes."""
    if len(header) != HEADER_SIZE:
        raise ValueError("header must be %d bytes" % HEADER_SIZE)
    return crc8(bytes(header[0:4]) + bytes(header[5:HEADER_SIZE]))


def build_header(index, hw, ver_minor, ver_patch, body, type_, unknown):
    raw = bytearray(
        HEADER.pack(
            MAGIC,
            0,
            index,
            hw,
            ver_patch,
            ver_minor,
            zlib.crc32(body) & 0xFFFFFFFF,
            len(body),
            type_,
            unknown,
        )
    )
    raw[4] = header_crc8(raw)
    return bytes(raw)


def parse(data):
    """Split a firmware image into sections, returning a list of dicts.

    Each dict holds the decoded header fields, the body bytes and the result of
    every checksum check. Raises FirmwareError if the layout is not recognised.
    """
    sections = []
    offset = 0
    while offset < len(data):
        if len(data) - offset < HEADER_SIZE:
            raise FirmwareError(
                "truncated section header at offset 0x%X" % offset
            )
        header = data[offset : offset + HEADER_SIZE]
        (
            magic,
            stored_crc8,
            index,
            hw,
            ver_patch,
            ver_minor,
            stored_crc32,
            body_len,
            type_,
            unknown,
        ) = HEADER.unpack(header)
        if magic != MAGIC:
            raise FirmwareError(
                "bad magic 0x%08X at offset 0x%X (expected 0x%08X)"
                % (magic, offset, MAGIC)
            )
        body_start = offset + HEADER_SIZE
        body_end = body_start + body_len
        if body_end > len(data):
            raise FirmwareError(
                "section %d at offset 0x%X claims %d bytes but only %d remain"
                % (index, offset, body_len, len(data) - body_start)
            )
        body = data[body_start:body_end]
        sections.append(
            {
                "offset": offset,
                "index": index,
                "hw": hw,
                "ver_minor": ver_minor,
                "ver_patch": ver_patch,
                "type": type_,
                "unknown": unknown,
                "body_len": body_len,
                "stored_crc8": stored_crc8,
                "computed_crc8": header_crc8(header),
                "stored_crc32": stored_crc32,
                "computed_crc32": zlib.crc32(body) & 0xFFFFFFFF,
                "body": body,
            }
        )
        offset = body_end
    if not sections:
        raise FirmwareError("file is empty")
    return sections


def problems(sections):
    """Return a list of human-readable consistency problems (empty if OK)."""
    issues = []
    for position, s in enumerate(sections):
        name = "section %d" % s["index"]
        if s["stored_crc8"] != s["computed_crc8"]:
            issues.append(
                "%s: header CRC-8 is 0x%02X, expected 0x%02X"
                % (name, s["stored_crc8"], s["computed_crc8"])
            )
        if s["stored_crc32"] != s["computed_crc32"]:
            issues.append(
                "%s: body CRC-32 is 0x%08X, expected 0x%08X"
                % (name, s["stored_crc32"], s["computed_crc32"])
            )
        if s["index"] != position:
            issues.append(
                "%s is stored at position %d" % (name, position)
            )
    hws = {s["hw"] for s in sections}
    if len(hws) > 1:
        issues.append(
            "sections disagree on hardware revision: %s"
            % ", ".join(str(h) for h in sorted(hws))
        )
    return issues


def _version(s):
    return "0.%d.%d" % (s["ver_minor"], s["ver_patch"])


def cmd_info(args):
    data = _read(args.file)
    sections = parse(data)
    print("%s: %d bytes, %d sections" % (args.file, len(data), len(sections)))
    for s in sections:
        print(
            "  [%d] @0x%06X  type %d %-9s  hw%d  v%-8s  %7d bytes  "
            "crc8 %02X %s  crc32 %08X %s"
            % (
                s["index"],
                s["offset"],
                s["type"],
                TYPE_NAMES.get(s["type"], "?"),
                s["hw"],
                _version(s),
                s["body_len"],
                s["stored_crc8"],
                "ok" if s["stored_crc8"] == s["computed_crc8"] else "BAD",
                s["stored_crc32"],
                "ok" if s["stored_crc32"] == s["computed_crc32"] else "BAD",
            )
        )
    issues = problems(sections)
    for issue in issues:
        print("  PROBLEM: " + issue)
    if issues:
        return 1
    print("  all checksums valid")
    return 0


def cmd_unpack(args):
    data = _read(args.file)
    sections = parse(data)
    issues = problems(sections)
    if issues and not args.force:
        for issue in issues:
            print("PROBLEM: " + issue, file=sys.stderr)
        print("refusing to unpack an inconsistent file (use --force)",
              file=sys.stderr)
        return 1
    os.makedirs(args.dir, exist_ok=True)
    manifest = {
        "format": "mi-walkie-talkie-1s-firmware",
        "format_version": 1,
        "source_file": os.path.basename(args.file),
        "source_size": len(data),
        "source_crc32": "%08X" % (zlib.crc32(data) & 0xFFFFFFFF),
        "sections": [],
    }
    for s in sections:
        name = "%d_%s_v%s.bin" % (
            s["index"],
            TYPE_NAMES.get(s["type"], "type%d" % s["type"]),
            _version(s),
        )
        with open(os.path.join(args.dir, name), "wb") as fh:
            fh.write(s["body"])
        manifest["sections"].append(
            {
                "file": name,
                "index": s["index"],
                "type": s["type"],
                "description": TYPE_DESCRIPTIONS.get(s["type"], "unknown"),
                "hw": s["hw"],
                "version": _version(s),
                "unknown": s["unknown"],
                "body_len": s["body_len"],
                "body_crc32": "%08X" % s["stored_crc32"],
            }
        )
    with open(os.path.join(args.dir, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")
    print("unpacked %d sections from %s into %s"
          % (len(sections), args.file, args.dir))
    return 0


def _parse_version(text):
    parts = text.split(".")
    if len(parts) != 3 or parts[0] != "0":
        raise FirmwareError(
            "version %r must look like 0.<minor>.<patch>" % text
        )
    return int(parts[1]), int(parts[2])


def pack_directory(directory, hw=None):
    """Rebuild a firmware image from an unpacked directory; returns bytes."""
    with open(os.path.join(directory, "manifest.json")) as fh:
        manifest = json.load(fh)
    if manifest.get("format") != "mi-walkie-talkie-1s-firmware":
        raise FirmwareError("manifest.json is not a firmware manifest")
    out = bytearray()
    for position, entry in enumerate(manifest["sections"]):
        with open(os.path.join(directory, entry["file"]), "rb") as fh:
            body = fh.read()
        ver_minor, ver_patch = _parse_version(entry["version"])
        out += build_header(
            index=position,
            hw=entry["hw"] if hw is None else hw,
            ver_minor=ver_minor,
            ver_patch=ver_patch,
            body=body,
            type_=entry["type"],
            unknown=entry.get("unknown", 5),
        )
        out += body
    return bytes(out)


def cmd_pack(args):
    image = pack_directory(args.dir, args.hw)
    issues = problems(parse(image))
    if issues:  # should be impossible; guards against bugs in this tool
        for issue in issues:
            print("PROBLEM: " + issue, file=sys.stderr)
        return 1
    with open(args.out, "wb") as fh:
        fh.write(image)
    print("packed %s: %d bytes, crc32 %08X"
          % (args.out, len(image), zlib.crc32(image) & 0xFFFFFFFF))
    return 0


def _read(path):
    with open(path, "rb") as fh:
        return fh.read()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Pack, unpack and verify Mi Walkie-Talkie 1S firmware."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("info", help="show sections and verify checksums")
    p.add_argument("file")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("unpack", help="split a firmware file into sections")
    p.add_argument("file")
    p.add_argument("dir")
    p.add_argument("--force", action="store_true",
                   help="unpack even if checksums are wrong")
    p.set_defaults(func=cmd_unpack)

    p = sub.add_parser("pack", help="rebuild a firmware file")
    p.add_argument("dir")
    p.add_argument("out")
    p.add_argument("--hw", type=int,
                   help="override the hardware revision in every header")
    p.set_defaults(func=cmd_pack)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FirmwareError, OSError, ValueError, KeyError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
