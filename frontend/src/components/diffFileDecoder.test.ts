import { describe, expect, it } from 'vitest';
import { decodeDiffFile, detectEncoding, stripBom } from './diffFileDecoder';

/** Encodes a string to UTF-16 LE bytes (no BOM). */
function toUtf16LeBytes(text: string): number[] {
  const bytes: number[] = [];
  for (let i = 0; i < text.length; i += 1) {
    const code = text.charCodeAt(i);
    bytes.push(code & 0xff, (code >> 8) & 0xff);
  }
  return bytes;
}

describe('decodeDiffFile', () => {
  it('decodes UTF-16 LE bytes with a BOM (PowerShell redirected diff)', () => {
    const content = 'diff --git a/x b/x\n@@ -1 +1 @@\n-old\n+new\n';
    const bytes = new Uint8Array([0xff, 0xfe, ...toUtf16LeBytes(content)]);
    const buffer = bytes.buffer;

    const result = decodeDiffFile(buffer);

    expect(result).toBe(content);
    expect(result.charCodeAt(0)).not.toBe(0xfeff);
  });

  it('decodes UTF-8 bytes with a BOM', () => {
    const content = 'diff --git a/x b/x\n';
    const encoded = new TextEncoder().encode(content);
    const bytes = new Uint8Array([0xef, 0xbb, 0xbf, ...encoded]);

    const result = decodeDiffFile(bytes.buffer);

    expect(result).toBe(content);
  });

  it('decodes plain UTF-8 bytes with no BOM', () => {
    const content = 'diff --git a/x b/x\n+added line\n';
    const encoded = new TextEncoder().encode(content);

    const result = decodeDiffFile(encoded.buffer);

    expect(result).toBe(content);
  });

  it('detects utf-16le, utf-16be, and utf-8 BOMs correctly', () => {
    expect(detectEncoding(new Uint8Array([0xff, 0xfe, 0x41, 0x00]))).toBe(
      'utf-16le',
    );
    expect(detectEncoding(new Uint8Array([0xfe, 0xff, 0x00, 0x41]))).toBe(
      'utf-16be',
    );
    expect(detectEncoding(new Uint8Array([0xef, 0xbb, 0xbf, 0x41]))).toBe(
      'utf-8',
    );
    expect(detectEncoding(new Uint8Array([0x41, 0x42, 0x43]))).toBe('utf-8');
  });

  it('strips a leading BOM character from decoded text', () => {
    expect(stripBom('﻿hello')).toBe('hello');
    expect(stripBom('hello')).toBe('hello');
  });
});
