// Use Vite's compiler so the exporter shares the site's TEI renderer and locales.
import {createServer} from 'vite';
process.env.BOOKSTACKS_BUILD_EPUB='1';
const server=await createServer({configFile:false,server:{middlewareMode:true},appType:'custom',logLevel:'error'});
try{const exporter=await server.ssrLoadModule('/scripts/build_epubs.ts');await exporter.main(process.argv.slice(2));}
finally{await server.close();}
