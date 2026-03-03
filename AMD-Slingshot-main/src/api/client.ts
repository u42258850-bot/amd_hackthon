import axios from 'axios';
import { auth } from '../firebase';
import { onAuthStateChanged, type User } from 'firebase/auth';

const runtimeFallbackApiBaseUrl =
  typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
    ? 'https://amd-hackthon.onrender.com'
    : 'http://localhost:8000';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || runtimeFallbackApiBaseUrl;

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 120000,
});

export const refreshFirebaseAuthHeader = async () => {
  const currentUser = auth.currentUser ?? (await waitForFirebaseUser(6000));
  if (!currentUser) {
    throw new Error('AUTH_REQUIRED');
  }

  const token = await currentUser.getIdToken(true);
  return {
    Authorization: `Bearer ${token}`,
    'X-Dev-User-Id': currentUser.uid,
  };
};

const waitForFirebaseUser = (timeoutMs = 4000): Promise<User | null> => {
  return new Promise((resolve) => {
    const timeoutId = setTimeout(() => {
      unsubscribe();
      resolve(auth.currentUser);
    }, timeoutMs);

    const unsubscribe = onAuthStateChanged(auth, (user) => {
      clearTimeout(timeoutId);
      unsubscribe();
      resolve(user);
    });
  });
};

export const getFirebaseAuthHeader = async (fallbackUserId?: string) => {
  const currentUser = auth.currentUser ?? (await waitForFirebaseUser());
  if (!currentUser) {
    if (fallbackUserId) {
      return {
        'X-Dev-User-Id': fallbackUserId,
      };
    }
    throw new Error('AUTH_REQUIRED');
  }

  const token = await currentUser.getIdToken(true);
  return {
    Authorization: `Bearer ${token}`,
    'X-Dev-User-Id': currentUser.uid,
  };
};
