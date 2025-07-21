// Sistema Financeiro - Main JavaScript Functions

// Global variables
let currentUser = null;
let isLoading = false;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    checkUserSession();
});

function initializeApp() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Add loading states to forms
    setupFormLoading();
    
    // Setup auto-logout on inactivity
    setupAutoLogout();
}

function setupEventListeners() {
    // Global search functionality
    const searchInputs = document.querySelectorAll('[data-search]');
    searchInputs.forEach(input => {
        input.addEventListener('keyup', debounce(function() {
            const searchType = this.dataset.search;
            const searchValue = this.value;
            performSearch(searchType, searchValue);
        }, 300));
    });

    // Auto-save functionality for forms
    const autoSaveForms = document.querySelectorAll('[data-auto-save]');
    autoSaveForms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('change', debounce(function() {
                autoSaveForm(form);
            }, 1000));
        });
    });

    // Confirmation dialogs
    const confirmBtns = document.querySelectorAll('[data-confirm]');
    confirmBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const message = this.dataset.confirm;
            if (!confirm(message)) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    });
}

function checkUserSession() {
    if (window.location.pathname.includes('/login') || window.location.pathname.includes('/register')) {
        return;
    }

    fetch('/api/user')
        .then(response => {
            if (!response.ok) {
                window.location.href = '/login';
                return;
            }
            return response.json();
        })
        .then(data => {
            if (data && data.user) {
                currentUser = data.user;
                updateUserInterface();
            } else {
                window.location.href = '/login';
            }
        })
        .catch(error => {
            console.error('Session check failed:', error);
            if (!window.location.pathname.includes('/login')) {
                window.location.href = '/login';
            }
        });
}

function updateUserInterface() {
    if (currentUser) {
        // Update user display in navbar
        const userDisplay = document.querySelector('.navbar .dropdown-toggle');
        if (userDisplay) {
            userDisplay.innerHTML = `<i class="fas fa-user me-1"></i>${currentUser.username}`;
        }

        // Update plan information if available
        if (currentUser.plan) {
            updatePlanDisplay(currentUser.plan);
        }
    }
}

function updatePlanDisplay(plan) {
    const planElements = document.querySelectorAll('[data-plan]');
    planElements.forEach(element => {
        const planData = element.dataset.plan;
        if (planData === 'name') {
            element.textContent = getPlanDisplayName(plan.plan_name);
        } else if (planData === 'limits') {
            element.innerHTML = `
                <small class="d-block">Clientes: ${plan.max_clients}</small>
                <small class="d-block">A Receber: ${plan.max_receivables}</small>
                <small class="d-block">A Pagar: ${plan.max_payables}</small>
            `;
        }
    });
}

// Loading functions
function showLoading() {
    if (isLoading) return;
    
    isLoading = true;
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.classList.remove('d-none');
    }
}

function hideLoading() {
    isLoading = false;
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.classList.add('d-none');
    }
}

// Toast notification functions
function showToast(message, type = 'info', duration = 5000) {
    const toast = document.getElementById('toast');
    if (!toast) return;

    const toastBody = toast.querySelector('.toast-body');
    const toastHeader = toast.querySelector('.toast-header');
    
    // Set message
    toastBody.textContent = message;
    
    // Set icon and colors based on type
    const icon = toastHeader.querySelector('i');
    toastHeader.className = 'toast-header';
    
    switch (type) {
        case 'success':
            toastHeader.classList.add('bg-success', 'text-white');
            icon.className = 'fas fa-check-circle me-2';
            break;
        case 'error':
            toastHeader.classList.add('bg-danger', 'text-white');
            icon.className = 'fas fa-exclamation-circle me-2';
            break;
        case 'warning':
            toastHeader.classList.add('bg-warning', 'text-dark');
            icon.className = 'fas fa-exclamation-triangle me-2';
            break;
        default:
            toastHeader.classList.add('bg-info', 'text-white');
            icon.className = 'fas fa-info-circle me-2';
    }
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast, { delay: duration });
    bsToast.show();
}

// Form handling functions
function setupFormLoading() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processando...';
                
                // Restore button after 30 seconds (fallback)
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 30000);
            }
        });
    });
}

function autoSaveForm(form) {
    const formData = new FormData(form);
    const autoSaveUrl = form.dataset.autoSave;
    
    if (!autoSaveUrl) return;
    
    fetch(autoSaveUrl, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Alterações salvas automaticamente', 'success', 2000);
        }
    })
    .catch(error => {
        console.error('Auto-save failed:', error);
    });
}

// Search functions
function performSearch(type, query) {
    const searchResults = document.querySelector(`[data-search-results="${type}"]`);
    if (!searchResults) return;
    
    if (query.length < 2) {
        searchResults.innerHTML = '';
        return;
    }
    
    fetch(`/api/search?type=${type}&q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(searchResults, data.results, type);
        })
        .catch(error => {
            console.error('Search failed:', error);
        });
}

function displaySearchResults(container, results, type) {
    if (!results || results.length === 0) {
        container.innerHTML = '<div class="dropdown-item text-muted">Nenhum resultado encontrado</div>';
        return;
    }
    
    container.innerHTML = results.map(result => {
        return `<div class="dropdown-item" onclick="selectSearchResult('${type}', ${result.id})">
                    ${result.name || result.title}
                </div>`;
    }).join('');
}

function selectSearchResult(type, id) {
    // Handle search result selection based on type
    switch (type) {
        case 'clients':
            window.location.href = `/clients?highlight=${id}`;
            break;
        case 'receivables':
            window.location.href = `/receivables?highlight=${id}`;
            break;
        case 'payables':
            window.location.href = `/payables?highlight=${id}`;
            break;
        default:
            console.log('Selected:', type, id);
    }
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatDate(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

function formatDateTime(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR');
}

function formatCurrency(value) {
    if (value === null || value === undefined) return 'R$ 0,00';
    
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

function formatPhone(phone) {
    if (!phone) return '';
    
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 13 && cleaned.startsWith('55')) {
        const number = cleaned.substring(2);
        return `(${number.substring(0,2)}) ${number.substring(2,7)}-${number.substring(7)}`;
    } else if (cleaned.length === 11) {
        return `(${cleaned.substring(0,2)}) ${cleaned.substring(2,7)}-${cleaned.substring(7)}`;
    }
    return phone;
}

function formatDocument(document) {
    if (!document) return '';
    
    const cleaned = document.replace(/\D/g, '');
    if (cleaned.length === 11) {
        // CPF
        return `${cleaned.substring(0,3)}.${cleaned.substring(3,6)}.${cleaned.substring(6,9)}-${cleaned.substring(9)}`;
    } else if (cleaned.length === 14) {
        // CNPJ
        return `${cleaned.substring(0,2)}.${cleaned.substring(2,5)}.${cleaned.substring(5,8)}/${cleaned.substring(8,12)}-${cleaned.substring(12)}`;
    }
    return document;
}

function getPlanDisplayName(planName) {
    const planNames = {
        'basic': 'Básico',
        'premium': 'Premium',
        'enterprise': 'Enterprise'
    };
    return planNames[planName] || planName;
}

// Authentication functions
function logout() {
    if (confirm('Tem certeza que deseja sair?')) {
        showLoading();
        
        fetch('/api/logout', {
            method: 'POST'
        })
        .then(() => {
            window.location.href = '/login';
        })
        .catch(error => {
            console.error('Logout failed:', error);
            window.location.href = '/login';
        })
        .finally(() => {
            hideLoading();
        });
    }
}

function changePassword() {
    const modal = document.getElementById('changePasswordModal');
    if (modal) {
        new bootstrap.Modal(modal).show();
    }
}

// Setup change password form
document.addEventListener('DOMContentLoaded', function() {
    const changePasswordForm = document.getElementById('changePasswordForm');
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const currentPassword = document.getElementById('currentPassword').value;
            const newPassword = document.getElementById('newPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            
            if (newPassword !== confirmPassword) {
                showToast('Nova senha e confirmação não coincidem', 'error');
                return;
            }
            
            if (newPassword.length < 6) {
                showToast('Nova senha deve ter pelo menos 6 caracteres', 'error');
                return;
            }
            
            showLoading();
            
            try {
                const response = await fetch('/api/change-password', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        current_password: currentPassword,
                        new_password: newPassword
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showToast(data.message, 'success');
                    bootstrap.Modal.getInstance(document.getElementById('changePasswordModal')).hide();
                    changePasswordForm.reset();
                } else {
                    showToast(data.error || 'Erro ao alterar senha', 'error');
                }
            } catch (error) {
                showToast('Erro de conexão', 'error');
            } finally {
                hideLoading();
            }
        });
    }
});

// Auto-logout functionality
function setupAutoLogout() {
    let logoutTimer;
    const LOGOUT_TIME = 30 * 60 * 1000; // 30 minutes
    
    function resetLogoutTimer() {
        clearTimeout(logoutTimer);
        logoutTimer = setTimeout(() => {
            showToast('Sessão expirada por inatividade', 'warning');
            setTimeout(logout, 3000);
        }, LOGOUT_TIME);
    }
    
    // Reset timer on user activity
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    events.forEach(event => {
        document.addEventListener(event, resetLogoutTimer, { passive: true });
    });
    
    // Initialize timer
    resetLogoutTimer();
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + S to save forms
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        const activeForm = document.activeElement.closest('form');
        if (activeForm) {
            const submitBtn = activeForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.click();
            }
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const activeModal = document.querySelector('.modal.show');
        if (activeModal) {
            const modalInstance = bootstrap.Modal.getInstance(activeModal);
            if (modalInstance) {
                modalInstance.hide();
            }
        }
    }
});

// Page visibility API for session management
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
        // Page is visible again, check session
        checkUserSession();
    }
});

// Service Worker registration (PWA)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(err) {
                console.log('ServiceWorker registration failed: ', err);
            });
    });
}

// PWA install prompt
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    // Show install button
    const installBtn = document.getElementById('installBtn');
    if (installBtn) {
        installBtn.style.display = 'block';
        installBtn.addEventListener('click', installPWA);
    }
});

function installPWA() {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                showToast('App instalado com sucesso!', 'success');
            }
            deferredPrompt = null;
            const installBtn = document.getElementById('installBtn');
            if (installBtn) {
                installBtn.style.display = 'none';
            }
        });
    }
}

// Export functions for global use
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showToast = showToast;
window.formatDate = formatDate;
window.formatDateTime = formatDateTime;
window.formatCurrency = formatCurrency;
window.formatPhone = formatPhone;
window.formatDocument = formatDocument;
window.getPlanDisplayName = getPlanDisplayName;
window.logout = logout;
window.changePassword = changePassword;
window.installPWA = installPWA;
