"""Tests for mwt_fw.py. Run with:  python3 -m unittest discover firmware-tools

These tests do not need any Xiaomi firmware: they use the 24-byte section
headers taken from Darkhorse's published "no limit" firmware files (to pin the
checksum algorithm) and synthetic section bodies for round-trip tests.
"""

import json
import os
import shutil
import struct
import tempfile
import unittest
import zlib

import mwt_fw

# Section headers from seal_0.12.7-nlt_hw3.bin, seal_0.16.8-nlt_hw4.bin and
# seal_0.16.8-nlt_hw5.bin (Mi1S-no_limit-19-04-10.zip).
REAL_HEADERS = [
    "5a000000ca00030007000c00bc40008a5493010003000500",
    "5a000000ef010300030004005018798df5e8010002000500",
    "5a00000028020300030001005f86c5ccf940010001000500",
    "5a0000009e0004000800100066bc8d16c48e010003000500",
    "5a0000000b010400010006006872d3e488f3010002000500",
    "5a0000002a02040001000100b9dc39ceb39b020001000500",
    "5a0000005a00050008001000733753d8c48e010003000500",
    "5a00000069010500010006006872d3e488f3010002000500",
    "5a0000004802050001000100b9dc39ceb39b020001000500",
]
REAL_HEADERS = [bytes.fromhex(h.replace(" ", "")) for h in REAL_HEADERS]


def synthetic_image(hw=4):
    bodies = [bytes(range(256)) * 40, b"\x4c\xfc" * 3001, b"\x7e" * 777]
    types = [3, 2, 1]
    versions = [(16, 8), (6, 1), (1, 1)]
    out = b""
    for index, (body, type_, (minor, patch)) in enumerate(
        zip(bodies, types, versions)
    ):
        out += mwt_fw.build_header(index, hw, minor, patch, body, type_, 5)
        out += body
    return out


class ChecksumTests(unittest.TestCase):
    def test_real_headers_have_24_bytes(self):
        for header in REAL_HEADERS:
            self.assertEqual(len(header), mwt_fw.HEADER_SIZE)

    def test_crc8_matches_every_real_header(self):
        for header in REAL_HEADERS:
            self.assertEqual(mwt_fw.header_crc8(header), header[4],
                             header.hex())

    def test_build_header_reproduces_real_headers(self):
        for header in REAL_HEADERS:
            (_, _, index, hw, patch, minor, crc32, length, type_,
             unknown) = mwt_fw.HEADER.unpack(header)
            # Fake a body with the right CRC/length by patching the result.
            rebuilt = bytearray(
                mwt_fw.build_header(index, hw, minor, patch, b"", type_,
                                    unknown)
            )
            struct.pack_into("<II", rebuilt, 0x0C, crc32, length)
            rebuilt[4] = mwt_fw.header_crc8(rebuilt)
            self.assertEqual(bytes(rebuilt), header)


class ParseTests(unittest.TestCase):
    def test_valid_image_has_no_problems(self):
        sections = mwt_fw.parse(synthetic_image())
        self.assertEqual([s["type"] for s in sections], [3, 2, 1])
        self.assertEqual(mwt_fw.problems(sections), [])

    def test_detects_corrupted_body(self):
        image = bytearray(synthetic_image())
        image[mwt_fw.HEADER_SIZE + 10] ^= 0xFF
        issues = mwt_fw.problems(mwt_fw.parse(bytes(image)))
        self.assertTrue(any("CRC-32" in i for i in issues), issues)

    def test_detects_corrupted_header(self):
        image = bytearray(synthetic_image())
        image[6] ^= 0x01  # hardware revision of section 0
        issues = mwt_fw.problems(mwt_fw.parse(bytes(image)))
        self.assertTrue(any("CRC-8" in i for i in issues), issues)

    def test_rejects_bad_magic(self):
        image = bytearray(synthetic_image())
        image[0] = 0x00
        with self.assertRaises(mwt_fw.FirmwareError):
            mwt_fw.parse(bytes(image))

    def test_rejects_truncated_file(self):
        with self.assertRaises(mwt_fw.FirmwareError):
            mwt_fw.parse(synthetic_image()[:-1])


class RoundTripTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.src = os.path.join(self.tmp, "fw.bin")
        with open(self.src, "wb") as fh:
            fh.write(synthetic_image())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_unpack_then_pack_is_byte_identical(self):
        out_dir = os.path.join(self.tmp, "unpacked")
        out = os.path.join(self.tmp, "repacked.bin")
        self.assertEqual(mwt_fw.main(["unpack", self.src, out_dir]), 0)
        self.assertEqual(mwt_fw.main(["pack", out_dir, out]), 0)
        with open(self.src, "rb") as a, open(out, "rb") as b:
            self.assertEqual(a.read(), b.read())

    def test_edited_section_gets_fresh_checksums(self):
        out_dir = os.path.join(self.tmp, "unpacked")
        out = os.path.join(self.tmp, "edited.bin")
        mwt_fw.main(["unpack", self.src, out_dir])
        with open(os.path.join(out_dir, "manifest.json")) as fh:
            first = json.load(fh)["sections"][0]["file"]
        path = os.path.join(out_dir, first)
        with open(path, "r+b") as fh:
            fh.seek(100)
            fh.write(b"\x00\x01\x02")
        self.assertEqual(mwt_fw.main(["pack", out_dir, out]), 0)
        with open(out, "rb") as fh:
            sections = mwt_fw.parse(fh.read())
        self.assertEqual(mwt_fw.problems(sections), [])
        with open(path, "rb") as fh:
            self.assertEqual(sections[0]["stored_crc32"],
                             zlib.crc32(fh.read()) & 0xFFFFFFFF)

    def test_hw_override_relabels_every_section(self):
        out_dir = os.path.join(self.tmp, "unpacked")
        out = os.path.join(self.tmp, "hw5.bin")
        mwt_fw.main(["unpack", self.src, out_dir])
        self.assertEqual(mwt_fw.main(["pack", out_dir, out, "--hw", "5"]), 0)
        with open(out, "rb") as fh:
            sections = mwt_fw.parse(fh.read())
        self.assertEqual({s["hw"] for s in sections}, {5})
        self.assertEqual(mwt_fw.problems(sections), [])

    def test_unpack_refuses_corrupt_file_without_force(self):
        with open(self.src, "r+b") as fh:
            fh.seek(mwt_fw.HEADER_SIZE + 5)
            fh.write(b"\xAA")
        out_dir = os.path.join(self.tmp, "unpacked")
        self.assertEqual(mwt_fw.main(["unpack", self.src, out_dir]), 1)
        self.assertEqual(
            mwt_fw.main(["unpack", "--force", self.src, out_dir]), 0
        )


if __name__ == "__main__":
    unittest.main()
