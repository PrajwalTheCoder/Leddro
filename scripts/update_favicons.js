import fs from 'fs';
import path from 'path';

const pubDir = path.resolve('public');
const logoPath = path.join(pubDir, 'logo.png');

fs.copyFileSync(logoPath, path.join(pubDir, 'favicon.png'));
fs.copyFileSync(logoPath, path.join(pubDir, 'favicon.ico'));

const b64 = fs.readFileSync(logoPath).toString('base64');
const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024"><image width="1024" height="1024" href="data:image/png;base64,${b64}"/></svg>`;
fs.writeFileSync(path.join(pubDir, 'favicon.svg'), svg, 'utf-8');

console.log('Successfully generated public/favicon.svg, favicon.png, favicon.ico from logo.png');
