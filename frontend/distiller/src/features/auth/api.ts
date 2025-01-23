import { apiClient } from '../../client';
import { User } from '../../types';

type AuthResponse = {
  access_token: string;
  token_type: string;
  exp: number;
};

export function authenticate(
  username: string,
  password: string,
): Promise<AuthResponse> {
  const form = new FormData();
  form.append('username', username);
  form.append('password', password);

  return apiClient
    .post({
      path: 'token',
      form,
      extra: { credentials: 'include' },
    })
    .then((res) => res.json());
}

export function refreshToken(): Promise<AuthResponse> {
  return apiClient
    .post({
      path: 'refresh_token',
      extra: { credentials: 'include' },
    })
    .then((res) => res.json());
}

export function deleteRefreshToken(): Promise<void> {
  return apiClient
    .delete({
      path: 'refresh_token',
    })
    .then((_) => undefined);
}

export function getUser(): Promise<User> {
  return apiClient
    .get({
      path: 'users/me',
    })
    .then((res) => res.json());
}
