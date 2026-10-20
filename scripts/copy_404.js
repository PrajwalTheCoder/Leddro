import fs from 'fs';
import path from 'path';

const distDir = path.resolve('dist');
const indexPath = path.join(distDir, 'index.html');
const notFoundPath = path.join(distDir, '404.html');

if (fs.existsSync(indexPath)) {
  let html = fs.readFileSync(indexPath, 'utf-8');
  
  // SPA redirect snippet for GitHub Pages subfolder
  const redirectScript = `
    <script>
      (function() {
        var path = window.location.pathname;
        var segments = path.split('/').filter(Boolean);
        if (segments.length > 0 && segments[0].toLowerCase() === 'leddro') {
          var repo = '/' + segments[0];
          var route = path.slice(repo.length);
          if (route && route !== '/' && !route.startsWith('/#')) {
            window.location.replace(repo + '/#' + route);
          }
        }
      })();
    </script>
  `;

  html = html.replace('</head>', `${redirectScript}</head>`);
  fs.writeFileSync(notFoundPath, html, 'utf-8');
  console.log('[build] Generated dist/404.html with GitHub Pages SPA redirect fallback');
}
