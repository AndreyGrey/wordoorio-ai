/**
 * CustomDropdown Component
 *
 * Reusable dropdown component with:
 * - Custom trigger button
 * - Dropdown menu with options
 * - Active state management
 * - Keyboard navigation support
 *
 * @version 1.0.0
 */

/**
 * Create dropdown HTML
 * @param {Object} config - Dropdown configuration
 * @returns {string} HTML string
 */
function createCustomDropdown(config) {
    const {
        id,
        options = [],
        defaultValue = null,
        placeholder = 'Выбрать',
        className = ''
    } = config;

    // Find selected option
    const selectedOption = options.find(opt => opt.value === defaultValue) || options[0];
    const selectedText = selectedOption ? selectedOption.label : placeholder;

    // Build options HTML
    const optionsHtml = options.map(opt => `
        <div class="dropdown-item ${opt.value === defaultValue ? 'active' : ''}" data-value="${escapeAttr(opt.value)}">
            ${escapeHtml(opt.label)}
        </div>
    `).join('');

    return `
        <div class="custom-dropdown ${className}" id="${id}" data-value="${escapeAttr(defaultValue || '')}">
            <button class="dropdown-trigger" type="button">
                <span class="dropdown-text">${escapeHtml(selectedText)}</span>
                <svg class="dropdown-arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M6 9l6 6 6-6"/>
                </svg>
            </button>
            <div class="dropdown-menu">
                ${optionsHtml}
            </div>
        </div>
    `;
}

/**
 * Escape HTML special characters
 * @param {string} str - String to escape
 * @returns {string} Escaped string
 */
function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/**
 * Escape attribute value
 * @param {string} str - String to escape
 * @returns {string} Escaped string
 */
function escapeAttr(str) {
    if (!str) return '';
    return String(str).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

/**
 * Initialize a single dropdown
 * @param {HTMLElement|string} dropdown - Dropdown element or ID
 * @param {Object} options - Options
 * @returns {Object} Dropdown instance
 */
function initDropdown(dropdown, options = {}) {
    const el = typeof dropdown === 'string'
        ? document.getElementById(dropdown)
        : dropdown;

    if (!el) {
        console.warn('Dropdown element not found');
        return null;
    }

    const { onChange } = options;
    const trigger = el.querySelector('.dropdown-trigger');
    const textEl = el.querySelector('.dropdown-text');
    const items = el.querySelectorAll('.dropdown-item');

    // Toggle dropdown
    trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        closeAllDropdowns();
        el.classList.toggle('open');
    });

    // Handle item selection
    items.forEach(item => {
        item.addEventListener('click', () => {
            const value = item.dataset.value;
            const label = item.textContent.trim();

            // Update display
            textEl.textContent = label;
            el.dataset.value = value;

            // Update active state
            items.forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            // Close dropdown
            el.classList.remove('open');

            // Callback
            if (onChange) {
                onChange(value, label, el);
            }
        });
    });

    // Keyboard navigation
    el.addEventListener('keydown', (e) => {
        if (!el.classList.contains('open')) return;

        const activeItem = el.querySelector('.dropdown-item.active');
        const allItems = Array.from(items);
        const currentIndex = allItems.indexOf(activeItem);

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            const nextIndex = (currentIndex + 1) % allItems.length;
            allItems[nextIndex].focus();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            const prevIndex = (currentIndex - 1 + allItems.length) % allItems.length;
            allItems[prevIndex].focus();
        } else if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            if (document.activeElement.classList.contains('dropdown-item')) {
                document.activeElement.click();
            }
        } else if (e.key === 'Escape') {
            el.classList.remove('open');
            trigger.focus();
        }
    });

    return {
        element: el,
        getValue: () => el.dataset.value,
        setValue: (value) => {
            const item = el.querySelector(`.dropdown-item[data-value="${value}"]`);
            if (item) {
                item.click();
            }
        },
        close: () => el.classList.remove('open'),
        open: () => el.classList.add('open')
    };
}

/**
 * Close all open dropdowns
 */
function closeAllDropdowns() {
    document.querySelectorAll('.custom-dropdown.open').forEach(d => {
        d.classList.remove('open');
    });
}

/**
 * Setup global click handler to close dropdowns
 */
function setupDropdownGlobalClose() {
    document.addEventListener('click', closeAllDropdowns);
}

/**
 * Get CustomDropdown styles
 * @returns {string} CSS styles
 */
function getCustomDropdownStyles() {
    return `
        /* ===== CUSTOM DROPDOWN v1.0 ===== */
        .custom-dropdown {
            position: relative;
            min-width: 140px;
        }

        .dropdown-trigger {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            padding: 12px 16px;
            border: none;
            border-radius: var(--radius-md, 12px);
            font-family: inherit;
            font-size: 0.875rem;
            font-weight: 600;
            background: var(--color-surface, #ffffff);
            color: var(--color-text, #1a202c);
            cursor: pointer;
            box-shadow: var(--shadow-sm, 0 1px 3px rgba(0,0,0,0.08));
            width: 100%;
            text-align: left;
            transition: all 0.2s ease;
        }

        .dropdown-trigger:hover {
            box-shadow: var(--shadow-md, 0 4px 12px rgba(0,0,0,0.1));
        }

        .dropdown-trigger:focus {
            outline: none;
            box-shadow: 0 0 0 3px rgba(57, 160, 179, 0.2);
        }

        .dropdown-text {
            flex: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .dropdown-arrow {
            flex-shrink: 0;
            color: var(--color-text-muted, #718096);
            transition: transform 0.2s ease;
        }

        .custom-dropdown.open .dropdown-arrow {
            transform: rotate(180deg);
        }

        /* Dropdown menu */
        .dropdown-menu {
            position: absolute;
            top: calc(100% + 6px);
            left: 0;
            right: 0;
            background: var(--color-surface, #ffffff);
            border-radius: var(--radius-md, 12px);
            box-shadow: var(--shadow-lg, 0 8px 24px rgba(0,0,0,0.12));
            opacity: 0;
            visibility: hidden;
            transform: translateY(-8px);
            transition: all 0.2s ease;
            z-index: var(--z-dropdown, 100);
            overflow: hidden;
            max-height: 300px;
            overflow-y: auto;
        }

        .custom-dropdown.open .dropdown-menu {
            opacity: 1;
            visibility: visible;
            transform: translateY(0);
        }

        /* Dropdown items */
        .dropdown-item {
            padding: 10px 16px;
            font-family: inherit;
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--color-text-secondary, #4a5568);
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .dropdown-item:hover {
            background: var(--color-surface-hover, #f7fafc);
            color: var(--color-text, #1a202c);
        }

        .dropdown-item:focus {
            outline: none;
            background: var(--color-surface-hover, #f7fafc);
        }

        .dropdown-item.active {
            background: rgba(57, 160, 179, 0.1);
            color: var(--color-secondary-dark, #1B7A94);
            font-weight: 600;
        }

        /* Scrollbar styling */
        .dropdown-menu::-webkit-scrollbar {
            width: 6px;
        }

        .dropdown-menu::-webkit-scrollbar-track {
            background: transparent;
        }

        .dropdown-menu::-webkit-scrollbar-thumb {
            background: var(--color-border, #e2e8f0);
            border-radius: 3px;
        }

        .dropdown-menu::-webkit-scrollbar-thumb:hover {
            background: var(--color-text-light, #a0aec0);
        }

        /* ===== RESPONSIVE ===== */
        @media (max-width: 640px) {
            .dropdown-trigger {
                padding: 10px 14px;
                font-size: 0.8125rem;
            }

            .dropdown-item {
                padding: 10px 14px;
                font-size: 0.8125rem;
            }
        }
    `;
}

/**
 * Initialize CustomDropdown styles
 */
function initCustomDropdownStyles() {
    if (!document.getElementById('custom-dropdown-styles')) {
        const styleEl = document.createElement('style');
        styleEl.id = 'custom-dropdown-styles';
        styleEl.innerHTML = getCustomDropdownStyles();
        document.head.appendChild(styleEl);
    }
}

/**
 * Initialize all dropdowns on page
 * @param {Object} options - Options for all dropdowns
 */
function initAllDropdowns(options = {}) {
    // Initialize styles
    initCustomDropdownStyles();

    // Setup global close handler
    setupDropdownGlobalClose();

    // Initialize all dropdowns
    const dropdowns = document.querySelectorAll('.custom-dropdown');
    const instances = [];

    dropdowns.forEach(dropdown => {
        const instance = initDropdown(dropdown, options);
        if (instance) {
            instances.push(instance);
        }
    });

    return instances;
}

// Auto-initialize styles on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    initCustomDropdownStyles();
    setupDropdownGlobalClose();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createCustomDropdown,
        initDropdown,
        initAllDropdowns,
        getCustomDropdownStyles,
        initCustomDropdownStyles,
        closeAllDropdowns
    };
}
