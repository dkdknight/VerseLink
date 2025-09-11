import { getRoleLabel, getRoleBadgeClasses } from '../roles';

describe('role helpers', () => {
  test('returns owner label and class', () => {
    expect(getRoleLabel('admin', true)).toBe('Propriétaire');
    expect(getRoleBadgeClasses('admin', true)).toContain('purple');
  });

  test('returns admin label', () => {
    expect(getRoleLabel('admin')).toBe('Admin');
    expect(getRoleBadgeClasses('admin')).toContain('red');
  });

  test('returns moderator label', () => {
    expect(getRoleLabel('moderator')).toBe('Modérateur');
    expect(getRoleBadgeClasses('moderator')).toContain('yellow');
  });

  test('returns member label by default', () => {
    expect(getRoleLabel('unknown')).toBe('Membre');
    expect(getRoleBadgeClasses('unknown')).toContain('gray');
  });
});