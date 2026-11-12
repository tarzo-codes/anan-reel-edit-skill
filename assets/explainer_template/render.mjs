// node render.mjs stills 25,200,600   |   node render.mjs video
// Renders the 1080x1920 explainer at scale 2 (2160x3840) so it sits on the reel at 100%.
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import path from 'node:path';
import fs from 'node:fs';
const [mode, list] = process.argv.slice(2);
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const composition = await selectComposition({serveUrl, id: 'explainer'});
fs.mkdirSync('out', {recursive: true});
if (mode === 'stills') {
  for (const fr of list.split(',')) {
    await renderStill({composition, serveUrl, output: `out/still_${fr}.png`, frame: Number(fr), imageFormat: 'png'});
    console.log('still', fr);
  }
} else {
  await renderMedia({composition, serveUrl, codec: 'h264', crf: 16, scale: 2, outputLocation: 'out/r5v2_explainer.mp4',
    concurrency: 6, muted: true, onProgress: ({progress}) => { if (Math.round(progress * 100) % 10 === 0) process.stdout.write(`${Math.round(progress * 100)}% `); }});
  console.log('\nvideo done');
}
