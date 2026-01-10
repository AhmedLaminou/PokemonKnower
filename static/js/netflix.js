/**
 * Netflix-Style Hero Carousel
 * PokémonKnower Premium UI Enhancement
 */

class HeroCarousel {
    constructor(container) {
        this.container = container;
        this.track = container.querySelector('.carousel-track');
        this.slides = container.querySelectorAll('.carousel-slide');
        this.dots = container.querySelectorAll('.carousel-dot');
        this.prevBtn = container.querySelector('.carousel-arrow.prev');
        this.nextBtn = container.querySelector('.carousel-arrow.next');
        this.progressBar = container.querySelector('.carousel-progress');
        
        this.currentIndex = 0;
        this.slideCount = this.slides.length;
        this.autoPlayInterval = null;
        this.progressInterval = null;
        this.autoPlayDelay = 8000; // 8 seconds per slide
        this.isPaused = false;
        
        this.init();
    }
    
    init() {
        // Set initial state
        this.updateSlide(0);
        
        // Bind navigation events
        if (this.prevBtn) {
            this.prevBtn.addEventListener('click', () => this.prev());
        }
        if (this.nextBtn) {
            this.nextBtn.addEventListener('click', () => this.next());
        }
        
        // Bind dot navigation
        this.dots.forEach((dot, index) => {
            dot.addEventListener('click', () => this.goToSlide(index));
        });
        
        // Pause on hover
        this.container.addEventListener('mouseenter', () => this.pause());
        this.container.addEventListener('mouseleave', () => this.resume());
        
        // Touch/swipe support
        this.initTouchEvents();
        
        // Start autoplay
        this.startAutoPlay();
    }
    
    updateSlide(index) {
        // Update track position
        this.track.style.transform = `translateX(-${index * 100}%)`;
        
        // Update active states
        this.slides.forEach((slide, i) => {
            slide.classList.toggle('active', i === index);
        });
        
        this.dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === index);
        });
        
        this.currentIndex = index;
    }
    
    next() {
        const nextIndex = (this.currentIndex + 1) % this.slideCount;
        this.goToSlide(nextIndex);
    }
    
    prev() {
        const prevIndex = (this.currentIndex - 1 + this.slideCount) % this.slideCount;
        this.goToSlide(prevIndex);
    }
    
    goToSlide(index) {
        this.updateSlide(index);
        this.resetProgress();
    }
    
    startAutoPlay() {
        this.resetProgress();
        this.autoPlayInterval = setInterval(() => {
            if (!this.isPaused) {
                this.next();
            }
        }, this.autoPlayDelay);
    }
    
    resetProgress() {
        if (this.progressBar) {
            this.progressBar.style.width = '0%';
            let progress = 0;
            clearInterval(this.progressInterval);
            
            this.progressInterval = setInterval(() => {
                if (!this.isPaused) {
                    progress += 100 / (this.autoPlayDelay / 100);
                    this.progressBar.style.width = `${Math.min(progress, 100)}%`;
                }
            }, 100);
        }
    }
    
    pause() {
        this.isPaused = true;
    }
    
    resume() {
        this.isPaused = false;
    }
    
    initTouchEvents() {
        let startX = 0;
        let endX = 0;
        
        this.container.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
        }, { passive: true });
        
        this.container.addEventListener('touchend', (e) => {
            endX = e.changedTouches[0].clientX;
            const diff = startX - endX;
            
            if (Math.abs(diff) > 50) {
                if (diff > 0) {
                    this.next();
                } else {
                    this.prev();
                }
            }
        }, { passive: true });
    }
}

/**
 * Voice AI Pokédex
 * Speech recognition and synthesis for hands-free interaction
 */
class VoicePokedex {
    constructor() {
        this.btn = document.getElementById('voiceBtn');
        this.feedback = document.getElementById('voiceFeedback');
        this.transcript = document.getElementById('voiceTranscript');
        this.waveform = document.querySelector('.voice-waveform');
        
        this.isListening = false;
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        
        // Check browser support
        this.isSupported = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
        
        if (this.isSupported) {
            this.init();
        } else {
            console.warn('Speech recognition not supported in this browser');
            if (this.btn) this.btn.style.display = 'none';
        }
    }
    
    init() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        
        // Bind events
        if (this.btn) {
            this.btn.addEventListener('click', () => this.toggle());
        }
        
        this.recognition.onstart = () => {
            this.isListening = true;
            this.btn?.classList.add('listening');
            this.showFeedback();
            this.updateTranscript('Listening...');
        };
        
        this.recognition.onend = () => {
            this.isListening = false;
            this.btn?.classList.remove('listening');
        };
        
        this.recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }
            
            if (interimTranscript) {
                this.updateTranscript(interimTranscript);
            }
            
            if (finalTranscript) {
                this.processCommand(finalTranscript);
            }
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.updateTranscript(`Error: ${event.error}`);
            this.isListening = false;
            this.btn?.classList.remove('listening');
        };
    }
    
    toggle() {
        if (this.isListening) {
            this.stop();
        } else {
            this.start();
        }
    }
    
    start() {
        if (!this.isSupported) return;
        try {
            this.recognition.start();
        } catch (e) {
            console.error('Error starting recognition:', e);
        }
    }
    
    stop() {
        try {
            this.recognition.stop();
        } catch (e) {
            console.error('Error stopping recognition:', e);
        }
    }
    
    showFeedback() {
        if (this.feedback) {
            this.feedback.classList.add('show');
        }
    }
    
    hideFeedback() {
        if (this.feedback) {
            setTimeout(() => {
                this.feedback.classList.remove('show');
            }, 2000);
        }
    }
    
    updateTranscript(text) {
        if (this.transcript) {
            this.transcript.textContent = text;
        }
    }
    
    async processCommand(command) {
        const lowerCommand = command.toLowerCase().trim();
        this.updateTranscript(`"${command}"`);
        
        // --- 1. Client-Side Instant Actions (Zero Latency) ---
        
        // Navigation (Fastest)
        const navigate = lowerCommand.match(/(?:go to|open|show)\s+(pokedex|scanner|quiz|gallery|home|favorites)/);
        if (navigate) {
            this.navigateTo(navigate[1]);
            this.hideFeedback();
            return;
        }

        // Simple Search
        const searchFor = lowerCommand.match(/(?:search for|look up|search)\s+(.+)/);
        if (searchFor) {
            this.performSearch(searchFor[1]);
            this.hideFeedback();
            return;
        }

        // --- 2. Server-Side AI Brain (Rotom) ---
        // If it's not a simple command, ask the AI Brain!
        // This includes "Tell me about..." because the AI creates better descriptions than the simple lookup.
        await this.askRotom(command);
        this.hideFeedback();
    }
    
    async askRotom(command) {
        try {
            this.updateTranscript("Thinking...");
            // Use the updated backend route which connects to ChatBot
            const response = await fetch('/api/voice/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: command })
            });

            const data = await response.json();

            if (data.speech) {
                this.speak(data.speech);
            }

            // Handle server actions
            if (data.action === 'navigate' && data.data.url) {
                window.location.href = data.data.url;
            } else if (data.action === 'show_pokemon' && data.data.name) {
                window.location.href = `/pokemon/${data.data.name}`;
            } else if (data.action === 'search' && data.data.query) {
                 this.performSearch(data.data.query);
            }
            
        } catch (error) {
            console.error('Rotom Brain Error:', error);
            this.speak("Sorry, I lost connection to the server.");
        }
    }

    cleanPokemonName(name) {
        // Remove common filler words
        return name.replace(/\b(a|an|the|pokemon|pokémon)\b/gi, '').trim();
    }
    
    // (lookupPokemon is deprecated in favor of askRotom, but kept for reference if needed)

    performSearch(query) {
        this.speak(`Searching for ${query}`);
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.value = query;
            searchInput.dispatchEvent(new Event('input'));
            document.getElementById('searchBtn')?.click();
        } else {
            window.location.href = `/search?q=${encodeURIComponent(query)}`;
        }
    }
    
    navigateTo(page) {
        const routes = {
            'home': '/',
            'pokedex': '/pokedex',
            'scanner': '/scanner',
            'quiz': '/quiz',
            'gallery': '/gallery',
            'favorites': '/favorites'
        };
        
        const route = routes[page.toLowerCase()];
        if (route) {
            this.speak(`Opening ${page}`);
            window.location.href = route;
        }
    }
    
    speak(text) {
        if (!this.synthesis) return;
        
        // Cancel any ongoing speech
        this.synthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0; // Slightly faster for natural feel
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        // --- ZERO COST PREMIUM VOICE UPGRADE ---
        // Look for "Natural" voices (Edge/Windows) or Google voices
        const voices = this.synthesis.getVoices();
        
        // Priority 1: "Natural" voices (Best quality, free)
        let preferredVoice = voices.find(v => v.name.includes('Natural') && v.lang.startsWith('en'));
        
        // Priority 2: Google voices (Good quality)
        if (!preferredVoice) {
            preferredVoice = voices.find(v => v.name.includes('Google') && v.lang.startsWith('en'));
        }
        
        // Priority 3: Any English voice
        if (!preferredVoice) {
            preferredVoice = voices.find(v => v.lang.startsWith('en'));
        }

        if (preferredVoice) {
            utterance.voice = preferredVoice;
            // console.log("Using voice:", preferredVoice.name); 
        }
        
        this.synthesis.speak(utterance);
    }
}

/**
 * Initialize on DOM ready
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Hero Carousel
    const carouselElement = document.querySelector('.hero-carousel');
    if (carouselElement) {
        window.heroCarousel = new HeroCarousel(carouselElement);
    }
    
    // Initialize Voice Pokédex
    window.voicePokedex = new VoicePokedex();
});
