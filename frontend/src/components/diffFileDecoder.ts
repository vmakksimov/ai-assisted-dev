/**
 * Decodes an uploaded `.diff`/`.patch` file's raw bytes into text, handling the
 * BOM/encoding variants produced by different shells and editors.
 *
 * Notably, PowerShell's `git diff ... > review.diff` redirection writes
 * UTF-16 LE with a BOM by default, which mangles into garbage (interleaved
 * NUL bytes) if read with a plain UTF-8 decoder (e.g. `FileReader.readAsText`
 * with no encoding, or `File.text()`).
 */

export type DiffTextEncoding = 'utf-16le' | 'utf-16be' | 'utf-8';

const BOM_UTF16_LE = [0xff, 0xfe];
const BOM_UTF16_BE = [0xfe, 0xff];
const BOM_UTF8 = [0xef, 0xbb, 0xbf];

/** Inspects the leading bytes of a buffer and returns the detected encoding. */
export function detectEncoding(bytes: Uint8Array): DiffTextEncoding {
  if (bytes[0] === BOM_UTF16_LE[0] && bytes[1] === BOM_UTF16_LE[1]) {
    return 'utf-16le';
  }
  if (bytes[0] === BOM_UTF16_BE[0] && bytes[1] === BOM_UTF16_BE[1]) {
    return 'utf-16be';
  }
  if (
    bytes[0] === BOM_UTF8[0] &&
    bytes[1] === BOM_UTF8[1] &&
    bytes[2] === BOM_UTF8[2]
  ) {
    return 'utf-8';
  }
  return 'utf-8';
}

/** Strips a leading BOM character (U+FEFF) from decoded text, if present. */
export function stripBom(text: string): string {
  return text.charCodeAt(0) === 0xfeff ? text.slice(1) : text;
}

/**
 * Decodes raw file bytes into a clean string, auto-detecting UTF-16 LE/BE and
 * UTF-8 (with or without BOM). Always returns BOM-free text.
 */
export function decodeDiffFile(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  const encoding = detectEncoding(bytes);
  const decoder = new TextDecoder(encoding);
  const decoded = decoder.decode(buffer);
  return stripBom(decoded);
}
