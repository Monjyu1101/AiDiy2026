import { register } from 'tsx/esm/api';
import { WorkerBootstrapper } from '@discordjs/ws';
register();
const { Discord通信 } = await import('./network.ts');
const network = new Discord通信();
network.Gateway開始();
// Gateway用agentとソケットはこのworkerだけが所有する。SDKのstrategy.destroy
// がworkerを終了し、認証前・再接続待ちを含めてソケットとタイマーを回収する。
await new WorkerBootstrapper().bootstrap();
