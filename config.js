// config.js - Separate Configuration File
// Create this file to keep your settings organized

// ===== ENVIRONMENT DETECTION =====
const ENVIRONMENT = {
    isDevelopment: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
    isProduction: window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1',
    isFileProtocol: window.location.protocol === 'file:'
};





// ===== BACKEND CONFIGURATIONS =====
const BACKEND_CONFIGS = {
    // Development servers
    local: {
        url: 'http://localhost:5000/api',
        name: 'Local Development Server',
        description: 'Default Flask development server'
    },
    localAlt: {
        url: 'http://127.0.0.1:5000/api',
        name: 'Local Alternative',
        description: 'Alternative local IP address'
    },
    custom: {
        url: 'http://localhost:8000/api',
        name: 'Custom Port',
        description: 'Custom development port'
    },
    docker: {
        url: 'http://localhost:3000/api',
        name: 'Docker Container',
        description: 'Dockerized backend'
    },
    
    // Production servers
    heroku: {
        url: 'https://your-app-name.herokuapp.com/api',
        name: 'Heroku Production',
        description: 'Heroku cloud deployment'
    },
    railway: {
        url: 'https://your-app.railway.app/api',
        name: 'Railway Production',
        description: 'Railway cloud deployment'
    },
    vercel: {
        url: 'https://your-app.vercel.app/api',
        name: 'Vercel Production',
        description: 'Vercel serverless deployment'
    },
    custom_domain: {
        url: 'https://api.yourdomain.com/api',
        name: 'Custom Domain',
        description: 'Your custom domain backend'
    }
};

// ===== SMART CONFIGURATION =====
const APP_CONFIG = {
    // Backend settings
    backend: {
        // Auto-select based on environment
        autoDetect: true,
        
        // Primary backend to try first
        primary: ENVIRONMENT.isDevelopment ? 'local' : 'heroku',
        
        // Fallback order (tried in sequence)
        fallbackOrder: ENVIRONMENT.isDevelopment 
            ? ['local', 'localAlt', 'custom', 'docker']
            : ['heroku', 'railway', 'vercel', 'custom_domain'],
        
        // Connection settings
        timeout: 10000,        // 10 seconds
        retryAttempts: 3,      // Retry 3 times
        retryDelay: 1000,      // 1 second between retries
        
        // Behavior settings
        fallbackToLocalStorage: true,    // Use localStorage if no backend
        showConnectionStatus: true,      // Show connection indicator
        autoReconnect: true,            // Try to reconnect periodically
        reconnectInterval: 30000        // Reconnect every 30 seconds
    },
    
    // Data settings
    data: {
        autosave: true,              // Auto-save to localStorage as backup
        syncInterval: 5000,          // Sync with backend every 5 seconds
        offlineQueueEnabled: true,   // Queue actions when offline
        maxOfflineActions: 100       // Maximum queued actions
    },
    
    // UI settings
    ui: {
        showDebugInfo: ENVIRONMENT.isDevelopment,  // Show debug info in dev mode
        animationSpeed: 300,                       // Animation duration (ms)
        notificationDuration: 4000,                // Notification display time (ms)
        theme: 'auto'                              // auto, light, dark
    },
    
    // Feature flags
    features: {
        exportImport: true,          // Enable data export/import
        advancedFiltering: true,     // Enable advanced filters
        charts: true,                // Enable chart visualization
        categories: true,            // Enable custom categories
        budgets: false,              // Enable budget features (future)
        multiCurrency: false         // Enable multiple currencies (future)
    }
};

// ===== DYNAMIC CONFIGURATION FUNCTIONS =====

// Get the best backend configuration for current environment
function getBestBackendConfig() {
    const primary = APP_CONFIG.backend.primary;
    
    if (BACKEND_CONFIGS[primary]) {
        return {
            name: primary,
            ...BACKEND_CONFIGS[primary]
        };
    }
    
    // Fallback to first available
    const fallback = APP_CONFIG.backend.fallbackOrder[0];
    return {
        name: fallback,
        ...BACKEND_CONFIGS[fallback]
    };
}

// Get all backend options for current environment
function getAvailableBackends() {
    const order = APP_CONFIG.backend.fallbackOrder;
    return order.map(name => ({
        name,
        ...BACKEND_CONFIGS[name]
    }));
}

// Update configuration at runtime
function updateConfig(section, key, value) {
    if (APP_CONFIG[section] && APP_CONFIG[section].hasOwnProperty(key)) {
        APP_CONFIG[section][key] = value;
        console.log(`✅ Config updated: ${section}.${key} = ${value}`);
        
        // Trigger configuration change event
        window.dispatchEvent(new CustomEvent('configChanged', {
            detail: { section, key, value }
        }));
        
        return true;
    } else {
        console.error(`❌ Invalid config path: ${section}.${key}`);
        return false;
    }
}

// Get current configuration
function getConfig(section = null, key = null) {
    if (section && key) {
        return APP_CONFIG[section]?.[key];
    } else if (section) {
        return APP_CONFIG[section];
    } else {
        return APP_CONFIG;
    }
}

// ===== BACKEND URL BUILDER =====
function buildBackendURL(configName, endpoint = '') {
    const config = BACKEND_CONFIGS[configName];
    if (!config) {
        throw new Error(`Backend configuration '${configName}' not found`);
    }
    
    const baseUrl = config.url.replace(/\/+$/, ''); // Remove trailing slashes
    const cleanEndpoint = endpoint.replace(/^\/+/, ''); // Remove leading slashes
    
    return cleanEndpoint ? `${baseUrl}/${cleanEndpoint}` : baseUrl;
}

// ===== ENVIRONMENT INFO =====
function getEnvironmentInfo() {
    return {
        ...ENVIRONMENT,
        hostname: window.location.hostname,
        protocol: window.location.protocol,
        port: window.location.port,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString()
    };
}

// ===== CONFIGURATION VALIDATION =====
function validateConfig() {
    const issues = [];
    
    // Check backend configurations
    Object.entries(BACKEND_CONFIGS).forEach(([name, config]) => {
        if (!config.url) {
            issues.push(`Backend '${name}' missing URL`);
        }
        if (!config.name) {
            issues.push(`Backend '${name}' missing name`);
        }
    });
    
    // Check fallback order
    APP_CONFIG.backend.fallbackOrder.forEach(name => {
        if (!BACKEND_CONFIGS[name]) {
            issues.push(`Fallback backend '${name}' not found in configurations`);
        }
    });
    
    if (issues.length > 0) {
        console.warn('⚠️ Configuration issues found:', issues);
        return { valid: false, issues };
    }
    
    console.log('✅ Configuration validation passed');
    return { valid: true, issues: [] };
}

// ===== EXPORT CONFIGURATION =====
// Make configurations globally available
window.BACKEND_CONFIGS = BACKEND_CONFIGS;
window.APP_CONFIG = APP_CONFIG;
window.ENVIRONMENT = ENVIRONMENT;

// Make functions globally available
window.getBestBackendConfig = getBestBackendConfig;
window.getAvailableBackends = getAvailableBackends;
window.updateConfig = updateConfig;
window.getConfig = getConfig;
window.buildBackendURL = buildBackendURL;
window.getEnvironmentInfo = getEnvironmentInfo;
window.validateConfig = validateConfig;

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Configuration loaded');
    console.log('📊 Environment:', getEnvironmentInfo());
    console.log('⚙️ Best backend:', getBestBackendConfig());
    
    // Validate configuration
    validateConfig();
    
    // Show available configurations in development
    if (ENVIRONMENT.isDevelopment) {
        console.log('🛠️ Available backends:', getAvailableBackends());
        console.log('🎛️ Full configuration:', APP_CONFIG);
    }
});

// ===== HELPER FUNCTIONS FOR CONSOLE =====
console.log('🔧 Configuration Helper Functions:');
console.log('- getBestBackendConfig() - Get recommended backend');
console.log('- getAvailableBackends() - List all backend options');
console.log('- updateConfig("section", "key", value) - Change configuration');
console.log('- getConfig("section", "key") - Get configuration value');
console.log('- getEnvironmentInfo() - Show environment details');
console.log('- validateConfig() - Check configuration validity');