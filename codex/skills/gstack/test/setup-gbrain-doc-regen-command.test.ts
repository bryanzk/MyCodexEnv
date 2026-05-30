import { describe, test, expect } from 'bun:test';
import * as fs from 'fs';
import * as path from 'path';

const ROOT = path.resolve(import.meta.dir, '..');
const SETUP = fs.readFileSync(path.join(ROOT, 'setup'), 'utf-8');
const PACKAGE_JSON = JSON.parse(fs.readFileSync(path.join(ROOT, 'package.json'), 'utf-8')) as {
  scripts?: Record<string, string>;
};

describe('setup gbrain doc regen command', () => {
  test('setup uses an existing script path for brain-aware SKILL.md regeneration', () => {
    expect(PACKAGE_JSON.scripts?.['gen:skill-docs']).toBeString();
    expect(PACKAGE_JSON.scripts?.['gen:skill-docs:user']).toBeUndefined();
    expect(SETUP).toContain('bun_cmd run gen:skill-docs --respect-detection --host claude');
    expect(SETUP).not.toContain('gen:skill-docs:user');
  });
});
