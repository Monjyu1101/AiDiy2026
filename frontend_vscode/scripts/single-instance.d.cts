declare const instanceLock: {
  起動ロック(name: string, repeated?: () => void, port?: number): Promise<{
    port: number;
    close(): Promise<void>;
  } | null>;
};
export = instanceLock;
