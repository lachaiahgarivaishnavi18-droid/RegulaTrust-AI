import EmbeddedPostgres from 'embedded-postgres';
import { resolve } from 'node:path';
import { existsSync } from 'node:fs';
const directory=resolve('../storage/postgres');
const pg=new EmbeddedPostgres({databaseDir:directory,user:'regulatrust',password:process.env.LOCAL_DB_PASSWORD||'local-development-only',port:55432,persistent:true,autoRehydrateSymlinks:true,authMethod:'scram-sha-256',initdbFlags:['--encoding=UTF8','--locale=C']});
if(!existsSync(resolve(directory,'PG_VERSION')))await pg.initialise();
await pg.start();
const client=pg.getPgClient();await client.connect();
for(const name of ['regulatrust','regulatrust_test']){const found=await client.query('SELECT 1 FROM pg_database WHERE datname=$1',[name]);if(!found.rowCount)await client.query(`CREATE DATABASE ${name} ENCODING 'UTF8' LC_COLLATE 'C' LC_CTYPE 'C' TEMPLATE template0`);}
await client.end();
console.log('Local PostgreSQL ready on 127.0.0.1:55432 (development only).');
let stopping=false;
async function stop(){if(stopping)return;stopping=true;await pg.stop();process.exit(0);}
process.on('SIGINT',stop);process.on('SIGTERM',stop);
setInterval(()=>{},30000);
