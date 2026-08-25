import fs from 'node:fs';
import path from 'node:path';
import { PUBLISHED_AUTHOR_SLUGS } from '../../lib/library';

export function getStaticPaths() {
  const root = path.resolve(process.cwd(), 'tei');
  return fs.readdirSync(root, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && PUBLISHED_AUTHOR_SLUGS.has(entry.name))
    .flatMap((directory) => fs.readdirSync(path.join(root, directory.name), { withFileTypes: true })
      .filter((file) => file.isFile() && /\.(xml|pdf)$/i.test(file.name))
      .map((file) => ({
        params: { file: `${directory.name}/${file.name}` },
        props: { sourcePath: path.join(root, directory.name, file.name) },
      })));
}

export function GET({ props }: { props: { sourcePath: string } }) {
  const isPdf = path.extname(props.sourcePath).toLowerCase() === '.pdf';
  return new Response(fs.readFileSync(props.sourcePath), {
    headers: {
      'Content-Type': isPdf ? 'application/pdf' : 'application/tei+xml; charset=utf-8',
      'Content-Disposition': `attachment; filename="${path.basename(props.sourcePath)}"`,
    },
  });
}
