// firebase-config.js - KEEP THIS FILE AND MODIFY IT
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-app.js";
import { 
    getAuth, 
    GoogleAuthProvider,
    FacebookAuthProvider
} from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-firestore.js";

const firebaseConfig = {
    apiKey: "AIzaSyBorSfB85wz5fF1chryeogjwalxLclH3Q0",
    authDomain: "feelingdumb-bcca6.firebaseapp.com",
    databaseURL: "https://feelingdumb-bcca6-default-rtdb.firebaseio.com",
    projectId: "feelingdumb-bcca6",
    storageBucket: "feelingdumb-bcca6.firebasestorage.app",
    messagingSenderId: "751169232781",
    appId: "1:751169232781:web:0eb3314995b45639dfe7c4",
    measurementId: "G-YLKSEWQ7Z2"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
auth.languageCode = 'en';
const googleProvider = new GoogleAuthProvider();
const facebookProvider = new FacebookAuthProvider();
const db = getFirestore(app);

export { auth, googleProvider as provider, facebookProvider, db };
