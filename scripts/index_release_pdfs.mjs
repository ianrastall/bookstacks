#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';

const repository = process.env.GITHUB_REPOSITORY || 'ianrastall/bookstacks';
const apiRoot = (process.env.GITHUB_API_URL || 'https://api.github.com').replace(/\/+$/, '');
const outputPath = path.resolve(process.cwd(), 'tmp', 'release-pdfs.json');
const headers = {
  Accept: 'application/vnd.github+json',
  'User-Agent': 'bookstacks-release-indexer',
  'X-GitHub-Api-Version': '2022-11-28',
};

if (process.env.GITHUB_TOKEN) headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;

async function getJson(url) {
  const response = await fetch(url, { headers });
  if (!response.ok) throw new Error(`GitHub API returned ${response.status} for ${url}`);
  return response.json();
}

async function getAllPages(pathname) {
  const values = [];
  for (let page = 1; ; page += 1) {
    const separator = pathname.includes('?') ? '&' : '?';
    const batch = await getJson(`${apiRoot}${pathname}${separator}per_page=100&page=${page}`);
    values.push(...batch);
    if (batch.length < 100) return values;
  }
}

const releases = await getAllPages(`/repos/${repository}/releases`);
const index = {};

for (const release of releases) {
  if (release.draft || !release.tag_name.startsWith('publications-')) continue;
  const assets = await getAllPages(`/repos/${repository}/releases/${release.id}/assets`);
  for (const asset of assets) {
    if (!asset.name.toLowerCase().endsWith('.pdf')) continue;
    index[asset.name] ??= asset.browser_download_url;
  }
}

await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.writeFile(outputPath, `${JSON.stringify(index, null, 2)}\n`, 'utf8');
console.log(`Indexed ${Object.keys(index).length} release PDF(s).`);
