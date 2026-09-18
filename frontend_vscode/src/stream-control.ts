export const STREAM_START = '\u0002';
export const STREAM_END = '\u0003';
export const STREAM_CANCEL = '\u0018';

export type StreamControl = 'start' | 'end' | 'cancel';

export function streamControlOf(content: string): StreamControl | undefined {
  const control = content.replace(/[\r\n]+$/, '');
  if (control === STREAM_START.trimEnd()) return 'start';
  if (control === STREAM_END.trimEnd()) return 'end';
  if (control === STREAM_CANCEL.trimEnd()) return 'cancel';
  return undefined;
}

export function visibleStreamContent(content: string): string {
  return content
    .replace(/[\u0002\u0003\u0018]/g, '')
    .replace(/[\r\n]+$/, '');
}
