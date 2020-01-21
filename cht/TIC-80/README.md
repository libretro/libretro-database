# TIC-80 Cheats

These are cheats available for [TIC-80 games](https://tic.computer/play) when played through RetroArch/libretro.

## Usage

1. Start a game
2. Open up the Quick Menu (F1)
3. Cheats --> Load Cheat File (Replace)
4. Select the cheat related to the game you're playing
5. Toggle the desired cheat ON to enable the cheat

## Development

To create a cheat, you'll use the following format:

`TIC-80/My Game.cht`
```
cheats = 2

cheat0_desc = "First Cheat"
cheat0_code = "0 1"
cheat0_enable = false

cheat1_desc = "Second Cheat"
cheat1_code = "1 58 2 45 3 41"
cheat1_enable = false
```

The `cheat0_code` represents a string of numbers. The first number is the index in [persistent memory](https://github.com/nesbox/TIC-80/wiki/pmem), and the second number is the desired value. This can be multiple pairs of index values.

In the above example, `cheat0_code = "0 1"` would the same as calling `pmem(0, 1)`. For `cheat1_code = "1 58 2 45 3 41"`, that would be the same as calling...

```
pmem(1, 58)
pmem(2, 45)
pmem(3, 41)
```

To find the pmem indexes for game, you'll have to look through the source code to find which pmem index is for what function.
