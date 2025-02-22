
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-app.js";
import { getAuth, 
        createUserWithEmailAndPassword,
        signInWithEmailAndPassword,
        signOut,
        onAuthStateChanged,
        signInWithPopup,
        GoogleAuthProvider,
        FacebookAuthProvider } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js";


const firebaseConfig = {
    apiKey: "AIzaSyAu_fXf_EoNpp10WRs7xc2F3fKbla7WAS0",
    authDomain: "simple-firebase-91658.firebaseapp.com",
    projectId: "simple-firebase-91658",
    storageBucket: "simple-firebase-91658.appspot.com",
    messagingSenderId: "424748845206",
    appId: "1:424748845206:web:966c5ed3fc459277411ab7",
    measurementId: "G-H4WKK504Y4"
  };

  // Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();
const new_provider = new FacebookAuthProvider();



