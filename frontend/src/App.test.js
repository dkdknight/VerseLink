import React from 'react';
import { render, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider, useAuth } from './App';
import { authService } from './services/authService';

jest.mock('./services/authService', () => ({
  authService: {
    discordCallback: jest.fn(),
    logout: jest.fn(),
    checkAuth: jest.fn(),
    setAuthToken: jest.fn(),
    clearAuthToken: jest.fn()
  }
}));

test('login → logout (failing) → login allows reconnection', async () => {
  localStorage.clear();
  let auth;
  const TestComponent = () => {
    auth = useAuth();
    return null;
  };

  authService.discordCallback.mockResolvedValueOnce({
    access_token: 'token1',
    user: { id: 1 }
  });
  authService.logout.mockRejectedValueOnce(new Error('logout failed'));

  render(
    <MemoryRouter>
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    </MemoryRouter>
  );

  await act(async () => {
    await auth.login('code1');
  });
  expect(auth.isAuthenticated).toBe(true);
  expect(auth.user.id).toBe(1);

  await act(async () => {
    await auth.logout();
  });
  expect(authService.clearAuthToken).toHaveBeenCalled();
  expect(auth.isAuthenticated).toBe(false);

  authService.discordCallback.mockResolvedValueOnce({
    access_token: 'token2',
    user: { id: 2 }
  });

  await act(async () => {
    await auth.login('code2');
  });
  expect(auth.isAuthenticated).toBe(true);
  expect(auth.user.id).toBe(2);
});