#!/bin/env lua

--[[
MIT License

Copyright 2026 Zoomll

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
]]

-- Written in Lua 5.4
-- Depends on xml2lua (https://github.com/manoelcampos/xml2lua)
-- Tested on OpenSUSE Tumbleweed GNU/Linux

-- Usage: 
--   File (Default): ``./logiqx2cmp.lua -f [xml filename]``
--      Outputs a new file in your working directory or overwrites an existing one.
--   Directory: ``./logiqx2cmp.lua -d [xml folder] [output folder]``
--      Creates the new folder in your working directory with the converted DATs using another folder as input. Will overwrite DATs if they already exist at that path.
-- The new file(s) will automatically be given the correct name.

local xml2lua = require('xml2lua')
local handler = require('xmlhandler.tree')

local args = {}
if arg[1] ~= '-f' and arg[1] ~= '-d' then
    args[1] = '-f'      -- Flag
    args[2] = arg[1]    -- Input
    args[3] = arg[2]    -- Output
else
    args = arg
end

local expectedDoctype = '<!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">'

local function convertDAT(input, output)
    local file, err1 = io.open(input, 'r')
    if err1 then error(err1) end
    local xml = file:read('*a')
    io.close(file)

    if xml:match("^[^\n]*\n([^\n]*)") ~= expectedDoctype then warn("File does not have the correct DOCTYPE") return end

    local localHandler = handler:new()
    local parser = xml2lua.parser(localHandler)
    parser:parse(xml)
    local data = localHandler.root.datafile

    local system = data.header.name:gsub('^.-%s%-%sLost Level Archive%s%-%s', '')

    -- Header
    local cmpString = 'clrmamepro (\n\t'
    cmpString = cmpString .. 'name "' .. system .. '"\n\t'
    cmpString = cmpString .. 'description "' .. system .. '"\n\t'
    cmpString = cmpString .. 'version "' .. os.date("%Y.%m.%d") .. '"\n\t'
    cmpString = cmpString .. 'homepage "https://github.com/libretro/libretro-database"\n\t'
    cmpString = cmpString .. 'comment "DAT ported from ' .. data.header.url .. ' by logiqx2cmp.lua"\n)'

    print('Converting DAT for ' .. system .. ' ...')
    -- Games
    for i, game in ipairs(data.game) do
        cmpString = cmpString .. '\n\n'
        cmpString = cmpString .. 'game (\n\t'
        cmpString = cmpString .. 'name "' .. game._attr.name .. '"\n\t'
        cmpString = cmpString .. 'description "' .. game.description .. '"'
        if game.rom then
            cmpString = cmpString .. '\n\trom ('
            local rom = {}
            if #game.rom > 1 then
                rom = game.rom[1]._attr
            else
                rom = game.rom._attr
            end
            cmpString = cmpString .. ' name "' .. rom.name .. '"'
            cmpString = cmpString .. ' size ' .. rom.size
            cmpString = cmpString .. ' crc ' .. rom.crc
            cmpString = cmpString .. ' md5 ' .. rom.md5
            if rom.sha1 then
                cmpString = cmpString .. ' sha1 ' .. rom.sha1
            end
            cmpString = cmpString .. ' )'
        end
        cmpString = cmpString .. '\n)'
    end

    local outPath = output .. "/" .. system .. '.dat'
    local dat, err2 = io.open(outPath, 'w')
    if err2 then error(err2) end
    dat:write(cmpString)
    dat:close()

    print('Wrote DAT file to `' .. outPath .. '`')
end

if args[1] == '-f' then
    convertDAT(args[2], '.')
else
    os.execute('mkdir -p ' .. args[3])

    for file in io.popen('ls -- ' .. args[2]):lines() do
        if file:find('%.xml') then
            convertDAT(args[2] .. '/' .. file, args[3])
        end
    end
end