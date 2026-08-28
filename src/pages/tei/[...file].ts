import fs from 'node:fs';
import path from 'node:path';
import { PUBLISHED_AUTHOR_SLUGS } from '../../lib/library';

export function getStaticPaths() {
  const root = path.resolve(process.cwd(), 'tei');
  return fs.readdirSync(root, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && PUBLISHED_AUTHOR_SLUGS.has(entry.name))
    .flatMap((directory) => findPublishedFiles(path.join(root, directory.name))
      .map((sourcePath) => ({
        params: { file: path.relative(root, sourcePath).split(path.sep).join('/') },
        props: { sourcePath },
      })));
}

export function GET({ props }: { props: { sourcePath: string } }) {
  const extension = path.extname(props.sourcePath).toLowerCase();
  const contentTypes: Record<string, string> = {
    '.xml': 'application/tei+xml; charset=utf-8',
    '.pdf': 'application/pdf',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
  };
  const isImage = ['.png', '.jpg', '.jpeg', '.gif', '.svg'].includes(extension);
  return new Response(fs.readFileSync(props.sourcePath), {
    headers: {
      'Content-Type': contentTypes[extension] ?? 'application/octet-stream',
      'Content-Disposition': `${isImage ? 'inline' : 'attachment'}; filename="${path.basename(props.sourcePath)}"`,
    },
  });
}

function findPublishedFiles(root: string): string[] {
  return fs.readdirSync(root, { withFileTypes: true }).flatMap((entry) => {
    const target = path.join(root, entry.name);
    if (entry.isDirectory()) return findPublishedFiles(target);
    return entry.isFile() && /\.(xml|pdf|png|jpe?g|gif|svg)$/i.test(entry.name) ? [target] : [];
  });
}
