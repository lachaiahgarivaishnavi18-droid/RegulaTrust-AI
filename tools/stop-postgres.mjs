import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { execFileSync, spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
import { existsSync } from 'node:fs';
const directory=resolve('../storage/postgres');
const require=createRequire(import.meta.url);
const dependencyRequire=createRequire(require.resolve('embedded-postgres'));
const {pg_ctl}=await import(pathToFileURL(dependencyRequire.resolve('@embedded-postgres/windows-x64')).href);
const status=existsSync(resolve(directory,'postmaster.pid'))?spawnSync(pg_ctl,['-D',directory,'status'],{windowsHide:true,stdio:'pipe'}).status:3;
if(status===0){execFileSync(pg_ctl,['-D',directory,'-m','fast','-w','stop'],{stdio:'inherit',windowsHide:true});}else if(status===3){console.log('Local development PostgreSQL is already stopped.');}else{throw new Error('Unable to determine local PostgreSQL status.');}
