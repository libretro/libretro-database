import os
import re

ramOffset = -0xC000

def convert_mcf_to_cht(directory):
    """Convert all BlueMSX .mcf cheat files in a directory into RetroArch .cht files."""
    for filename in os.listdir(directory):
        if not filename.lower().endswith('.mcf'):
            continue
        
        #print(filename)
        input_path = os.path.join(directory, filename)
        output_path = os.path.join(directory, os.path.splitext(filename)[0] + '.cht')
        
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as infile:
            content = infile.read()
        
        inputLines = content.splitlines()
        cheatNumber = 0
        lines = []
        for inputLine in inputLines:
            if inputLine is "":
                continue
            if inputLine[0] == "!":
                continue
            # Some lines are missing the extra 0
            
            try:
                dummy, addr, value , dummy2, description = inputLine.split(',',4)
            except:
                dummy, addr, value , description = inputLine.split(',',3)
                
            description = description.strip()
            addr = addr.strip()
            newaddr = int(addr) + int(ramOffset)
            
            # if value is negative, it is a .dsk game
            # must subtract the (negative) offset, not add
            if newaddr < 0:
                newaddr = int(addr) - int(ramOffset)
                
            value = value.strip()
            
            lines.append(f'cheat{cheatNumber}_desc = "{description}"')
            lines.append(f'cheat{cheatNumber}_address = "{newaddr}"')
            lines.append(f'cheat{cheatNumber}_address_bit_position = "255"')
            lines.append(f'cheat{cheatNumber}_big_endian = "false"')
            lines.append(f'cheat{cheatNumber}_enable = "false"')
            lines.append(f'cheat{cheatNumber}_value = "{value}"')
            lines.append(f'cheat{cheatNumber}_cheat_type = "1"')
            lines.append(f'cheat{cheatNumber}_code = ""')
            lines.append(f'cheat{cheatNumber}_address_bit_position = "0"')
            lines.append(f'cheat{cheatNumber}_handler = "1"')
            lines.append(f'cheat{cheatNumber}_memory_search_size = "3"')
            lines.append(f'cheat{cheatNumber}_rumble_port = "0"')
            lines.append(f'cheat{cheatNumber}_rumble_primary_duration = "0"')
            lines.append(f'cheat{cheatNumber}_rumble_primary_strength = "0"')
            lines.append(f'cheat{cheatNumber}_rumble_secondary_strength = "0"')
            lines.append(f'cheat{cheatNumber}_rumble_type = "0"')
            lines.append(f'cheat{cheatNumber}_rumble_value = "0"')
            
            lines.append("")  # blank line between cheats
            cheatNumber = cheatNumber + 1    
            
        lines.append(f'cheats = "{cheatNumber}"')    
        with open(output_path, 'w', encoding='utf-8') as outfile:
            outfile.write("\n".join(lines))
        
        print(f"✅ Converted {filename} → {os.path.basename(output_path)}")

convert_mcf_to_cht("./")