# Mi Walkie-Talkie 1S firmware tools

`mwt_fw.py` unpacks, repacks and verifies firmware files for the Xiaomi Mi
Walkie-Talkie 1S (codename "seal"), such as Darkhorse's "no limit" files
`seal_0.16.8-nlt_hw4.bin`. It needs only Python 3.8+; no extra packages.

```bash
python3 mwt_fw.py info   seal_0.16.8-nlt_hw4.bin
python3 mwt_fw.py unpack seal_0.16.8-nlt_hw4.bin unpacked/
python3 mwt_fw.py pack   unpacked/ rebuilt.bin
```

- `info` lists the sections and checks every checksum.
- `unpack` writes each section to its own file, plus `manifest.json` with the
  header fields. It refuses a file whose checksums don't match (`--force`
  overrides).
- `pack` rebuilds a firmware file from an unpacked folder and recomputes every
  checksum, so an edited section produces a valid file. Unpacking and then
  packing an unmodified file gives back a byte-for-byte identical file.
- `pack --hw N` changes the hardware-revision label in every header. **It does
  not convert the firmware between revisions**: the main program differs
  slightly between revisions, so only flash a file built for your radio's
  revision.

The tool doesn't change any firmware contents itself; it only takes files
apart and puts them back together. Flashing a modified file is at your own
risk.

## File format

A firmware file is a series of sections. Each section is a 24-byte
little-endian header followed by the section's contents:

| Offset | Size | Field | Notes |
|---|---|---|---|
| 0x00 | 4 | magic | always `0x0000005A` |
| 0x04 | 1 | header CRC-8 | over the other 23 header bytes (below) |
| 0x05 | 1 | index | section number 0, 1, 2 |
| 0x06 | 2 | hardware revision | 3, 4 or 5 |
| 0x08 | 2 | version patch | version is `0.<minor>.<patch>` |
| 0x0A | 2 | version minor | |
| 0x0C | 4 | contents CRC-32 | standard CRC-32 (as zlib) |
| 0x10 | 4 | contents length | bytes |
| 0x14 | 2 | type | 3 = main program, 2 = Bluetooth, 1 = voice |
| 0x16 | 2 | unknown | 5 in every known file; preserved |

The header CRC-8 uses polynomial `0x31`, reflected input and output, initial
value `0x5A` and no final XOR. It is computed over header bytes `0x00–0x03`
followed by `0x05–0x17`.

When flashing, the phone app also sends a CRC-32 of the whole file, which it
computes itself.

### Sections in the known files

| Type | Contents |
|---|---|
| 3 | Main program for the radio's STM32-type processor (ARM Thumb code, no encryption). Its vector table starts the section; the reset vector points into `0x0800xxxx` flash. It drives the AT1846S radio chip and FM5802N FM tuner, and contains a debug command menu. |
| 2 | Patch firmware for the Broadcom BCM20703A2 Bluetooth chip. |
| 1 | Spoken voice prompts as raw 8-bit audio. |

| File | Sections |
|---|---|
| `seal_0.12.7-nlt_hw3.bin` | main 0.12.7, Bluetooth 0.4.3, voice 0.1.3 |
| `seal_0.16.8-nlt_hw4.bin` | main 0.16.8, Bluetooth 0.6.1, voice 0.1.1 |
| `seal_0.16.8-nlt_hw5.bin` | same as hw4 except 4 bytes of the main program and the hardware revision |

## Tests

```bash
python3 -m unittest discover firmware-tools
```

The tests don't need any firmware files: they check the checksum algorithm
against the real section headers and round-trip made-up firmware.
