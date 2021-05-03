#!/usr/bin/env python3

# Copyright (C) 2021 David Guillen Fandos

# Parses a CHT file and attempts to decrypt any cheats that might be encrypted
# Will just copy the contents should the cheats be unencrypted.
# This will effectively remove any master cheat if it's only used to encrypt

import sys, re, struct

def ror(v, a):
  return ((v >> a) | (v << (32 - a))) & 0xffffffff

def ishex(s):
  return all(x.upper() in "0123456789ABCDEF" for x in s)

# Generates 32 bits out of the LFSR by combining three step ouputs
def lfsr_advance(state0):
  state1 = (state0 * 0x41C64E6D + 0x3039) & 0xffffffff
  state2 = (state1 * 0x41C64E6D + 0x3039) & 0xffffffff
  state3 = (state2 * 0x41C64E6D + 0x3039) & 0xffffffff
  # Combine the three states into one
  return (((state1 << 14) & 0xC0000000) |
          ((state2 >>  1) & 0x3FFF8000) |
          ((state3 >> 16) & 0x00007FFF), state3)

def next_tblidx(lfsr_state):
  roll, lfsr_state = lfsr_advance(lfsr_state)
  count = 48
  
  if roll == count:
    roll = 0
  
  if roll < count:
    return roll, lfsr_state

  bit = 1

  while count < 0x10000000 and count < roll:
    count = (count << 4) & 0xFFFFFFFF
    bit = (bit << 4) & 0xFFFFFFFF

  while count < 0x80000000 and count < roll:
    count = (count << 1) & 0xFFFFFFFF
    bit = (bit << 1) & 0xFFFFFFFF

  while True:
    mask = 0
    if roll >= count:
      roll -= count
    if roll >= (count >> 1):
      roll -= (count >> 1)
      mask |= ror(bit, 1)
    if roll >= (count >> 2):
      roll -= (count >> 2)
      mask |= ror(bit, 2)
    if roll >= (count >> 3):
      roll -= (count >> 3)
      mask |= ror(bit, 3)
    if roll == 0 or (bit >> 4) == 0:
      break
    bit >>= 4
    count >>= 4

  mask &= 0xE0000000
  if mask == 0 or (bit & 7) == 0:
    return roll, lfsr_state

  if mask & ror(bit, 3):
    roll += (count >> 3)
  if mask & ror(bit, 2):
    roll += (count >> 2)
  if mask & ror(bit, 1):
    roll += (count >> 1)

  return roll, lfsr_state

def decrypt(addr, val, encdata):
  buf = list(struct.pack(">IH", addr, val))
  deckey, tbldata, seeds = encdata

  for i in range(47, -1, -1):
    off1 = i >> 3
    off2 = tbldata[i] >> 3
    bit1 = i & 7
    bit2 = tbldata[i] & 7

    # Extract the indicated bits
    p1 = (buf[off1] >> bit1) & 1
    p2 = (buf[off2] >> bit2) & 1
    # Swap bits, first clear then set if necessary
    buf[off1] &= ~(1 << bit1)
    buf[off2] &= ~(1 << bit2)
    buf[off1] |= (p2 << bit1)
    buf[off2] |= (p1 << bit2)

  # Xor decrypt with the calculated values
  s1 = struct.pack(">IH", seeds[0], seeds[1] & 0xffff)
  buf = [a ^ b for (a, b) in zip(buf, s1)]

  for i in range(5):
    buf[i] ^= (((deckey >> 8) ^ buf[i+1]) & 0xff)
  buf[5] ^= ((deckey >> 8) & 0xff)

  for i in range(5, 0, -1):
    buf[i] ^= ((deckey ^ buf[i-1]) & 0xff)
  buf[0] ^= (deckey & 0xff)

  s2 = struct.pack(">IH", seeds[2], seeds[3] & 0xffff)
  buf = bytes(a ^ b for (a, b) in zip(buf, s2))

  return struct.unpack(">IH", buf)

def calculateSeeds(addr, val):
  tbl = list(range(48))
  rngstate = (val & 0xff) ^ 0x1111
  
  # Performs some table swaps based on the code
  for i in range(80):
    p1, rngstate = next_tblidx(rngstate)
    p2, rngstate = next_tblidx(rngstate)
    tbl[p1], tbl[p2] = tbl[p2], tbl[p1]

  # Reinitialize the RNG now to a fixed value and draw a variable number
  rngstate = 0x4EFAD1C3
  for i in range((addr >> 24) & 15):
    # Yeah this is on purpose, the output wired to the state
    rngstate, _ = lfsr_advance(rngstate)

  seed2, rngstate = lfsr_advance(rngstate)
  seed3, rngstate = lfsr_advance(rngstate)

  # Do it again, super secure stuff :P
  rngstate = (val >> 8) ^ 0xF254
  for i in range(val >> 8):
    # Yeah this is on purpose, the output wired to the state
    rngstate, _ = lfsr_advance(rngstate)

  seed0, rngstate = lfsr_advance(rngstate)
  seed1, rngstate = lfsr_advance(rngstate)

  return (addr, tbl, [seed0, seed1, seed2, seed3])


with open(sys.argv[1]) as ifd:
  vrs = {}
  for line in ifd.read().split("\n"):
    m = re.match("^([^\s=]+)\s*=\s*\"([^\"]+)\"$", line.strip())
    if m:
      vrs[m.group(1)] = m.group(2)
    else:
      m = re.match("^([^\s=]+)\s*=\s*([^\s=]+)$", line.strip())
      if m:
        vrs[m.group(1)] = m.group(2)

assert "cheats" in vrs

outtext = "cheats = %s\n\n" % vrs["cheats"]
encdata = None
for i in range(int(vrs["cheats"])):
  cdesc = vrs["cheat%d_desc" % i]
  ccode = vrs["cheat%d_code" % i].upper()
  cenab = vrs["cheat%d_enable" % i]

  m = ccode.split("+")
  if not all(len(x) == 12 and ishex(x) for x in m):
    m = ccode.split(" ")
    if not all(len(x) == 12 and ishex(x) for x in m):
      m = re.findall("[0-9a-fA-F]{8}[\+ ][0-9a-fA-F]{4}", ccode)
      if not m:
        print("Bad code", ccode)
        sys.exit(1)

  ocodes = []
  for c in m:
    if "+" in c:
      adrs, val = c.split("+")
    elif " " in c:
      adrs, val = c.split(" ")
    else:
      adrs, val = c[:8], c[8:]
    addr, val = int(adrs, 16), int(val, 16)
    if encdata:
      # Decode the data first!
      addr, val = decrypt(addr, val, encdata)
    elif adrs[0] == '9':
      # Update encryption data, next codes must be encrypted
      encdata = calculateSeeds(addr, val)
      #print("Change code", c, encdata)
      continue  # Skip this code since it's now useless

    finalcode = "%08x+%04x" % (addr, val)
    ocodes.append(finalcode)
  # Update code!
  vrs["cheat%d_code" % i] = "+".join(ocodes).upper()

  outtext += 'cheat%d_desc = "%s"\n' % (i, vrs["cheat%d_desc" % i])
  outtext += 'cheat%d_code = "%s"\n' % (i, vrs["cheat%d_code" % i])
  outtext += 'cheat%d_enable = false\n\n' % i

with open(sys.argv[1], "w") as ofd:
  ofd.write(outtext)

