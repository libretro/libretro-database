import { parse } from "@retrobrainz/dat";
import chalk from "chalk";
import { glob, readFile } from "node:fs/promises";

for await (const datFile of glob("**/*.dat")) {
  console.log(datFile);
  const datContent = await readFile(datFile, "utf8");
  const dat = parse(datContent);
  const crcMap = {};
  const serialMap = {};
  for (const game of dat) {
    if (game.$class !== "game" || game.$entries?.length !== 1) {
      continue;
    }
    const crc = game.$entries?.[0].crc;
    const serial = game.$entries?.[0].serial;
    if (crc) {
      crcMap[crc] = (crcMap[crc] || 0) + 1;
    }
    if (serial) {
      serialMap[serial] = (serialMap[serial] || 0) + 1;
    }
  }
  for (const [crc, count] of Object.entries(crcMap)) {
    if (count > 1) {
      console.log(chalk.red(`    duplicate crc: ${crc} (${count})`));
    }
  }
  for (const [serial, count] of Object.entries(serialMap)) {
    if (count > 1) {
      console.log(chalk.red(`    duplicate serial: ${serial} (${count})`));
    }
  }
}
