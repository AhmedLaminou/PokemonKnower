/**
 * Pokémon Knower - Main JavaScript
 * Handles search, scanner, camera, and UI interactions
 */

document.addEventListener('DOMContentLoaded', () => {
    // ==================== Mobile Navigation ====================
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.getElementById('navLinks');
    
    if (mobileMenuBtn && navLinks) {
        mobileMenuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('show');
            mobileMenuBtn.classList.toggle('active');
        });
    }

    // ==================== Search Functionality ====================
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const filterToggle = document.getElementById('filterToggle');
    const filtersPanel = document.getElementById('filtersPanel');
    const applyFilters = document.getElementById('applyFilters');
    const resetFilters = document.getElementById('resetFilters');
    const searchResults = document.getElementById('searchResults');
    const searchPagination = document.getElementById('searchPagination');

    let currentPage = 1;

    // Toggle filters panel
    if (filterToggle && filtersPanel) {
        filterToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            filtersPanel.classList.toggle('show');
        });

        document.addEventListener('click', (e) => {
            if (!filtersPanel.contains(e.target) && e.target !== filterToggle) {
                filtersPanel.classList.remove('show');
            }
        });
    }

    // Search function
    async function performSearch(page = 1) {
        if (!searchResults) return;
        
        const query = searchInput ? searchInput.value.trim() : '';
        const type = document.getElementById('typeFilter')?.value || '';
        const minAttack = document.getElementById('minAttack')?.value || '';
        const minDefense = document.getElementById('minDefense')?.value || '';
        const minStamina = document.getElementById('minStamina')?.value || '';

        const params = new URLSearchParams();
        if (query) params.append('q', query);
        if (type) params.append('type', type);
        if (minAttack) params.append('minAttack', minAttack);
        if (minDefense) params.append('minDefense', minDefense);
        if (minStamina) params.append('minStamina', minStamina);
        params.append('page', page);

        searchResults.innerHTML = '<div class="loader"><div class="pokeball-loader"></div></div>';

        try {
            const response = await fetch(`/search?${params.toString()}`);
            const data = await response.json();
            
            if (data.error) {
                searchResults.innerHTML = `<p class="error-message">${data.error}</p>`;
                return;
            }

            displaySearchResults(data.results);
            displayPagination(data.pagination);
            currentPage = page;
        } catch (error) {
            console.error('Search error:', error);
            searchResults.innerHTML = '<p class="error-message">Failed to search. Please try again.</p>';
        }
    }

    // Display search results as cards
    function displaySearchResults(results) {
        if (!searchResults) return;
        
        if (!results || results.length === 0) {
            searchResults.innerHTML = '<p class="no-results">No Pokémon found matching your criteria.</p>';
            return;
        }

        searchResults.innerHTML = results.map(pokemon => `
            <a href="/pokemon/${pokemon.name}" class="pokemon-card" data-type="${pokemon.main_type?.toLowerCase() || ''}">
                <div class="card-header">
                    <span class="card-number">#${String(pokemon.number).padStart(3, '0')}</span>
                    <div class="card-types">
                        <span class="type-badge ${pokemon.main_type?.toLowerCase()}">${pokemon.main_type}</span>
                        ${pokemon.secondary_type ? `<span class="type-badge ${pokemon.secondary_type.toLowerCase()}">${pokemon.secondary_type}</span>` : ''}
                    </div>
                </div>
                <div class="card-image">
                    <img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${pokemon.number}.png" 
                         alt="${pokemon.name}"
                         loading="lazy"
                         onerror="this.src='/static/images/pokeball.png'">
                </div>
                <div class="card-body">
                    <h3 class="card-name">${pokemon.name}</h3>
                    <p class="card-category">${pokemon.category || ''}</p>
                    <div class="card-stats">
                        <div class="stat-item">
                            <span class="stat-label">ATK</span>
                            <span class="stat-value">${pokemon.attack}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">DEF</span>
                            <span class="stat-value">${pokemon.defense}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">HP</span>
                            <span class="stat-value">${pokemon.stamina}</span>
                        </div>
                    </div>
                </div>
            </a>
        `).join('');
    }

    // Display pagination
    function displayPagination(pagination) {
        if (!searchPagination || !pagination || pagination.total_pages <= 1) {
            if (searchPagination) searchPagination.innerHTML = '';
            return;
        }

        let html = '';
        
        if (pagination.has_prev) {
            html += `<button class="page-btn" data-page="${pagination.page - 1}"><i class="fas fa-chevron-left"></i></button>`;
        }

        for (let i = 1; i <= pagination.total_pages; i++) {
            if (i === 1 || i === pagination.total_pages || (i >= pagination.page - 2 && i <= pagination.page + 2)) {
                html += `<button class="page-btn ${i === pagination.page ? 'active' : ''}" data-page="${i}">${i}</button>`;
            } else if (i === pagination.page - 3 || i === pagination.page + 3) {
                html += '<span class="page-ellipsis">...</span>';
            }
        }

        if (pagination.has_next) {
            html += `<button class="page-btn" data-page="${pagination.page + 1}"><i class="fas fa-chevron-right"></i></button>`;
        }

        searchPagination.innerHTML = html;

        // Add click handlers
        searchPagination.querySelectorAll('.page-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                performSearch(parseInt(btn.dataset.page));
                searchResults.scrollIntoView({ behavior: 'smooth' });
            });
        });
    }

    // Event listeners
    if (searchBtn) {
        searchBtn.addEventListener('click', () => performSearch(1));
    }

    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') performSearch(1);
        });
    }

    if (applyFilters) {
        applyFilters.addEventListener('click', () => {
            performSearch(1);
            filtersPanel?.classList.remove('show');
        });
    }

    if (resetFilters) {
        resetFilters.addEventListener('click', () => {
            document.getElementById('typeFilter').value = '';
            document.getElementById('minAttack').value = '';
            document.getElementById('minDefense').value = '';
            document.getElementById('minStamina').value = '';
            if (searchInput) searchInput.value = '';
            searchResults.innerHTML = '';
            searchPagination.innerHTML = '';
        });
    }

    // ==================== Scanner Functionality ====================
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    const uploadPreview = document.getElementById('uploadPreview');
    const resultsPanel = document.getElementById('resultsPanel');
    const scanBtn = document.getElementById('scanBtn');
    const retryBtn = document.getElementById('retryBtn');
    const cameraBtn = document.getElementById('cameraBtn');

    let currentFile = null;

    if (uploadZone && fileInput) {
        // Click to upload
        uploadZone.addEventListener('click', () => fileInput.click());

        // Drag and drop
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
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
            alert('Please upload a valid image file.');
            return;
        }

        currentFile = file;

        const reader = new FileReader();
        reader.onload = (e) => {
            if (uploadPreview) {
                uploadPreview.src = e.target.result;
                uploadZone.classList.add('has-image');
            }
            if (scanBtn) scanBtn.disabled = false;
            if (retryBtn) retryBtn.style.display = 'inline-flex';
            
            // Reset results
            if (resultsPanel) resultsPanel.classList.remove('has-results');
        };
        reader.readAsDataURL(file);
    }

    // Scan button
    if (scanBtn) {
        scanBtn.addEventListener('click', async () => {
            if (!currentFile) return;

            scanBtn.disabled = true;
            scanBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';

            const formData = new FormData();
            formData.append('file', currentFile);

            try {
                const response = await fetch('/predict', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    displayScanResults(data);
                }
            } catch (error) {
                console.error('Scan error:', error);
                alert('Failed to identify Pokémon. Please try again.');
            } finally {
                scanBtn.disabled = false;
                scanBtn.innerHTML = '<i class="fas fa-search"></i> Identify Pokémon';
            }
        });
    }

    // Retry button
    if (retryBtn) {
        retryBtn.addEventListener('click', () => {
            currentFile = null;
            if (uploadPreview) uploadPreview.src = '';
            if (uploadZone) uploadZone.classList.remove('has-image');
            if (scanBtn) scanBtn.disabled = true;
            if (resultsPanel) resultsPanel.classList.remove('has-results');
            retryBtn.style.display = 'none';
            if (fileInput) fileInput.value = '';
        });
    }

    // Display scan results
    function displayScanResults(data) {
        const resultName = document.getElementById('resultName');
        const resultImage = document.getElementById('resultImage');
        const resultTypes = document.getElementById('resultTypes');
        const resultConfidence = document.getElementById('resultConfidence');
        const topMatches = document.getElementById('topMatches');
        const viewDetailsBtn = document.getElementById('viewDetailsBtn');

        if (resultName) resultName.textContent = data.name;
        
        if (resultImage && data.pokemon) {
            resultImage.src = `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${data.pokemon.number}.png`;
        }

        if (resultTypes && data.pokemon) {
            let typesHtml = `<span class="type-badge ${data.pokemon.main_type?.toLowerCase()}">${data.pokemon.main_type}</span>`;
            if (data.pokemon.secondary_type) {
                typesHtml += `<span class="type-badge ${data.pokemon.secondary_type.toLowerCase()}">${data.pokemon.secondary_type}</span>`;
            }
            resultTypes.innerHTML = typesHtml;
        }

        if (resultConfidence) {
            const confidence = data.confidence;
            resultConfidence.textContent = `${confidence.toFixed(1)}% Confidence`;
            resultConfidence.className = 'result-confidence';
            if (confidence >= 85) {
                resultConfidence.classList.add('high');
            } else if (confidence >= 65) {
                resultConfidence.classList.add('medium');
            } else {
                resultConfidence.classList.add('low');
            }
        }

        if (topMatches && data.top_3) {
            topMatches.innerHTML = data.top_3.map(match => `
                <div class="match-item">
                    <span class="match-name">${match.name}</span>
                    <div class="match-bar">
                        <div class="match-bar-fill" style="width: ${match.confidence}%"></div>
                    </div>
                    <span class="match-percent">${match.confidence.toFixed(1)}%</span>
                </div>
            `).join('');
        }

        if (viewDetailsBtn) {
            viewDetailsBtn.href = `/pokemon/${data.name}`;
            viewDetailsBtn.style.display = 'inline-flex';
        }

        if (resultsPanel) resultsPanel.classList.add('has-results');
    }

    // ==================== Camera Functionality ====================
    const cameraModal = document.getElementById('cameraModal');
    const closeCameraModal = document.getElementById('closeCameraModal');
    const cameraFeed = document.getElementById('cameraFeed');
    const cameraCanvas = document.getElementById('cameraCanvas');
    const captureBtn = document.getElementById('captureBtn');

    let cameraStream = null;

    if (cameraBtn) {
        cameraBtn.addEventListener('click', async () => {
            if (!cameraModal) return;

            try {
                cameraStream = await navigator.mediaDevices.getUserMedia({ 
                    video: { facingMode: 'environment' } 
                });
                cameraFeed.srcObject = cameraStream;
                cameraModal.style.display = 'flex';
            } catch (error) {
                console.error('Camera error:', error);
                alert('Unable to access camera. Please check permissions.');
            }
        });
    }

    if (closeCameraModal) {
        closeCameraModal.addEventListener('click', () => {
            closeCamera();
        });
    }

    if (cameraModal) {
        cameraModal.addEventListener('click', (e) => {
            if (e.target === cameraModal) {
                closeCamera();
            }
        });
    }

    function closeCamera() {
        if (cameraStream) {
            cameraStream.getTracks().forEach(track => track.stop());
            cameraStream = null;
        }
        if (cameraModal) cameraModal.style.display = 'none';
    }

    if (captureBtn) {
        captureBtn.addEventListener('click', () => {
            if (!cameraFeed || !cameraCanvas) return;

            const ctx = cameraCanvas.getContext('2d');
            cameraCanvas.width = cameraFeed.videoWidth;
            cameraCanvas.height = cameraFeed.videoHeight;
            ctx.drawImage(cameraFeed, 0, 0);

            cameraCanvas.toBlob((blob) => {
                const file = new File([blob], 'camera_capture.png', { type: 'image/png' });
                handleFile(file);
                closeCamera();
            }, 'image/png');
        });
    }

    // ==================== Keyboard Navigation ====================
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeCamera();
            if (filtersPanel) filtersPanel.classList.remove('show');
        }
    });
});
