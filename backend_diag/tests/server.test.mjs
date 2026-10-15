import test from 'node:test';
import assert from 'node:assert/strict';
import {createHandler,createServer,basePath,publicUrl,parseArgs} from '../diag_main.mjs';
const response=()=>({status:0,headers:{},body:null,writeHead(status,headers){this.status=status;this.headers=headers;},end(body){this.body=body;}});
async function request(handler,url,method='GET',authorization,extra={}) {const res=response();await handler({url,method,headers:{authorization,...extra}},res);return res;}
const auth='Bearer test-key';
test('API authentication, encoded Japanese paths and static boundary',async()=>{
 const h=createHandler({token:'test-key',prefix:'/proxy/8097/',entries:[],coverage:{sourceTargetFiles:3333,complete:true}});
 assert.equal((await request(h,'/proxy/8097/api/一覧')).status,401);
 const listing=await request(h,'/proxy/8097/api/%E4%B8%80%E8%A6%A7','GET',auth);assert.equal(listing.status,200);assert.equal(JSON.parse(listing.body).調査.sourceTargetFiles,3333);
 for(const url of ['/proxy/8097/../catalog.json','/proxy/8097/catalog.json','/api/一覧','/proxy/8097/%ZZ']) assert.notEqual((await request(h,url,'GET',auth)).status,200);
 const shell=await request(h,'/proxy/8097/');assert.equal(shell.status,200);assert.match(shell.headers['Content-Security-Policy'],/frame-ancestors 'none'/);assert.ok(!shell.body.toString().includes('test-key'));
});
test('fixed diagnostic action, no command/path/body/query arguments',async()=>{
 let scans=0;const h=createHandler({token:'test-key',entries:[],scanFn:async()=>{scans++;return [];}});
 assert.equal((await request(h,'/api/診断','POST')).status,401);
 assert.equal((await request(h,'/api/診断','POST',auth,{'content-length':'4'})).status,400);
 assert.equal((await request(h,'/api/診断?command=bad','POST',auth)).status,400);
 assert.equal((await request(h,'/api/診断','POST',auth,{'transfer-encoding':'chunked'})).status,400);
 assert.equal(scans,0);assert.equal((await request(h,'/api/診断','POST',auth)).status,200);assert.equal(scans,1);
});
test('concurrent scan rejected and failed scan unlocks',async()=>{
 let release;const h=createHandler({token:'test-key',scanFn:()=>new Promise(r=>{release=r;})});
 const first=request(h,'/api/診断','POST',auth);assert.equal((await request(h,'/api/診断','POST',auth)).status,409);release([]);assert.equal((await first).status,200);
});
test('server connection/header bounds, no listener started',()=>{
 const server=createServer({token:'test-key',entries:[]});assert.equal(server.maxConnections,16);assert.equal(server.headersTimeout,10000);assert.equal(server.requestTimeout,10000);assert.equal(server.maxRequestsPerSocket,20);server.close();
});
test('strict args and Codespaces/base-path URLs',()=>{
 assert.deepEqual(parseArgs(['--browser','--no-open','--port','8097','--base-path','/proxy/8097']),{port:8097,prefix:'/proxy/8097/',noOpen:true,browser:true,help:false});
 for(const args of [['--port','-1'],['--port','65536'],['--command','whoami'],['--base-path','//evil/']]) assert.throws(()=>parseArgs(args));
 assert.equal(basePath('/proxy/8097'),'/proxy/8097/');assert.throws(()=>basePath('/a/../'));
 assert.equal(publicUrl(8097,'/',{CODESPACES:'true',CODESPACE_NAME:'safe-name',GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:'app.github.dev'}),'https://safe-name-8097.app.github.dev/');
 assert.equal(publicUrl(8097,'/',{CODESPACES:'true',CODESPACE_NAME:'bad/name',GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:'app.github.dev'}),'http://127.0.0.1:8097/');
});
