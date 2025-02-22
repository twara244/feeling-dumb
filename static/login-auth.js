
// auth.js - CREATE THIS NEW FILE
import { 
    signInWithPopup,
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    sendPasswordResetEmail,
    fetchSignInMethodsForEmail
} from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js";
import { auth, provider, facebookProvider } from "./firebase-config.js";

export const authService = {
    // Google Authentication
    async signInWithGoogle() {
        try {
            provider.setCustomParameters({ 'prompt': 'select_account' });
            const result = await signInWithPopup(auth, provider);
            const idToken = await result.user.getIdToken();
            return { user: result.user, idToken };
        } catch (error) {
            throw this.handleAuthError(error);
        }
    },

    async signUpWithGoogle() {
        try {
            provider.setCustomParameters({ 'prompt': 'select_account' });
            const result = await signInWithPopup(auth, provider);
            const userExists = await this.checkIfUserExists(result.user.email);
            
            if (userExists) {
                throw new Error('User already exists');
            }
            
            const idToken = await result.user.getIdToken();
            return { user: result.user, idToken };
        } catch (error) {
            throw this.handleAuthError(error);
        }
    },

    // Facebook Authentication
    async signInWithFacebook() {
        try {
            facebookProvider.setCustomParameters({ 'display': 'popup' });
            const result = await signInWithPopup(auth, facebookProvider);
            const idToken = await result.user.getIdToken();
            return { user: result.user, idToken };
        } catch (error) {
            throw this.handleAuthError(error);
        }
    },

    async signUpWithFacebook() {
        try {
            facebookProvider.setCustomParameters({ 'display': 'popup' });
            const result = await signInWithPopup(auth, facebookProvider);
            const idToken = await result.user.getIdToken();
            return { user: result.user, idToken };
        } catch (error) {
            throw this.handleAuthError(error);
        }
    },

    // Email/Password Authentication
    async signInWithEmail(email, password) {
        try {
            const result = await signInWithEmailAndPassword(auth, email, password);
            const idToken = await result.user.getIdToken();
            return { user: result.user, idToken };
        } catch (error) {
            throw this.handleAuthError(error);
        }
    },

    async createAccountWithEmail(email, password) {
        try {
            const result = await createUserWithEmailAndPassword(auth, email, password);
            const idToken = await result.user.getIdToken();
            return { user: result.user, idToken };
        } catch (error) {
            throw this.handleAuthError(error);
        }
    },

    // Password Reset
    async resetPassword(email) {
        try {
            await sendPasswordResetEmail(auth, email);
        } catch (error) {
            throw this.handleAuthError(error);
        }
    },

    // Helper Methods
    async checkIfUserExists(email) {
        try {
            const signInMethods = await fetchSignInMethodsForEmail(auth, email);
            return signInMethods.length > 0;
        } catch (error) {
            throw this.handleAuthError(error);
        }
    },

    handleAuthError(error) {
        console.error('Auth Error:', error);
        
        const errorMessages = {
            'auth/invalid-email': 'Invalid email address',
            'auth/user-disabled': 'This account has been disabled',
            'auth/user-not-found': 'No account found with this email',
            'auth/wrong-password': 'Incorrect password',
            'auth/email-already-in-use': 'An account already exists with this email',
            'auth/weak-password': 'Password should be at least 6 characters',
            'auth/popup-closed-by-user': 'Sign-in popup was closed before completing',
            'auth/network-request-failed': 'Network error. Please check your connection'
        };

        return new Error(errorMessages[error.code] || error.message);
    }
};
