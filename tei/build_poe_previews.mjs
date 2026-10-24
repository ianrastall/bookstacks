// Explicit offline encoding of sidebar-sized derivatives; never a site-build step.
// Sharp is supplied by the repository's locked Astro installation.
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const root = new URL('./poe/', import.meta.url);
const manifest = new URL('illustrations.json', root);
const plates = JSON.parse(await fs.readFile(manifest, 'utf8'));
for (const plate of plates) {
  const file = plate.file.replace(/\.png$/, '.jpg');
  const output = new URL(file, root);
  const info = await sharp(await fs.readFile(new URL(plate.file, root)))
    .resize({ width: 640, withoutEnlargement: true })
    .jpeg({ quality: 92, mozjpeg: true })
    .toFile(fileURLToPath(output));
  const data = await fs.readFile(output);
  plate.preview = { file, width: info.width, height: info.height,
    sha256: crypto.createHash('sha256').update(data).digest('hex') };
}
await fs.writeFile(manifest, JSON.stringify(plates, null, 2) + '\n');
console.log(`Encoded ${plates.length} sidebar previews; original PNGs preserved.`);
