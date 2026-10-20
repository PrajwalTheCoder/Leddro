import fs from 'fs';
import path from 'path';

const distDir = path.resolve('dist');
const notFoundPath = path.join(distDir, '404.html');

const html404 = `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Leddro — Redirecting...</title>
    <script type="text/javascript">
      // Single Page Apps for GitHub Pages
      // MIT License - https://github.com/rafgraph/spa-github-pages
      // pathSegmentsToKeep is 1 for project pages (e.g. username.github.io/Leddro/)
      var pathSegmentsToKeep = 1;
      var l = window.location;
      var repo = l.pathname.split('/').slice(0, 1 + pathSegmentsToKeep).join('/');
      var route = l.pathname.slice(1).split('/').slice(pathSegmentsToKeep).join('/').replace(/&/g, '~and~');
      var search = l.search ? '&' + l.search.slice(1).replace(/&/g, '~and~') : '';
      l.replace(
        l.protocol + '//' + l.hostname + (l.port ? ':' + l.port : '') +
        repo + '/?/' + route + search + l.hash
      );
    </script>
  </head>
  <body style="background:#0A0D13;color:#8B949E;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;">
    <p>Navigating to Leddro...</p>
  </body>
</html>
`;

fs.writeFileSync(notFoundPath, html404, 'utf-8');
console.log('[build] Generated dist/404.html with clean URL SPA redirect fallback (no hash)');
