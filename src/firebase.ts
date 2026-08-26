import { initializeApp, getApps, getApp } from 'firebase/app';
import {
  getAuth,
  RecaptchaVerifier,
  signInWithPhoneNumber,
  ConfirmationResult,
  UserCredential
} from 'firebase/auth';

// Firebase configuration from environment variables (with project fallbacks)
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'AIzaSyBHLTzWd6XHJTd2xp3kWOHszCvb4GWlWfU',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'letzryd-dev-test.firebaseapp.com',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'letzryd-dev-test',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || 'letzryd-dev-test.firebasestorage.app',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '925756819101',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || '1:925756819101:web:83388ce68b39a49b587674'
};

// Check if Firebase configuration is provided
export const isFirebaseConfigured = Boolean(
  firebaseConfig.apiKey &&
  firebaseConfig.apiKey !== 'YOUR_FIREBASE_API_KEY' &&
  firebaseConfig.projectId
);

// Initialize Firebase App
const app = isFirebaseConfigured
  ? (!getApps().length ? initializeApp(firebaseConfig) : getApp())
  : null;

// Initialize Firebase Auth
export const auth = app ? getAuth(app) : null;

export { RecaptchaVerifier, signInWithPhoneNumber };
export type { ConfirmationResult, UserCredential };
