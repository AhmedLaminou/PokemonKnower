document.addEventListener('DOMContentLoaded', () => {
    // Search state
    let currentPage = 1;
    let currentQuery = '';
    let currentFilters = {};
    let currentFile = null;
    
    // Elements - with null checks for pages that don't have all elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const imagePreview = document.getElementById('image-preview');
    const uploadPlaceholder = document.querySelector('#drop-zone .upload-placeholder');
    const predictBtn = document.getElementById('predict-btn');
    
    // Result Elements
    const infoScreenInitialState = document.querySelector('.info-screen .initial-state');
    const resultState = document.querySelector('.result-state');
    const loader = document.getElementById('loader');
    const pokemonName = document.getElementById('pokemon-name');
    const confidenceBadge = document.getElementById('confidence-badge');
    const statsList = document.getElementById('stats-list');
    const scanLine = document.querySelector('.scan-line');

    // --- File Handling ---
    
    // Only set up file handling if elements exist (index page)
    if (dropZone && fileInput) {
        // Click to upload
        dropZone.addEventListener('click', () => fileInput.click());

        // Drag & Drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                handleFile(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                handleFile(e.target.files[0]);
            }
        });
    }

    function handleFile(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please upload a valid image file!');
            return;
        }

        currentFile = file;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            if (imagePreview) {
                imagePreview.src = e.target.result;
                imagePreview.style.display = 'block';
            }
            if (uploadPlaceholder) {
                uploadPlaceholder.style.display = 'none';
            }
            if (predictBtn) {
                predictBtn.disabled = false;
            }
            resetPokedex();
        };
        reader.readAsDataURL(file);
    }

    function resetPokedex() {
        if (infoScreenInitialState) infoScreenInitialState.style.display = 'block';
        if (resultState) resultState.style.display = 'none';
        if (resultState) resultState.classList.remove('show');
        if (loader) loader.style.display = 'none';
        if (scanLine) scanLine.style.display = 'none';
    }

    // --- Prediction Logic ---
    if (predictBtn) {
        predictBtn.addEventListener('click', async () => {
            if (!currentFile) return;

            // UI Updates
            predictBtn.disabled = true;
            predictBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> SCANNING...';
            if (infoScreenInitialState) infoScreenInitialState.style.display = 'none';
            if (resultState) {
                resultState.style.display = 'none';
                resultState.classList.remove('show');
            }
            if (loader) loader.style.display = 'block';
            if (scanLine) scanLine.style.display = 'block';

            const formData = new FormData();
            formData.append('file', currentFile);

            try {
                // Simulate a small delay for the "Scanning" effect
                await new Promise(r => setTimeout(r, 1200));

                const response = await fetch('/predict', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.error) {
                    alert('Error: ' + data.error);
                    resetPokedex();
                } else {
                    showResults(data);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Communication Error with Pokédex Server.');
                resetPokedex();
            } finally {
                predictBtn.disabled = false;
                predictBtn.innerHTML = '<i class="fas fa-search"></i> IDENTIFY POKÉMON';
                if (loader) loader.style.display = 'none';
                if (scanLine) scanLine.style.display = 'none';
            }
        });
    }

    function showResults(data) {
        if (!pokemonName || !confidenceBadge || !statsList) return;
        
        // Basic Info
        pokemonName.textContent = data.class.toUpperCase();
        
        // Confidence is already 0-100 from backend
        const confidence = data.confidence;
        confidenceBadge.textContent = `Confidence: ${confidence.toFixed(1)}%`;
        
        // Color code confidence with gradients
        if (confidence > 85) {
            confidenceBadge.style.background = 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)';
        } else if (confidence > 65) {
            confidenceBadge.style.background = 'linear-gradient(135deg, #ff9800 0%, #e65100 100%)';
        } else {
            confidenceBadge.style.background = 'linear-gradient(135deg, #f44336 0%, #c62828 100%)';
        }

        // Top 3 Matches
        statsList.innerHTML = '';
        if (data.top_3 && data.top_3.length > 0) {
            data.top_3.forEach((stat, index) => {
                const li = document.createElement('li');
                // Confidence is already 0-100 from backend
                const percentage = stat.confidence.toFixed(1);
                li.innerHTML = `
                    <span>${stat.class}</span>
                    <span>${percentage}%</span>
                `;
                // Add slight delay for animation effect
                li.style.animationDelay = `${index * 0.1}s`;
                statsList.appendChild(li);
            });
        }

        // --- Stats Card Population (optional, may not exist) ---
        const statsCard = document.getElementById('stats-card');
        if (statsCard && data.stats && Object.keys(data.stats).length > 0) {
            const statsName = document.getElementById('stats-name');
            const pokedexDesc = document.getElementById('pokedex-desc');
            const statsHeight = document.getElementById('stats-height');
            const statsWeight = document.getElementById('stats-weight');
            
            if (statsName) statsName.textContent = data.class;
            if (pokedexDesc) pokedexDesc.textContent = data.stats.desc || '';
            if (statsHeight) statsHeight.textContent = data.stats.height || '';
            if (statsWeight) statsWeight.textContent = data.stats.weight || '';

            // Type Badges
            const typeContainer = document.getElementById('type-badges');
            if (typeContainer) {
                typeContainer.innerHTML = '';
                
                const mainType = data.stats.type;
                if (mainType && mainType !== 'Unknown') {
                    const badge = document.createElement('span');
                    badge.className = `type-badge-item type-${mainType.toLowerCase()}`;
                    badge.textContent = mainType;
                    typeContainer.appendChild(badge);
                }

                const secType = data.stats.secondary_type;
                if (secType && secType !== '') {
                    const badge = document.createElement('span');
                    badge.className = `type-badge-item type-${secType.toLowerCase()}`;
                    badge.textContent = secType;
                    typeContainer.appendChild(badge);
                }
            }

            // Progress Bars (Normalize to ~300 max for visual)
            const updateBar = (id, valId, value) => {
                const bar = document.getElementById(id);
                const valDisplay = document.getElementById(valId);
                if (bar && valDisplay) {
                    valDisplay.textContent = value || 0;
                    const width = Math.min((value / 300) * 100, 100);
                    bar.style.width = `${width}%`;
                }
            };

            updateBar('bar-atk', 'val-atk', data.stats.attack);
            updateBar('bar-def', 'val-def', data.stats.defense);
            updateBar('bar-sta', 'val-sta', data.stats.stamina);

            statsCard.style.display = 'block';
        } else if (statsCard) {
            statsCard.style.display = 'none';
        }

        // Show results with animation
        if (resultState) {
            resultState.style.display = 'block';
            resultState.classList.add('show');
        }
        if (infoScreenInitialState) {
            infoScreenInitialState.style.display = 'none';
        }
    }

    // --- Slider Logic (Optional - element may not exist) ---
    const sliderTrack = document.getElementById('slider-track');
    if (sliderTrack) {
        sliderTrack.addEventListener('mouseenter', () => {
            sliderTrack.style.animationPlayState = 'paused';
        });
        sliderTrack.addEventListener('mouseleave', () => {
            sliderTrack.style.animationPlayState = 'running';
        });
    }

    // --- Search Elements ---
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const advancedSearchToggle = document.getElementById('advanced-search-toggle');
    const advancedSearchPanel = document.getElementById('advanced-search-panel');
    const applyFiltersBtn = document.getElementById('apply-filters');
    const resetFiltersBtn = document.getElementById('reset-filters');
    const searchResults = document.getElementById('search-results');
    const pagination = document.getElementById('pagination');
    const modal = document.getElementById('pokemon-modal');
    const closeModal = document.querySelector('.close-modal');

    // Toggle Advanced Search Panel
    if (advancedSearchToggle && advancedSearchPanel) {
        advancedSearchToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            advancedSearchPanel.classList.toggle('show');
        });

        // Close advanced search when clicking outside
        document.addEventListener('click', (e) => {
            if (!advancedSearchPanel.contains(e.target) && e.target !== advancedSearchToggle) {
                advancedSearchPanel.classList.remove('show');
            }
        });
    }

    // Close Modal
    if (closeModal && modal) {
        closeModal.onclick = () => modal.style.display = "none";
    }
    
    window.onclick = (event) => {
        if (modal && event.target == modal) modal.style.display = "none";
    }

    // Search event listeners
    if (searchBtn) {
        searchBtn.addEventListener('click', () => performSearch());
    }
    
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') performSearch();
        });
    }

    // Filter event listeners
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', () => {
            performSearch();
            if (advancedSearchPanel) advancedSearchPanel.classList.remove('show');
        });
    }

    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', resetFilters);
    }

    // Reset all filters
    function resetFilters() {
        const typeFilter = document.getElementById('type-filter');
        const minWeight = document.getElementById('min-weight');
        const maxWeight = document.getElementById('max-weight');
        const minHeight = document.getElementById('min-height');
        const maxHeight = document.getElementById('max-height');
        const minAttack = document.getElementById('min-attack');
        const minDefense = document.getElementById('min-defense');
        const minStamina = document.getElementById('min-stamina');
        
        if (typeFilter) typeFilter.value = '';
        if (minWeight) minWeight.value = '';
        if (maxWeight) maxWeight.value = '';
        if (minHeight) minHeight.value = '';
        if (maxHeight) maxHeight.value = '';
        if (minAttack) minAttack.value = '0';
        if (minDefense) minDefense.value = '0';
        if (minStamina) minStamina.value = '0';
        
        // Reset current filters and perform search
        currentFilters = {};
        performSearch();
    }

    // Get current filter values
    function getFilters() {
        const typeFilter = document.getElementById('type-filter');
        const minWeight = document.getElementById('min-weight');
        const maxWeight = document.getElementById('max-weight');
        const minHeight = document.getElementById('min-height');
        const maxHeight = document.getElementById('max-height');
        const minAttack = document.getElementById('min-attack');
        const minDefense = document.getElementById('min-defense');
        const minStamina = document.getElementById('min-stamina');
        
        return {
            type: typeFilter ? typeFilter.value : '',
            min_weight: minWeight ? (minWeight.value || 0) : 0,
            max_weight: maxWeight ? (maxWeight.value || '') : '',
            min_height: minHeight ? (minHeight.value || 0) : 0,
            max_height: maxHeight ? (maxHeight.value || '') : '',
            min_attack: minAttack ? (minAttack.value || 0) : 0,
            min_defense: minDefense ? (minDefense.value || 0) : 0,
            min_stamina: minStamina ? (minStamina.value || 0) : 0
        };
    }

    // Build query string from filters
    function buildQueryString(filters) {
        const params = new URLSearchParams();
        
        // Add search query if exists
        if (currentQuery) {
            params.append('q', currentQuery);
        }
        
        // Add filters if they have values
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== '' && value !== 0) {
                params.append(key, value);
            }
        });
        
        // Add pagination
        params.append('page', currentPage);
        
        return params.toString();
    }

    // Perform search with current filters
    async function performSearch() {
        currentQuery = searchInput.value.trim();
        currentFilters = getFilters();
        currentPage = 1; // Reset to first page on new search
        
        await fetchSearchResults();
    }

    // Fetch search results from the server
    async function fetchSearchResults() {
        const queryString = buildQueryString(currentFilters);
        
        // Show loading state
        searchResults.innerHTML = '<div class="loading">Searching for Pokémon...</div>';
        searchResults.style.opacity = '1';
        searchResults.style.transform = 'translateY(0)';
        
        try {
            const response = await fetch(`/search?${queryString}`);
            const data = await response.json();
            
            if (data.error) {
                searchResults.innerHTML = `<div class="error">${data.error}</div>`;
            } else {
                displaySearchResults(data);
            }
        } catch (error) {
            console.error('Search error:', error);
            searchResults.innerHTML = '<div class="error">Failed to fetch search results. Please try again.</div>';
        }
    }

    // Display search results in the UI
    function displaySearchResults(data) {
        let results = [];
        let paginationData = { page: 1, total_pages: 1 };
        
        // Handle both direct results array and object with results/pagination structure
        if (Array.isArray(data)) {
            results = data;
        } else if (data && data.results) {
            results = data.results;
            paginationData = data.pagination || { page: 1, total_pages: 1 };
        }
        
        if (!results || results.length === 0) {
            searchResults.innerHTML = '<div class="no-results">No Pokémon found matching your criteria.</div>';
            pagination.innerHTML = '';
            return;
        }
        
        // Create results grid
        let html = '<div class="search-results-grid">';
        
        results.forEach(pokemon => {
            const types = [];
            if (pokemon.main_type && pokemon.main_type !== 'Unknown') {
                types.push(pokemon.main_type);
            }
            if (pokemon.secondary_type && pokemon.secondary_type !== '') {
                types.push(pokemon.secondary_type);
            }
            
            // Get pokemon number from name for image lookup
            let pokemonNumber = pokemon.number || '1';
            
            html += `
                <div class="pokemon-card" data-name="${pokemon.name.toLowerCase()}">
                    <div class="pokemon-image">
                        <img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${pokemonNumber}.png" 
                             alt="${pokemon.name}" 
                             onerror="this.onerror=null; this.src='/static/images/pokeball.png'"
                        >
                    </div>
                    <div class="pokemon-details">
                        <h3 class="pokemon-name">${pokemon.name}</h3>
                        <div class="pokemon-types">
                            ${types.map(type => `<span class="type-badge-item type-${type.toLowerCase()}">${type}</span>`).join('')}
                        </div>
                        <div class="pokemon-stats">
                            <div class="stat">
                                <span class="stat-label">ATK</span>
                                <div class="stat-bar">
                                    <div class="stat-fill" style="width: ${(pokemon.attack / 200) * 100}%"></div>
                                </div>
                                <span class="stat-value">${pokemon.attack}</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">DEF</span>
                                <div class="stat-bar">
                                    <div class="stat-fill" style="width: ${(pokemon.defense / 200) * 100}%"></div>
                                </div>
                                <span class="stat-value">${pokemon.defense}</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        searchResults.innerHTML = html;
        searchResults.classList.add('visible');
        
        // Add click handlers to pokemon cards
        document.querySelectorAll('.pokemon-card').forEach(card => {
            card.addEventListener('click', () => {
                const pokemonName = card.dataset.name;
                // Navigate to pokemon details page
                window.location.href = `/pokemon/${pokemonName}`;
            });
        });
        
        // Update pagination
        updatePagination(paginationData);
    }
    
    // Update pagination controls
    function updatePagination(paginationData) {
        const { page, total_pages } = paginationData;
        
        if (total_pages <= 1) {
            pagination.innerHTML = '';
            return;
        }
        
        let html = '';
        
        // Previous button
        html += `<button class="page-btn" ${page === 1 ? 'disabled' : ''} data-page="${page - 1}">
                    <i class="fas fa-chevron-left"></i>
                 </button>`;
        
        // Page numbers
        const maxVisiblePages = 5;
        let startPage = Math.max(1, page - Math.floor(maxVisiblePages / 2));
        let endPage = startPage + maxVisiblePages - 1;
        
        if (endPage > total_pages) {
            endPage = total_pages;
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }
        
        // First page
        if (startPage > 1) {
            html += `<button class="page-btn" data-page="1">1</button>`;
            if (startPage > 2) {
                html += '<span class="page-ellipsis">...</span>';
            }
        }
        
        // Page numbers
        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="page-btn ${i === page ? 'active' : ''}" data-page="${i}">${i}</button>`;
        }
        
        // Last page
        if (endPage < total_pages) {
            if (endPage < total_pages - 1) {
                html += '<span class="page-ellipsis">...</span>';
            }
            html += `<button class="page-btn" data-page="${total_pages}">${total_pages}</button>`;
        }
        
        // Next button
        html += `<button class="page-btn" ${page === total_pages ? 'disabled' : ''} data-page="${page + 1}">
                    <i class="fas fa-chevron-right"></i>
                 </button>`;
        
        pagination.innerHTML = html;
        
        // Add event listeners to pagination buttons
        document.querySelectorAll('.page-btn:not(.disabled)').forEach(btn => {
            btn.addEventListener('click', () => {
                const newPage = parseInt(btn.dataset.page);
                if (newPage !== page) {
                    currentPage = newPage;
                    fetchSearchResults();
                    // Scroll to top of results
                    searchResults.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    }
    
    // Fetch detailed information for a specific Pokemon
    async function fetchPokemonDetails(name) {
        try {
            const response = await fetch(`/search?q=${encodeURIComponent(name)}`);
            const data = await response.json();
            
            if (data.error) {
                alert(data.error);
            } else {
                showModal(data);
            }
        } catch (error) {
            console.error('Error fetching Pokemon details:', error);
            alert('Failed to fetch Pokemon details. Please try again.');
        }
    }

    function showModal(data) {
        // Populate Modal
        document.getElementById('modal-name').textContent = data.class;
        document.getElementById('modal-desc').textContent = data.stats.desc;
        document.getElementById('modal-height').textContent = data.stats.height;
        document.getElementById('modal-weight').textContent = data.stats.weight;
        
        // Image
        const img = document.getElementById('modal-img');
        // Try to find specific image or use default
        // For now, using default 1.jpeg as requested, or maybe we can try to fetch from pokeapi in future
        img.src = '/static/images/1.jpeg'; 

        // Types
        const typeContainer = document.getElementById('modal-types');
        typeContainer.innerHTML = '';
        if (data.stats.type && data.stats.type !== 'Unknown') {
            const badge = document.createElement('span');
            badge.className = `type-badge-item type-${data.stats.type.toLowerCase()}`;
            badge.textContent = data.stats.type;
            typeContainer.appendChild(badge);
        }
        if (data.stats.secondary_type) {
            const badge = document.createElement('span');
            badge.className = `type-badge-item type-${data.stats.secondary_type.toLowerCase()}`;
            badge.textContent = data.stats.secondary_type;
            typeContainer.appendChild(badge);
        }

        // Stats
        const updateBar = (id, valId, value) => {
            const bar = document.getElementById(id);
            const valDisplay = document.getElementById(valId);
            valDisplay.textContent = value;
            const width = Math.min((value / 300) * 100, 100);
            bar.style.width = `${width}%`;
        };

        updateBar('modal-atk', 'modal-val-atk', data.stats.attack);
        updateBar('modal-def', 'modal-val-def', data.stats.defense);
        updateBar('modal-sta', 'modal-val-sta', data.stats.stamina);

        // Show Modal
        modal.style.display = "block";
    }
});
