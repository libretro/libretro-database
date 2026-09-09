import { parse } from "@retrobrainz/dat";
import chalk from "chalk";
import { glob, readFile } from "node:fs/promises";

for await (const datFile of glob(["dat/**/*.dat", "metadat/**/*.dat"], { exclude: ["dat/DOS.dat"] })) {
  console.log(datFile);
  const datContent = await readFile(datFile, "utf8");
  const dat = parse(datContent);
  const crcSerialMap = {};
  for (const game of dat) {
    if (
      game.$class !== "game" ||
      game.$entries?.length !== 1 ||
      game.$entries?.[0].$class !== "rom"
    ) {
      continue;
    }
    const crc = game.$entries?.[0].crc;
    const serial = game.$entries?.[0].serial || game.serial;
    // if both crc and serial are the same, mark as duplicate
    const key = JSON.stringify({crc, serial});
    crcSerialMap[key] = (crcSerialMap[key] || 0) + 1;
  }
  for (const [key, count] of Object.entries(crcSerialMap)) {
    if (count > 1) {
      const {crc, serial} = JSON.parse(key);
      console.log(chalk.red(`    duplicate: crc(${crc}), serial(${serial}), count(${count})`));
    }
  }
}
