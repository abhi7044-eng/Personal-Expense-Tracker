// Personal Expense Tracker - Fixed Version
// This version fixes common errors and improves reliability

// ===== CONFIGURATION SECTION =====
const BACKEND_CONFIGS = {
    local: 'http://localhost:5000/api',           // ✅ Your Python backend
    localAlt: 'http://127.0.0.1:5000/api',      // ✅ Alternative IP
    custom: 'http://localhost:8000/api',          // ✅ Custom port
    production: 'https://yourdomain.com/api'     // ✅ For later deployment
};

// ===== CHOOSE YOUR BACKEND MODE =====
let API_BASE_URL = 'http://localhost:5000/api';
let USE_BACKEND = true;
const AUTO_DETECT_BACKEND = true;

// ===== ADVANCED BACKEND SETTINGS =====
const BACKEND_SETTINGS = {
    timeout: 10000,
    retryAttempts: 3,
    fallbackToLocalStorage: true,
    showConnectionStatus: true
};

// Global variables
let transactions = [];
let backendConnected = false;
let currentFilters = { type: 'all', category: 'all', month: '' };

// Categories
const categories = {
    income: ['Salary', 'Freelance', 'Business', 'Investment', 'Gift', 'Bonus', 'Other Income'],
    expense: ['Food & Dining', 'Transportation', 'Housing', 'Utilities', 'Healthcare', 'Entertainment', 'Shopping', 'Education', 'Other Expense']
};

// DOM Elements - Initialize safely
let transactionForm, transactionType, transactionAmount, transactionCategory;
let transactionDescription, transactionDate, currentBalance, totalIncome;
let totalExpenses, transactionList, filterType, filterCategory;
let filterMonth, clearFiltersBtn;

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 Personal Expense Tracker - Fixed Version');
    
    // Initialize DOM elements safely
    if (!initializeDOMElements()) {
        console.error('❌ Failed to initialize DOM elements. Check your HTML structure.');
        showNotification('Error: Missing HTML elements. Please check your HTML file.', 'error');
        return;
    }
    
    console.log('📋 Configuration:', {
        API_BASE_URL,
        USE_BACKEND,
        AUTO_DETECT_BACKEND,
        BACKEND_SETTINGS
    });
    
    try {
        // Add connection status indicator
        addConnectionStatusIndicator();
        
        // Set today's date as default
        setTodayAsDefault();
        
        // Initialize backend connection
        if (USE_BACKEND || AUTO_DETECT_BACKEND) {
            await initializeBackendConnection();
        }
        
        // Load data
        await loadData();
        
        // Setup event listeners
        setupEventListeners();
        
        // Update display
        updateDisplay();
        updateFilterCategories();
        
        console.log('✅ Application initialized successfully');
        
    } catch (error) {
        console.error('❌ Initialization error:', error);
        showNotification('Application initialization failed. Using fallback mode.', 'error');
        
        // Fallback initialization
        loadDataFromStorage();
        updateDisplay();
    }
});

// ===== DOM INITIALIZATION =====
function initializeDOMElements() {
    try {
        transactionForm = document.getElementById('transaction-form');
        transactionType = document.getElementById('transaction-type');
        transactionAmount = document.getElementById('transaction-amount');
        transactionCategory = document.getElementById('transaction-category');
        transactionDescription = document.getElementById('transaction-description');
        transactionDate = document.getElementById('transaction-date');
        currentBalance = document.getElementById('current-balance');
        totalIncome = document.getElementById('total-income');
        totalExpenses = document.getElementById('total-expenses');
        transactionList = document.getElementById('transaction-list');
        filterType = document.getElementById('filter-type');
        filterCategory = document.getElementById('filter-category');
        filterMonth = document.getElementById('filter-month');
        clearFiltersBtn = document.getElementById('clear-filters');
        
        // Check if all required elements exist
        const requiredElements = [
            transactionForm, transactionType, transactionAmount, transactionCategory,
            transactionDescription, transactionDate, currentBalance, totalIncome,
            totalExpenses, transactionList
        ];
        
        const missingElements = requiredElements.filter(element => !element);
        
        if (missingElements.length > 0) {
            console.error('❌ Missing DOM elements:', missingElements.length);
            return false;
        }
        
        return true;
        
    } catch (error) {
        console.error('❌ Error initializing DOM elements:', error);
        return false;
    }
}

// ===== BACKEND CONNECTION METHODS =====
async function initializeBackendConnection() {
    console.log('🔌 Initializing backend connection...');
    updateConnectionStatus('connecting', 'Connecting to server...');
    
    const configs = Object.entries(BACKEND_CONFIGS);
    
    for (const [name, url] of configs) {
        console.log(`🔍 Trying ${name}: ${url}`);
        
        try {
            const isConnected = await testBackendConnection(url);
            if (isConnected) {
                API_BASE_URL = url;
                backendConnected = true;
                USE_BACKEND = true;
                
                console.log(`✅ Connected to ${name} backend: ${url}`);
                updateConnectionStatus('connected', `Connected to ${name} server`);
                showNotification(`Backend connected: ${name}`, 'success');
                
                return true;
            }
        } catch (error) {
            console.log(`❌ Failed to connect to ${name}: ${error.message}`);
        }
    }
    
    // No backend connection established
    console.log('🔄 No backend connection available');
    backendConnected = false;
    USE_BACKEND = false;
    
    if (BACKEND_SETTINGS.fallbackToLocalStorage) {
        updateConnectionStatus('offline', 'Using offline mode (localStorage)');
        showNotification('Backend unavailable. Using offline mode.', 'warning');
    } else {
        updateConnectionStatus('error', 'Backend connection failed');
        showNotification('Backend connection failed!', 'error');
    }
    
    return false;
}

async function testBackendConnection(url, timeout = BACKEND_SETTINGS.timeout) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
        const response = await fetch(`${url}/transactions`, {
            method: 'GET',
            signal: controller.signal,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
            const data = await response.json();
            return data.success !== false;
        }
        return false;
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            throw new Error('Connection timeout');
        }
        throw error;
    }
}

// ===== CONNECTION STATUS INDICATOR =====
function addConnectionStatusIndicator() {
    // Remove existing indicator if present
    const existing = document.getElementById('connection-status');
    if (existing) {
        existing.remove();
    }
    
    const indicator = document.createElement('div');
    indicator.id = 'connection-status';
    indicator.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        z-index: 1001;
        color: white;
        background: #6c757d;
        border: 2px solid transparent;
        transition: all 0.3s ease;
        cursor: pointer;
    `;
    indicator.textContent = 'Initializing...';
    indicator.title = 'Click for connection details';
    
    // Add click handler for connection info
    indicator.addEventListener('click', () => {
        const info = getConnectionInfo();
        alert(`Connection Status:
Backend Connected: ${info.connected}
Current URL: ${info.url}
Mode: ${info.mode}
Transactions: ${info.transactionCount}`);
    });
    
    document.body.appendChild(indicator);
}

function updateConnectionStatus(status, message) {
    const indicator = document.getElementById('connection-status');
    if (!indicator) return;
    
    const styles = {
        connected: { background: '#28a745', border: '2px solid #20c997' },
        offline: { background: '#ffc107', border: '2px solid #fd7e14', color: '#000' },
        error: { background: '#dc3545', border: '2px solid #e74c3c' },
        connecting: { background: '#17a2b8', border: '2px solid #20c997' }
    };
    
    const style = styles[status] || styles.connecting;
    Object.assign(indicator.style, style);
    indicator.textContent = message;
    
    if (!BACKEND_SETTINGS.showConnectionStatus) {
        indicator.style.display = 'none';
    }
}

// ===== ENHANCED API METHODS =====
async function makeAPIRequest(endpoint, options = {}) {
    if (!USE_BACKEND || !backendConnected) {
        throw new Error('Backend not available');
    }
    
    const url = `${API_BASE_URL}${endpoint}`;
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    for (let attempt = 1; attempt <= BACKEND_SETTINGS.retryAttempts; attempt++) {
        try {
            console.log(`🔄 API Request (attempt ${attempt}): ${options.method || 'GET'} ${url}`);
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), BACKEND_SETTINGS.timeout);
            
            const response = await fetch(url, {
                ...finalOptions,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                const errorText = await response.text();
                let errorData;
                try {
                    errorData = JSON.parse(errorText);
                } catch {
                    errorData = { error: errorText || `HTTP ${response.status}` };
                }
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }
            
            const data = await response.json();
            console.log(`✅ API Success: ${url}`);
            return data;
            
        } catch (error) {
            console.log(`❌ API Error (attempt ${attempt}): ${error.message}`);
            
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            
            if (attempt === BACKEND_SETTINGS.retryAttempts) {
                if (BACKEND_SETTINGS.fallbackToLocalStorage) {
                    console.log('🔄 Falling back to localStorage');
                    backendConnected = false;
                    USE_BACKEND = false;
                    updateConnectionStatus('offline', 'Backend disconnected - using offline mode');
                }
                throw new Error(`Backend unavailable: ${error.message}`);
            }
            
            // Wait before retry
            await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
        }
    }
}

// ===== DATA MANAGEMENT =====
async function handleFormSubmit(event) {
    event.preventDefault();
    
    try {
        const type = transactionType.value;
        const amount = parseFloat(transactionAmount.value);
        const category = transactionCategory.value;
        const description = transactionDescription.value.trim();
        const date = transactionDate.value;
        
        // Enhanced validation
        if (!type || !amount || !category || !description || !date) {
            showNotification('Please fill in all fields!', 'error');
            return;
        }
        
        if (isNaN(amount) || amount <= 0) {
            showNotification('Please enter a valid amount greater than zero!', 'error');
            return;
        }
        
        if (description.length < 2) {
            showNotification('Description must be at least 2 characters long!', 'error');
            return;
        }
        
        const newTransaction = { 
            type, 
            amount: parseFloat(amount.toFixed(2)), // Ensure proper decimal handling
            category, 
            description, 
            date 
        };
        
        // Add transaction
        if (USE_BACKEND && backendConnected) {
            await addTransactionToBackend(newTransaction);
        } else {
            addTransactionToLocalStorage(newTransaction);
        }
        
        await loadData();
        updateDisplay();
        
        // Reset form
        transactionForm.reset();
        setTodayAsDefault();
        updateCategoryOptions(); // Reset category dropdown
        
        showNotification(`${type.charAt(0).toUpperCase() + type.slice(1)} of $${amount.toFixed(2)} added successfully!`, 'success');
        
    } catch (error) {
        console.error('Error adding transaction:', error);
        
        if (BACKEND_SETTINGS.fallbackToLocalStorage && error.message.includes('Backend unavailable')) {
            try {
                const type = transactionType.value;
                const amount = parseFloat(transactionAmount.value);
                const category = transactionCategory.value;
                const description = transactionDescription.value.trim();
                const date = transactionDate.value;
                
                const newTransaction = { type, amount, category, description, date };
                addTransactionToLocalStorage(newTransaction);
                await loadData();
                updateDisplay();
                showNotification('Added to offline storage (backend unavailable)', 'warning');
            } catch (fallbackError) {
                console.error('Fallback error:', fallbackError);
                showNotification('Error adding transaction!', 'error');
            }
        } else {
            showNotification('Error adding transaction: ' + error.message, 'error');
        }
    }
}

// Backend API methods
async function addTransactionToBackend(transaction) {
    const result = await makeAPIRequest('/transactions', {
        method: 'POST',
        body: JSON.stringify(transaction)
    });
    return result;
}

async function loadDataFromBackend() {
    const result = await makeAPIRequest('/transactions');
    transactions = Array.isArray(result.data) ? result.data : [];
    console.log(`📊 Loaded ${transactions.length} transactions from backend`);
}

async function deleteTransactionFromBackend(transactionId) {
    await makeAPIRequest(`/transactions/${transactionId}`, {
        method: 'DELETE'
    });
}

// LocalStorage methods (fallback)
function addTransactionToLocalStorage(transaction) {
    transaction.id = Date.now() + Math.random(); // Ensure unique ID
    transaction.timestamp = new Date().toISOString();
    transactions.push(transaction);
    saveDataToStorage();
}

function loadDataFromStorage() {
    try {
        const savedData = localStorage.getItem('expenseTrackerData');
        if (savedData) {
            const parsedData = JSON.parse(savedData);
            transactions = Array.isArray(parsedData) ? parsedData : [];
            console.log(`📊 Loaded ${transactions.length} transactions from localStorage`);
        } else {
            transactions = [];
        }
    } catch (error) {
        console.error('Error loading from localStorage:', error);
        transactions = [];
        showNotification('Error loading saved data. Starting fresh.', 'warning');
    }
}

function saveDataToStorage() {
    try {
        localStorage.setItem('expenseTrackerData', JSON.stringify(transactions));
        console.log('💾 Data saved to localStorage');
    } catch (error) {
        console.error('Error saving to localStorage:', error);
        showNotification('Error saving data to local storage!', 'error');
    }
}

// Enhanced data loading
async function loadData() {
    try {
        if (USE_BACKEND && backendConnected) {
            await loadDataFromBackend();
        } else {
            loadDataFromStorage();
        }
    } catch (error) {
        console.error('Error loading data:', error);
        if (BACKEND_SETTINGS.fallbackToLocalStorage) {
            console.log('🔄 Falling back to localStorage');
            loadDataFromStorage();
        } else {
            transactions = [];
        }
    }
}

// Enhanced delete with backend support
async function deleteTransaction(transactionId) {
    if (!confirm('Are you sure you want to delete this transaction?')) {
        return;
    }
    
    try {
        if (USE_BACKEND && backendConnected) {
            await deleteTransactionFromBackend(transactionId);
        } else {
            transactions = transactions.filter(t => t.id != transactionId); // Use != for type flexibility
            saveDataToStorage();
        }
        
        await loadData();
        updateDisplay();
        showNotification('Transaction deleted successfully!', 'success');
        
    } catch (error) {
        console.error('Error deleting transaction:', error);
        showNotification('Error deleting transaction: ' + error.message, 'error');
    }
}

// ===== UTILITY FUNCTIONS =====
function setTodayAsDefault() {
    if (transactionDate) {
        const today = new Date().toISOString().split('T')[0];
        transactionDate.value = today;
    }
}

function setupEventListeners() {
    if (transactionForm) {
        transactionForm.addEventListener('submit', handleFormSubmit);
    }
    
    if (transactionType) {
        transactionType.addEventListener('change', updateCategoryOptions);
    }
    
    if (filterType) {
        filterType.addEventListener('change', handleFilterChange);
    }
    
    if (filterCategory) {
        filterCategory.addEventListener('change', handleFilterChange);
    }
    
    if (filterMonth) {
        filterMonth.addEventListener('change', handleFilterChange);
    }
    
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearAllFilters);
    }
}

function updateCategoryOptions() {
    if (!transactionType || !transactionCategory) return;
    
    const selectedType = transactionType.value;
    const categorySelect = transactionCategory;
    
    categorySelect.innerHTML = '<option value="">Select Category</option>';
    
    if (selectedType && categories[selectedType]) {
        categories[selectedType].forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categorySelect.appendChild(option);
        });
    }
}

function updateDisplay() {
    const totals = calculateTotals();
    
    if (currentBalance) {
        currentBalance.textContent = formatCurrency(totals.balance);
        currentBalance.style.color = totals.balance >= 0 ? '#28a745' : '#dc3545';
    }
    
    if (totalIncome) {
        totalIncome.textContent = formatCurrency(totals.income);
    }
    
    if (totalExpenses) {
        totalExpenses.textContent = formatCurrency(totals.expenses);
    }
    
    displayTransactions();
    updateFilterCategories();
}

function calculateTotals() {
    let income = 0;
    let expenses = 0;
    
    transactions.forEach(transaction => {
        const amount = parseFloat(transaction.amount) || 0;
        if (transaction.type === 'income') {
            income += amount;
        } else if (transaction.type === 'expense') {
            expenses += amount;
        }
    });
    
    return { income, expenses, balance: income - expenses };
}

function displayTransactions() {
    if (!transactionList) return;
    
    const filteredTransactions = getFilteredTransactions();
    
    transactionList.innerHTML = '';
    
    if (filteredTransactions.length === 0) {
        const noTransactionsMsg = document.createElement('p');
        noTransactionsMsg.className = 'no-transactions';
        noTransactionsMsg.textContent = transactions.length === 0 
            ? 'No transactions yet. Add your first transaction above!' 
            : 'No transactions match your current filters.';
        transactionList.appendChild(noTransactionsMsg);
        return;
    }
    
    // Sort by date (newest first)
    filteredTransactions.sort((a, b) => new Date(b.date) - new Date(a.date));
    
    filteredTransactions.forEach(transaction => {
        const transactionElement = createTransactionElement(transaction);
        transactionList.appendChild(transactionElement);
    });
}

function createTransactionElement(transaction) {
    const div = document.createElement('div');
    div.className = 'transaction-item fade-in';
    
    let formattedDate;
    try {
        formattedDate = new Date(transaction.date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (error) {
        formattedDate = transaction.date || 'Invalid Date';
    }
    
    const amount = parseFloat(transaction.amount) || 0;
    
    div.innerHTML = `
        <div class="transaction-info">
            <div class="transaction-description">${escapeHtml(transaction.description || 'No description')}</div>
            <div class="transaction-meta">
                ${escapeHtml(transaction.category || 'No category')} • ${formattedDate}
            </div>
        </div>
        <div class="transaction-amount ${transaction.type}">
            ${transaction.type === 'income' ? '+' : '-'}${formatCurrency(amount)}
        </div>
        <button class="btn btn-danger" onclick="deleteTransaction(${transaction.id})">
            Delete
        </button>
    `;
    
    return div;
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function getFilteredTransactions() {
    return transactions.filter(transaction => {
        if (currentFilters.type !== 'all' && transaction.type !== currentFilters.type) {
            return false;
        }
        
        if (currentFilters.category !== 'all' && transaction.category !== currentFilters.category) {
            return false;
        }
        
        if (currentFilters.month) {
            const transactionMonth = transaction.date ? transaction.date.substring(0, 7) : '';
            if (transactionMonth !== currentFilters.month) {
                return false;
            }
        }
        
        return true;
    });
}

function handleFilterChange() {
    if (filterType) currentFilters.type = filterType.value;
    if (filterCategory) currentFilters.category = filterCategory.value;
    if (filterMonth) currentFilters.month = filterMonth.value;
    
    displayTransactions();
}

function clearAllFilters() {
    if (filterType) filterType.value = 'all';
    if (filterCategory) filterCategory.value = 'all';
    if (filterMonth) filterMonth.value = '';
    
    currentFilters = { type: 'all', category: 'all', month: '' };
    
    displayTransactions();
    showNotification('Filters cleared!', 'info');
}

function updateFilterCategories() {
    if (!filterCategory) return;
    
    const categoryFilter = filterCategory;
    const currentValue = categoryFilter.value;
    
    const uniqueCategories = [...new Set(transactions.map(t => t.category))].filter(Boolean).sort();
    
    categoryFilter.innerHTML = '<option value="all">All Categories</option>';
    
    uniqueCategories.forEach(category => {
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category;
        categoryFilter.appendChild(option);
    });
    
    if (uniqueCategories.includes(currentValue)) {
        categoryFilter.value = currentValue;
    }
}

function formatCurrency(amount) {
    const numAmount = parseFloat(amount) || 0;
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
    }).format(Math.abs(numAmount));
}

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    Object.assign(notification.style, {
        position: 'fixed',
        top: '60px',
        right: '20px',
        padding: '1rem 2rem',
        borderRadius: '8px',
        color: 'white',
        fontWeight: '500',
        zIndex: '1000',
        transform: 'translateX(100%)',
        transition: 'transform 0.3s ease',
        maxWidth: '300px',
        wordWrap: 'break-word',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
    });
    
    const colors = {
        success: '#28a745',
        error: '#dc3545',
        info: '#17a2b8',
        warning: '#ffc107'
    };
    notification.style.backgroundColor = colors[type] || colors.info;
    
    if (type === 'warning') {
        notification.style.color = '#000';
    }
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 4000);
}

// ===== ADVANCED UTILITY FUNCTIONS =====
async function connectToBackend() {
    updateConnectionStatus('connecting', 'Connecting...');
    const connected = await initializeBackendConnection();
    if (connected) {
        await loadData();
        updateDisplay();
    }
}

function switchBackend(configName) {
    if (BACKEND_CONFIGS[configName]) {
        API_BASE_URL = BACKEND_CONFIGS[configName];
        console.log(`🔄 Switched to ${configName}: ${API_BASE_URL}`);
        connectToBackend();
    } else {
        console.error(`❌ Backend config '${configName}' not found`);
        showNotification(`Backend config '${configName}' not found`, 'error');
    }
}

function getConnectionInfo() {
    return {
        connected: backendConnected,
        url: API_BASE_URL,
        mode: USE_BACKEND ? 'backend' : 'localStorage',
        transactionCount: transactions.length,
        autoDetect: AUTO_DETECT_BACKEND,
        settings: BACKEND_SETTINGS
    };
}

function exportData() {
    try {
        const dataStr = JSON.stringify(transactions, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `expense_tracker_data_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showNotification('Data exported successfully!', 'success');
    } catch (error) {
        console.error('Export error:', error);
        showNotification('Error exporting data!', 'error');
    }
}

async function addSampleData() {
    const sampleTransactions = [
        { type: 'income', amount: 3000, category: 'Salary', description: 'Monthly Salary', date: '2024-08-01' },
        { type: 'expense', amount: 800, category: 'Housing', description: 'Rent Payment', date: '2024-08-01' },
        { type: 'expense', amount: 150, category: 'Food & Dining', description: 'Grocery Shopping', date: '2024-08-02' },
        { type: 'income', amount: 500, category: 'Freelance', description: 'Web Design Project', date: '2024-08-03' },
        { type: 'expense', amount: 60, category: 'Transportation', description: 'Gas for Car', date: '2024-08-04' }
    ];
    
    try {
        for (const transaction of sampleTransactions) {
            if (USE_BACKEND && backendConnected) {
                await addTransactionToBackend(transaction);
            } else {
                addTransactionToLocalStorage(transaction);
            }
        }
        
        await loadData();
        updateDisplay();
        showNotification('Sample data added!', 'success');
        
    } catch (error) {
        console.error('Error adding sample data:', error);
        showNotification('Error adding sample data: ' + error.message, 'error');
    }
}

// Console helper functions
console.log('🛠️  Available Functions:');
console.log('- connectToBackend() - Reconnect to Python server');
console.log('- switchBackend("local") - Switch backend (local/localAlt/custom/production)');
console.log('- getConnectionInfo() - Show connection status');
console.log('- addSampleData() - Add test transactions');
console.log('- exportData() - Download transactions as JSON');

// Make functions globally available
window.connectToBackend = connectToBackend;
window.switchBackend = switchBackend;
window.getConnectionInfo = getConnectionInfo;
window.addSampleData = addSampleData;
window.exportData = exportData;
window.deleteTransaction = deleteTransaction;