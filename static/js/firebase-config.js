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

  // Initialize Firebase
  app = initializeApp(firebaseConfig);
  auth = getAuth(app);
} catch (error) {
  console.error("Firebase initialization failed:", error);
}

export { auth };
