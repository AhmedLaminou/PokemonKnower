# Pokémon Knower: AI Strategy & Feature Proposals

## 1. Model Strategy: Fine-tune vs. Switch?

Your current `MobileNetV2` model is excellent for **Edge/Mobile** use because it's lightweight, but it struggles with scaling to 1000+ classes because collecting high-quality data for every single Pokémon is a massive bottleneck.

### Option A: The "Modern Pro" Approach (LLM/Vision)

Instead of a fixed classifier, use a **Vision-Language Model (VLM)**.

- **Model**: `google/gemini-flash-1.5` or `openai/gpt-4o-mini` via OpenRouter.
- **Pros**: Zero-shot recognition. It already "knows" what every Pokémon (including Gen 9 and Mega Evolutions) looks like. No training needed.
- **Cons**: Requires API calls (latency and cost).

### Option B: The "Custom Expert" Approach (Fine-tuning)

If you want to keep it local and own the weights:

- **Upgrade the Backbone**: Move from `MobileNetV2` to **`EfficientNetV2-S`** or a **`Vision Transformer (ViT)`**. These capture global patterns much better than the local kernels in MobileNet.
- **Data Augmentation**: Your current notebook uses standard transforms. Adding **MixUp** or **CutMix** can push that 88% into the 93-95% range.

### 💡 Recommendation: The Hybrid "Rotom-Scan"

Use your **Custom Model** as a first pass (it's instant). If the confidence is `< 90%`, automatically send the image to a **VLM** on the backend. This gives you speed for common cases and perfect accuracy for everything else.

---

## 2. Cool AI Feature Proposals

### 📸 1. The Real-time "AR Pokedex" (OpenCV)

Instead of just uploading an image, create a `/scan` page that uses your webcam.

- **AI Logic**: Use OpenCV's `MatchTemplate` or `ORB` descriptors to detect a Pokémon shape in the frame.
- **UX**: Draw a high-tech SVG "locking-on" square around the detected Pokémon and show its stats in real-time as a floating AR overlay.

### ✨ 2. Shiny & Rarity Detector (OpenCV)

- **Logic**: Use OpenCV to convert the image to **HSV color space**. Calculate the color histogram of the detected Pokémon.
- **Feature**: Compare the colors against the "standard" sprite. If it detects a shift (e.g., Charizard being black/grey instead of orange), trigger a "SHINY DETECTED!" animation with star particles.

### 🔍 3. Semantic "Lookalike" Search

- **Logic**: Use an AI embedding model (like `text-embedding-3-small`) to index the "vibes" of Pokémon.
- **Feature**: "I want a Pokémon that looks like a scary ghost but is also cute." The AI will find the closest semantic match in your database.

### 🎨 4. AI-Powered "Battle Stats" from Sketch

- **Logic**: Allow users to draw a rough sketch of a Pokémon.
- **Feature**: Use an Image-to-Image AI (like ControlNet) to turn their sketch into a "professional" style Pokémon and use the VLM to guess its stats based on the drawing.

---

### Which one should we build first? 🚀

I'm ready to help you implement the **Hybrid VLM fallback** (to get 100% coverage) or the **OpenCV Shiny Detector**!
