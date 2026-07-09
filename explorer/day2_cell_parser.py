import base64
from pytoniq_core import Cell, begin_cell, Address


SPAM_BODY = "te6cckEBAQEALwAAWgAAAABHZXQgMzAwIHRlc3RuZXQgVE9OIHwgVEc6IEB0ZXN0bmV0X21hcmtldKC5Zfw="

#convert the base64 into raw bytes 
raw = base64.b64decode(SPAM_BODY)
print(len(raw), "bytes")

# print those raw bytes as hexadecimal 
# two hexadecimal characters per byte
print(raw.hex())


#Processing of the raw bytes and what information they give
#body of the message in bytes and its lenght is 62
#b5ee9c7241010101002f00005a000000004765742033303020746573746e657420544f4e207c2054473a2040746573746e65745f6d61726

#Check BAG OF CELLS. Check first 4 bytes
if (raw[0:4].hex()) == "b5ee9c72":
    print("This is a bag of cells")

assert raw[0:4] == bytes.fromhex("b5ee9c72"), "not a BOC"


#Check the byte at position 5
"""
in 01000001 bit 7 is the leftmost bit


bit7 = 0  no index section
bit6 = 1  CRC32 present at tail  
bit5 = 0  no cache bits
bits4-3   unused (00)
bits2-0 = 001  ref width = 1 byte

ref_width means how many bytes does a cell index take. 
"""

target_byte = raw[4]
bit_string = f"{target_byte:08b}"
print(bit_string)
#01000001



#6th byte
#size fields below are 1 byte each in size
print(f"Fields below are of size: {raw[5]} bytes")


#7th byte
#how many cells are there in the bag of cells
print(f"There are {raw[6]} cells in the bag of cells")


#8th byte
#the root count
print(f"The root count is {raw[7]}")

#9th byte 
#raw[8] can ignore as its always 0 for us

#raw[9] the total byte length of the cell records section 
print(f"The total byte length of the cell records section  {raw[9]}")


#raw[10] pointing to the cell index in this case #0 that is the root
print(f"Index of the root {raw[10]}")


"""
The 2 bytes d1 and d2 are the descriptors for the cell content
"""

#raw[11] 12th bit lets call it d1
#d1 & 7   → 0 references (leaf cell)
#d1 & 8 → 0 = ordinary cell
print(f"The d1 descriptor is {raw[11]}")
assert raw[11] & 8 == 0, "exotic cell — SDK territory"


#raw[12] data length in nibble (4 bits)
print(f"The number of nibbles shipped are {raw[12]}")
bytes_shipped = (raw[12] +1) // 2
print(f"Number of bytes shipped {bytes_shipped}")
assert raw[12] % 2 == 0, "odd nibble count — padding rule needed, not implemented"

"""
The padding rule (this is the clever bit): when the content doesn't fill the last byte,
you can't just zero-pad — a decoder couldn't tell trailing data-zeros from pad-zeros.
TON's convention: append a single 1 bit, then 0s to the byte boundary.
"""




"""
opcode is raw[13:17]

It identifies the message type

op = 0x00000000  →  "plain text comment follows"     (your spam)
op = 0x7362d09c  →  "jetton transfer notification"   (standard token protocol)
op = 0xd53276db  →  "excesses" (gas refund)          (another standard)
op = <yours>     →  whatever your contract defines
"""

opcode = raw[13:17]
text = raw[17:58]

print(f"opcode: 0x{opcode.hex()}")
print(f"comment: {text.decode('utf-8')}")



# raw[58:61] crc32 bt checksum
print(f"crc tail: {raw[58:62].hex()}")   # expect a0b965fc




#Another smarter way to do it 
data_start = 13
data_len = (raw[12] + 1) // 2          # 45
opcode = raw[data_start : data_start + 4]
text   = raw[data_start + 4 : data_start + data_len]
crc1    = raw[data_start + data_len : data_start + data_len + 4]
assert data_start + data_len + 4 == len(raw), "byte accounting broken"

print(crc1.hex())




cell = Cell.one_from_boc(SPAM_BODY)


# base64 + magic + header walk      Cell.one_from_boc(...)
# + descriptors + CRC
s = cell.begin_parse()
print(s)
#s is of type slice in pytoniq
print(type(s))


# s.load_uint(32)) : read the next 32 bits i.e. raw[13:17] after the header
# s.load_snake_string() : raw[17:58].decode("utf-8")
print(hex(s.load_uint(32)), s.load_snake_string())


"""
Second example to understand CELL
"""


s = Cell.one_from_boc(SPAM_BODY).begin_parse()

# ── introspection: how much is left? ─────────────────────────
s.remaining_bits          # 360 for your cell (45 bytes * 8)
s.remaining_refs          # 0 — leaf cell

# ── consuming reads (advance the cursor) ─────────────────────
op   = s.load_uint(32)    # unsigned int from next 32 bits  -> 0
                          # widths are arbitrary: load_uint(7) is legal
# s.load_int(32)          # signed (two's complement) — negative rand_seed déjà vu
# s.load_bit()            # single bit -> 0/1 (flags, like the bounce flag)
# s.load_bytes(4)         # next 4 bytes as raw bytes
# s.load_bits(12)         # sub-byte amounts, as a bit-array
txt  = s.load_snake_string()   # rest as UTF-8, following ref-chain if any

# ── peeking (NO cursor advance) ───────────────────────────────
s2 = Cell.one_from_boc(SPAM_BODY).begin_parse()
s2.preload_uint(32)       # look at the opcode without eating it —
                          # classic dispatch move: peek op, decide, then load

# ── skipping ─────────────────────────────────────────────────
s3 = Cell.one_from_boc(SPAM_BODY).begin_parse()
s3.skip_bits(32)          # don't care about the opcode, jump to text
print(s3.load_snake_string())




# BUILD a cell like a withdrawal request body:
body = (begin_cell()
        .store_uint(0x37fb0b18, 32)                      # my opcode
        .store_uint(42, 64)                              # query id
        .store_coins(1_500_000_000)                      # 1.5 TON, var-length!
        .store_address(Address("0QDJqqf9LXrJcywKC7jgHT68ZUSq_gJfHCPii3qg7yPEQ8Is"))
        .end_cell())

# PARSE it back — reads MUST mirror the writes, same order, same widths:
p = body.begin_parse()
print(hex(p.load_uint(32)))    # 0x37fb0b18
print(p.load_uint(64))         # 42
print(p.load_coins())          # 1500000000  (nanotons — NANO habit applies)
print(p.load_address())        # your address (raw form)
print(p.remaining_bits)        # 0 — fully consumed, nothing dangling



#Print the tree when a cell has multiple child cells 
def print_tree(cell, depth=0):
    print("  " * depth + f"cell: {len(cell.bits)} bits, {len(cell.refs)} refs")
    for ref in cell.refs:
        print_tree(ref, depth + 1)

print_tree(Cell.one_from_boc(SPAM_BODY))