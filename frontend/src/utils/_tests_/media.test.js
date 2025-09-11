import { getMediaUrl } from '../media';

describe('getMediaUrl', () => {
  const originalEnv = process.env.REACT_APP_BACKEND_URL;

  beforeEach(() => {
    process.env.REACT_APP_BACKEND_URL = 'http://backend.test';
  });

  afterEach(() => {
    process.env.REACT_APP_BACKEND_URL = originalEnv;
  });

  test('returns absolute URL unchanged', () => {
    expect(getMediaUrl('http://example.com/img.png')).toBe('http://example.com/img.png');
  });

  test('prefixes backend URL for relative paths', () => {
    expect(getMediaUrl('/uploads/logo.png')).toBe('http://backend.test/uploads/logo.png');
  });

  test('returns empty string for falsy input', () => {
    expect(getMediaUrl(null)).toBe('');
  });
});