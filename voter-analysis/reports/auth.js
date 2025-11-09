/**
 * Authentication Module for Kerala Election Insights Dashboard
 * Handles password verification and access control
 */

class DashboardAuth {
    constructor() {
        this.passwordData = null;
        this.currentAccess = null; // { level: 'master' | 'ward', wardId: '...' }
        this.SESSION_KEY = 'dashboard_auth';
    }

    /**
     * Initialize authentication system
     */
    async init() {
        // Check if already logged in
        const savedAuth = this.loadSession();
        if (savedAuth) {
            this.currentAccess = savedAuth;
            return true;
        }
        return false;
    }

    /**
     * Load password hashes from server
     */
    async loadPasswordData() {
        try {
            const response = await fetch('passwords.json');
            if (!response.ok) {
                throw new Error('Failed to load password data');
            }
            this.passwordData = await response.json();
            return true;
        } catch (error) {
            console.error('Error loading password data:', error);
            return false;
        }
    }

    /**
     * Hash password using SHA-256
     * @param {string} password - Plain text password
     * @returns {Promise<string>} Hex hash
     */
    async hashPassword(password) {
        const msgBuffer = new TextEncoder().encode(password);
        const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        return hashHex;
    }

    /**
     * Verify entered password against stored hashes
     * @param {string} inputPassword - The password entered by user
     * @returns {Promise<Object|null>} Access info or null if invalid
     */
    async verifyPassword(inputPassword) {
        if (!this.passwordData) {
            await this.loadPasswordData();
        }

        if (!this.passwordData) {
            console.error('Password data not loaded');
            return null;
        }

        // Hash the input password
        const inputHash = await this.hashPassword(inputPassword);

        // Check master password
        if (inputHash === this.passwordData.master.hash) {
            return {
                level: 'master',
                wardId: null
            };
        }

        // Check ward passwords
        for (const [wardName, wardData] of Object.entries(this.passwordData.wards)) {
            if (inputHash === wardData.hash) {
                return {
                    level: 'ward',
                    wardId: wardName
                };
            }
        }

        return null;
    }

    /**
     * Handle login attempt
     * @param {string} password - The password entered by user
     * @returns {Promise<Object>} Result object with success status and message
     */
    async login(password) {
        if (!password || password.trim().length === 0) {
            return {
                success: false,
                message: 'Please enter a password'
            };
        }

        const access = await this.verifyPassword(password);

        if (access) {
            this.currentAccess = access;
            this.saveSession(access);

            return {
                success: true,
                level: access.level,
                wardId: access.wardId,
                message: access.level === 'master'
                    ? 'Master access granted - Full dashboard access'
                    : `Ward access granted - ${access.wardId}`
            };
        } else {
            return {
                success: false,
                message: 'Invalid password. Please try again.'
            };
        }
    }

    /**
     * Logout and clear session
     */
    logout() {
        this.currentAccess = null;
        sessionStorage.removeItem(this.SESSION_KEY);
        window.location.reload();
    }

    /**
     * Save authentication state to session storage
     */
    saveSession(access) {
        sessionStorage.setItem(this.SESSION_KEY, JSON.stringify(access));
    }

    /**
     * Load authentication state from session storage
     */
    loadSession() {
        const saved = sessionStorage.getItem(this.SESSION_KEY);
        if (saved) {
            try {
                return JSON.parse(saved);
            } catch (error) {
                console.error('Error parsing saved session:', error);
                return null;
            }
        }
        return null;
    }

    /**
     * Check if user has access to specific ward
     * @param {string} wardId - Ward identifier to check
     * @returns {boolean} True if user has access
     */
    hasAccessToWard(wardId) {
        if (!this.currentAccess) {
            return false;
        }

        // Master has access to everything
        if (this.currentAccess.level === 'master') {
            return true;
        }

        // Ward-specific access
        return this.currentAccess.wardId === wardId;
    }

    /**
     * Get current access level
     * @returns {Object|null} Current access info
     */
    getCurrentAccess() {
        return this.currentAccess;
    }

    /**
     * Filter ward list based on access level
     * @param {Array} wards - Full list of wards
     * @returns {Array} Filtered list of wards
     */
    filterWardsByAccess(wards) {
        if (!this.currentAccess) {
            return [];
        }

        // Master sees all wards
        if (this.currentAccess.level === 'master') {
            return wards;
        }

        // Ward-specific user sees only their ward
        return wards.filter(ward => ward.text === this.currentAccess.wardId);
    }

    /**
     * Check if current user is master
     * @returns {boolean}
     */
    isMaster() {
        return this.currentAccess && this.currentAccess.level === 'master';
    }
}

// Create global auth instance
const dashboardAuth = new DashboardAuth();
