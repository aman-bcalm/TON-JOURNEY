import base64
from pytoniq_core import Cell

SPAM_BODY = "te6cckEBAQEALwAAWgAAAABHZXQgMzAwIHRlc3RuZXQgVE9OIHwgVEc6IEB0ZXN0bmV0X21hcmtldKC5Zfw="

def print_tree(cell, depth=0):
    # 1. Create a nice visual tree structure for the console
    indent = "    " * depth
    branch = "└── " if depth > 0 else "Root: "
    
    # 2. Extract the hex representation of the bits
    # (pytoniq's BitArray handles the hex conversion for us)
    try:
        hex_data = cell.bits.to_hex()
    except AttributeError:
        # Fallback just in case you are on an older version of pytoniq
        hex_data = str(cell.bits)

    # 3. The Adjusted Print Statement
    print(f"{indent}{branch}[{len(cell.bits)} bits, {len(cell.refs)} refs] -> Hex: {hex_data}")
    
    # 4. Recursively print all child cells (the branches)
    for ref in cell.refs:
        print_tree(ref, depth + 1)

def main():
    print("Parsing Bag of Cells (BoC) Payload...\n")
    
    # Convert the base64 string into a TON Root Cell
    root_cell = Cell.one_from_boc(SPAM_BODY)
    
    # Pass the Root Cell into our recursive function
    print_tree(root_cell)

# The standard Python entry point
if __name__ == "__main__":
    main()