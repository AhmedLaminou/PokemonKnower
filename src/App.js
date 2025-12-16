import React from 'react';
import './App.css';

const App = () => {
  const [searchResults, setSearchResults] = React.useState([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState('');
  const [uploadedImage, setUploadedImage] = React.useState(null);
  const [predictionResult, setPredictionResult] = React.useState(null);
  const [showFilters, setShowFilters] = React.useState(false);
  const [filters, setFilters] = React.useState({
    type: '',
    minWeight: '',
    maxWeight: '',
    minHeight: '',
    maxHeight: '',
    minAttack: '0',
    minDefense: '0',
    minStamina: '0'
  });

  const handleSearch = async (e) => {
    if (e && e.preventDefault) {
      e.preventDefault();
    }
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('q', searchQuery);
      if (filters.type) params.append('type', filters.type);
      if (filters.minWeight) params.append('min_weight', filters.minWeight);
      if (filters.maxWeight) params.append('max_weight', filters.maxWeight);
      if (filters.minHeight) params.append('min_height', filters.minHeight);
      if (filters.maxHeight) params.append('max_height', filters.maxHeight);
      if (filters.minAttack) params.append('min_attack', filters.minAttack);
      if (filters.minDefense) params.append('min_defense', filters.minDefense);
      if (filters.minStamina) params.append('min_stamina', filters.minStamina);

      const response = await fetch(`http://localhost:5000/search?${params.toString()}`);
      const data = await response.json();
      setSearchResults(data.results || []);
      setShowFilters(false);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleResetFilters = () => {
    setFilters({
      type: '',
      minWeight: '',
      maxWeight: '',
      minHeight: '',
      maxHeight: '',
      minAttack: '0',
      minDefense: '0',
      minStamina: '0'
    });
    setSearchQuery('');
    setSearchResults([]);
  };

  const handleImageDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      processImage(file);
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      processImage(file);
    }
  };

  const processImage = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      setUploadedImage(e.target.result);
    };
    reader.readAsDataURL(file);
  };

  const handlePredict = async () => {
    if (!uploadedImage) return;

    setIsLoading(true);
    try {
      const blob = await (await fetch(uploadedImage)).blob();
      const formData = new FormData();
      formData.append('file', blob, 'pokemon.jpg');

      const response = await fetch('http://localhost:5000/predict', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      if (data.error) {
        alert('Error: ' + data.error);
      } else {
        setPredictionResult(data);
      }
    } catch (error) {
      console.error('Prediction error:', error);
      alert('Error predicting Pokemon');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="bg-overlay"></div>
      <div className="particles"></div>

      {/* Navbar */}
      <nav className="navbar">
        <div className="nav-container">
          <div className="logo">
            <span className="pokeball">🔴</span>
            <span className="logo-text">Pokemon Knower</span>
          </div>
          <div className="nav-links">
            <a href="#home">Home</a>
            <a href="#search">Search</a>
            <a href="#upload">Scan</a>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section id="home" className="hero">
        <div className="hero-content">
          <h1 className="hero-title">Gotta Know <span className="accent">'Em All!</span></h1>
          <p className="hero-subtitle">The Ultimate AI Pokemon Identifier</p>
        </div>
      </section>

      {/* Search Section */}
      <section id="search" className="search-section">
        <div className="container">
          <h2>Search Pokemon</h2>
          
          <div className="search-box">
            <input
              type="text"
              className="search-input"
              placeholder="Search by name or type..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button className="search-btn" onClick={handleSearch} disabled={isLoading}>
              {isLoading ? '🔍 Searching...' : '🔍'}
            </button>
            <button 
              className="filter-btn"
              onClick={() => setShowFilters(!showFilters)}
              title="Advanced Filters"
            >
              ⚙️
            </button>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div className="filters-panel">
              <div className="filter-row">
                <div className="filter-group">
                  <label>Type</label>
                  <select name="type" value={filters.type} onChange={handleFilterChange}>
                    <option value="">All Types</option>
                    <option value="normal">Normal</option>
                    <option value="fire">Fire</option>
                    <option value="water">Water</option>
                    <option value="electric">Electric</option>
                    <option value="grass">Grass</option>
                    <option value="ice">Ice</option>
                    <option value="fighting">Fighting</option>
                    <option value="poison">Poison</option>
                    <option value="ground">Ground</option>
                    <option value="flying">Flying</option>
                    <option value="psychic">Psychic</option>
                    <option value="bug">Bug</option>
                    <option value="rock">Rock</option>
                    <option value="ghost">Ghost</option>
                    <option value="dragon">Dragon</option>
                    <option value="dark">Dark</option>
                    <option value="steel">Steel</option>
                    <option value="fairy">Fairy</option>
                  </select>
                </div>

                <div className="filter-group">
                  <label>Weight (kg)</label>
                  <div className="range-group">
                    <input 
                      type="number" 
                      name="minWeight" 
                      placeholder="Min" 
                      value={filters.minWeight}
                      onChange={handleFilterChange}
                      step="0.1"
                    />
                    <span>-</span>
                    <input 
                      type="number" 
                      name="maxWeight" 
                      placeholder="Max" 
                      value={filters.maxWeight}
                      onChange={handleFilterChange}
                      step="0.1"
                    />
                  </div>
                </div>

                <div className="filter-group">
                  <label>Height (m)</label>
                  <div className="range-group">
                    <input 
                      type="number" 
                      name="minHeight" 
                      placeholder="Min" 
                      value={filters.minHeight}
                      onChange={handleFilterChange}
                      step="0.1"
                    />
                    <span>-</span>
                    <input 
                      type="number" 
                      name="maxHeight" 
                      placeholder="Max" 
                      value={filters.maxHeight}
                      onChange={handleFilterChange}
                      step="0.1"
                    />
                  </div>
                </div>
              </div>

              <div className="filter-row">
                <div className="filter-group">
                  <label>Min Attack</label>
                  <input 
                    type="number" 
                    name="minAttack" 
                    value={filters.minAttack}
                    onChange={handleFilterChange}
                    min="0"
                  />
                </div>
                <div className="filter-group">
                  <label>Min Defense</label>
                  <input 
                    type="number" 
                    name="minDefense" 
                    value={filters.minDefense}
                    onChange={handleFilterChange}
                    min="0"
                  />
                </div>
                <div className="filter-group">
                  <label>Min Stamina</label>
                  <input 
                    type="number" 
                    name="minStamina" 
                    value={filters.minStamina}
                    onChange={handleFilterChange}
                    min="0"
                  />
                </div>
              </div>

              <div className="filter-actions">
                <button className="btn-apply" onClick={handleSearch}>Apply Filters</button>
                <button className="btn-reset" onClick={handleResetFilters}>Reset</button>
              </div>
            </div>
          )}

          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="results">
              <h3>Found {searchResults.length} Pokemon</h3>
              <div className="pokemon-grid">
                {searchResults.map((pokemon, idx) => (
                  <div key={idx} className="pokemon-card">
                    <div className="pokemon-image">
                      <img 
                        src={`https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${pokemon.number}.png`}
                        alt={pokemon.name}
                        onError={(e) => e.target.src = 'https://via.placeholder.com/150'}
                      />
                    </div>
                    <div className="pokemon-info">
                      <h4>{pokemon.name}</h4>
                      <div className="type-badges">
                        <span className={`badge type-${pokemon.main_type?.toLowerCase()}`}>
                          {pokemon.main_type}
                        </span>
                        {pokemon.secondary_type && (
                          <span className={`badge type-${pokemon.secondary_type?.toLowerCase()}`}>
                            {pokemon.secondary_type}
                          </span>
                        )}
                      </div>
                      <div className="stats">
                        <div className="stat">
                          <span className="stat-label">ATK</span>
                          <div className="stat-bar">
                            <div className="stat-fill" style={{ width: `${(pokemon.attack / 200) * 100}%` }}></div>
                          </div>
                          <span className="stat-value">{pokemon.attack}</span>
                        </div>
                        <div className="stat">
                          <span className="stat-label">DEF</span>
                          <div className="stat-bar">
                            <div className="stat-fill" style={{ width: `${(pokemon.defense / 200) * 100}%` }}></div>
                          </div>
                          <span className="stat-value">{pokemon.defense}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {searchResults.length === 0 && searchQuery && !isLoading && (
            <div className="no-results">No Pokemon found matching your criteria.</div>
          )}
        </div>
      </section>

      {/* Upload & Scan Section */}
      <section id="upload" className="upload-section">
        <div className="container">
          <h2>Scan Pokemon</h2>
          
          <div className="upload-grid">
            <div className="upload-box">
              <div 
                className="drop-zone"
                onDrop={handleImageDrop}
                onDragOver={(e) => e.preventDefault()}
              >
                {uploadedImage ? (
                  <img src={uploadedImage} alt="Uploaded" className="preview-image" />
                ) : (
                  <div className="placeholder">
                    <span className="upload-icon">📷</span>
                    <p>Drag image here or click</p>
                    <input 
                      type="file" 
                      accept="image/*"
                      onChange={handleImageUpload}
                      style={{ display: 'none' }}
                      id="file-input"
                    />
                    <label htmlFor="file-input" style={{ cursor: 'pointer', color: 'var(--primary)' }}>
                      Choose File
                    </label>
                  </div>
                )}
              </div>
              <button 
                className="predict-btn"
                onClick={handlePredict}
                disabled={!uploadedImage || isLoading}
              >
                {isLoading ? 'Analyzing...' : 'START SCAN'}
              </button>
            </div>

            <div className="result-box">
              {predictionResult ? (
                <div className="prediction-result">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1.5rem' }}>
                    <div>
                      <h3 style={{ fontSize: '2rem', margin: '0 0 0.5rem 0', textTransform: 'capitalize' }}>
                        {predictionResult.class}
                      </h3>
                      <div className="confidence" style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>
                        {predictionResult.confidence}% Match
                      </div>
                      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                        {predictionResult.stats?.type && (
                          <span className={`badge type-${predictionResult.stats.type.toLowerCase()}`}>
                            {predictionResult.stats.type}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Stats Grid */}
                  {predictionResult.stats && (
                    <div style={{ 
                      display: 'grid', 
                      gridTemplateColumns: 'repeat(2, 1fr)', 
                      gap: '1rem',
                      marginBottom: '1.5rem',
                      borderTop: '1px solid rgba(255,255,255,0.2)',
                      paddingTop: '1rem'
                    }}>
                      <div>
                        <div style={{ fontSize: '0.8rem', color: '#888', textTransform: 'uppercase', marginBottom: '0.3rem' }}>HP</div>
                        <div style={{ fontSize: '1.3rem', fontWeight: 'bold', color: 'var(--primary)' }}>
                          {predictionResult.stats.hp}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.8rem', color: '#888', textTransform: 'uppercase', marginBottom: '0.3rem' }}>ATK</div>
                        <div style={{ fontSize: '1.3rem', fontWeight: 'bold', color: 'var(--accent)' }}>
                          {predictionResult.stats.attack}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.8rem', color: '#888', textTransform: 'uppercase', marginBottom: '0.3rem' }}>DEF</div>
                        <div style={{ fontSize: '1.3rem', fontWeight: 'bold', color: '#667eea' }}>
                          {predictionResult.stats.defense}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.8rem', color: '#888', textTransform: 'uppercase', marginBottom: '0.3rem' }}>SPD</div>
                        <div style={{ fontSize: '1.3rem', fontWeight: 'bold', color: '#4ade80' }}>
                          {predictionResult.stats.speed}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Top Predictions */}
                  <div className="top-predictions">
                    <h4>Also Detected:</h4>
                    {predictionResult.top_3?.slice(1).map((pred, idx) => (
                      <div key={idx} style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center',
                        padding: '0.75rem 0',
                        borderBottom: idx < predictionResult.top_3.length - 2 ? '1px solid rgba(255,255,255,0.1)' : 'none'
                      }}>
                        <span style={{ textTransform: 'capitalize' }}>{pred.class}</span>
                        <div style={{ 
                          background: 'rgba(255,204,0,0.1)', 
                          padding: '0.3rem 0.7rem', 
                          borderRadius: '20px',
                          fontSize: '0.9rem',
                          color: 'var(--primary)',
                          fontWeight: '600'
                        }}>
                          {pred.confidence.toFixed(1)}%
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="empty-state">
                  <span className="empty-icon">🔍</span>
                  <p>Upload a Pokemon image to scan</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <p>© 2025 Pokemon Knower | Powered by AI</p>
      </footer>
    </div>
  );
};

export default App;
