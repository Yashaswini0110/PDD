// Import the functions you need from the SDKs you need
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

// Fetch config from backend
let app;
let auth;

try {
  const response = await fetch("/config/firebase");
  if (!response.ok) throw new Error("Failed to load Firebase config");
  const firebaseConfig = await response.json();

  // Check if Firebase config is valid (all required fields present)
  if (firebaseConfig.apiKey && firebaseConfig.authDomain && firebaseConfig.projectId) {
    // Initialize Firebase
    app = initializeApp(firebaseConfig);
    auth = getAuth(app);
  } else {
    console.warn("Firebase config is incomplete. Running in dev mode without Firebase.");
    // Create a mock auth object for development
    auth = null;
  }
} catch (error) {
  console.error("Firebase initialization failed:", error);
  console.warn("Running in dev mode without Firebase. Use sessionStorage.setItem('dev_bypass', 'true') to bypass auth.");
  auth = null;
}

export { auth };
