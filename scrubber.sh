#!/bin/bash


find . -depth -name "*[<>*?|\":']*" |     # Find all files or folders containing 'bad' characters.
while read FILEDIR                            # Read them line-by-line.
do
        DIR="${FILEDIR%/*}"                   # Get the folder its inside
        FILE="${FILEDIR/*\/}"                 # Get the plain name.
        NEWFILE="${FILE//[<>*?|\":\']/}" # Substitute _ for bad things.
        mv "$DIR/$FILE" "$DIR/$NEWFILE"  # Rename it.
done
