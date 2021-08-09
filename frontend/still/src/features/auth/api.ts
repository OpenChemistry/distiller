import { apiClient } from '../../client';
import { User } from '../../types';

type AuthResponse = {
  access_token: string;
  token_type: string;
}

export function authenticate(username: string, password: string): Promise<AuthResponse> {
  const form = new FormData();
  form.append('username', username);
  form.append('password', password);

  return apiClient.post({
    url: 'token',
    form,
  }).then(res => res.json());
}

export function getUser(): Promise<User> {
  return apiClient.get({
    url: 'users/me',
  }).then(res => res.json());
}
