import random
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebsiteGenerator:
    def __init__(self):
        self.themes = {
            "Bright Minimalist": {
                "colors": {"primary": "#FFFFFF", "secondary": "#F3F4F6", "accent": "#3B82F6", "text": "#1F2937"},
                "style": "clean, white background, minimal design"
            },
            "Dark Modern": {
                "colors": {"primary": "#1F2937", "secondary": "#111827", "accent": "#60A5FA", "text": "#F9FAFB"},
                "style": "dark gray/blue, professional"
            },
            "Neon Cyberpunk": {
                "colors": {"primary": "#000000", "secondary": "#1A1A1A", "accent": "#FF00FF", "text": "#00FFFF"},
                "style": "black background with electric colors"
            },
            "Warm Cream": {
                "colors": {"primary": "#FEF3C7", "secondary": "#FDE68A", "accent": "#F59E0B", "text": "#92400E"},
                "style": "amber/orange, restaurant vibes"
            },
            "Mint Fresh": {
                "colors": {"primary": "#D1FAE5", "secondary": "#A7F3D0", "accent": "#10B981", "text": "#064E3B"},
                "style": "emerald green, health/wellness"
            },
            "Luxury Dark": {
                "colors": {"primary": "#1F2937", "secondary": "#111827", "accent": "#F59E0B", "text": "#F9FAFB"},
                "style": "slate with gold accents"
            },
            "Bold Primary": {
                "colors": {"primary": "#EF4444", "secondary": "#3B82F6", "accent": "#EC4899", "text": "#FFFFFF"},
                "style": "red, blue, pink dominant"
            },
            "Pastel Gradient": {
                "colors": {"primary": "#FCE7F3", "secondary": "#E0E7FF", "accent": "#C7D2FE", "text": "#4C1D95"},
                "style": "soft gradient colors"
            },
            "High Contrast": {
                "colors": {"primary": "#000000", "secondary": "#FFFFFF", "accent": "#000000", "text": "#FFFFFF"},
                "style": "black/white bold"
            },
            "Corporate Blue": {
                "colors": {"primary": "#1E40AF", "secondary": "#3B82F6", "accent": "#60A5FA", "text": "#FFFFFF"},
                "style": "traditional business blue"
            },
            "Playful Gradient": {
                "colors": {"primary": "#FF6B6B", "secondary": "#4ECDC4", "accent": "#45B7D1", "text": "#2C3E50"},
                "style": "rainbow-ish gradients"
            },
            "Tech Dark": {
                "colors": {"primary": "#1A1A2E", "secondary": "#16213E", "accent": "#E94560", "text": "#F5F5F5"},
                "style": "purple/cyan neon tech"
            },
            "Nature Green": {
                "colors": {"primary": "#14532D", "secondary": "#166534", "accent": "#84CC16", "text": "#F0FDF4"},
                "style": "forest/eco theme"
            },
            "Sunset Gradient": {
                "colors": {"primary": "#FF6B35", "secondary": "#F7931E", "accent": "#FDC830", "text": "#2C3E50"},
                "style": "warm oranges/pinks sunset"
            },
            "Retro 80s": {
                "colors": {"primary": "#FF00FF", "secondary": "#00FFFF", "accent": "#FFFF00", "text": "#000000"},
                "style": "bright neon + dark retro"
            }
        }
        
        self.last_used_theme = None
        
    def detect_industry(self, prompt: str) -> str:
        """Detect industry from user prompt"""
        prompt_lower = prompt.lower()
        
        sports_keywords = ["football", "soccer", "basketball", "team", "league", "players", "coach", "sport", "game", "match"]
        restaurant_keywords = ["food", "restaurant", "cafe", "chef", "menu", "dining", "pizza", "burger", "cuisine", "eat"]
        fitness_keywords = ["gym", "fitness", "trainer", "workout", "yoga", "personal training", "exercise", "health"]
        ecommerce_keywords = ["shop", "store", "products", "clothing", "sell", "boutique", "buy", "retail"]
        healthcare_keywords = ["doctor", "clinic", "medical", "health", "hospital", "patient", "treatment"]
        realestate_keywords = ["property", "real estate", "house", "apartment", "agent", "home", "rental"]
        agency_keywords = ["agency", "creative", "design", "marketing", "branding", "advertising"]
        education_keywords = ["course", "education", "school", "learn", "training", "teach", "student"]
        
        if any(keyword in prompt_lower for keyword in sports_keywords):
            return "sports"
        elif any(keyword in prompt_lower for keyword in restaurant_keywords):
            return "restaurant"
        elif any(keyword in prompt_lower for keyword in fitness_keywords):
            return "fitness"
        elif any(keyword in prompt_lower for keyword in ecommerce_keywords):
            return "ecommerce"
        elif any(keyword in prompt_lower for keyword in healthcare_keywords):
            return "healthcare"
        elif any(keyword in prompt_lower for keyword in realestate_keywords):
            return "realestate"
        elif any(keyword in prompt_lower for keyword in agency_keywords):
            return "agency"
        elif any(keyword in prompt_lower for keyword in education_keywords):
            return "education"
        else:
            return "saas"  # Default
    
    def select_theme(self, avoid_theme: Optional[str] = None) -> Tuple[str, Dict]:
        """Select a random theme, avoiding the specified one if provided"""
        available_themes = [t for t in self.themes.keys() if t != avoid_theme]
        selected_theme = random.choice(available_themes)
        return selected_theme, self.themes[selected_theme]
    
    def get_real_images(self, category: str, count: int = 5) -> List[str]:
        """Get real Unsplash images for different categories"""
        image_urls = {
            "sports_hero": [
                "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1552667466-07770ae110d0?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1517466787929-bc90951d0974?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1579952363873-27d3bfad9c0d?w=1200&h=800&fit=crop"
            ],
            "sports_players": [
                "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1516589178581-6cd7833ae3b2?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1511884642898-4c92249e20b6?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1507924538820-ede9a631df31?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1552667466-07770ae110d0?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=400&h=400&fit=crop"
            ],
            "restaurant_hero": [
                "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1559329007-40df8a9345d8?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1449784046597-1ad5e5531f3b?w=1200&h=800&fit=crop"
            ],
            "restaurant_dishes": [
                "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1473093226795-af9932fe7555?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1458642849426-c5d0a557b00c?w=400&h=400&fit=crop"
            ],
            "fitness_hero": [
                "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1540497077202-7c8a3219c4ad?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=1200&h=800&fit=crop"
            ],
            "fitness_gym": [
                "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1540497077202-7c8a3219c4ad?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1506629905687-662f3b603b5e?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1517836357463-d258be16a245?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1540497077202-7c8a3219c4ad?w=400&h=400&fit=crop"
            ],
            "saas_dashboard": [
                "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200&h=800&fit=crop"
            ],
            "office": [
                "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=400&h=400&fit=crop"
            ],
            "healthcare": [
                "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1200&h=800&fit=crop"
            ],
            "ecommerce_products": [
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop"
            ],
            "handshake_trust": [
                "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=1200&h=800&fit=crop",
                "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=1200&h=800&fit=crop"
            ]
        }
        
        return random.sample(image_urls.get(category, image_urls["office"]), min(count, len(image_urls.get(category, image_urls["office"]))))
    
    def generate_ai_plan(self, prompt: str, business_name: str = "Business Name", regenerate: bool = False) -> Dict:
        """Main function to generate website based on prompt"""
        try:
            # Detect industry
            industry = self.detect_industry(prompt)
            logger.info(f"Detected industry: {industry}")
            
            # Select theme (avoid previous if regenerating)
            avoid_theme = self.last_used_theme if regenerate else None
            theme_name, theme_config = self.select_theme(avoid_theme)
            self.last_used_theme = theme_name
            logger.info(f"Selected theme: {theme_name}")
            
            # Generate website based on industry
            if industry == "sports":
                html = self._generate_sports_website(business_name, theme_name, theme_config)
            elif industry == "restaurant":
                html = self._generate_restaurant_website(business_name, theme_name, theme_config)
            elif industry == "fitness":
                html = self._generate_fitness_website(business_name, theme_name, theme_config)
            elif industry == "ecommerce":
                html = self._generate_ecommerce_website(business_name, theme_name, theme_config)
            elif industry == "healthcare":
                html = self._generate_healthcare_website(business_name, theme_name, theme_config)
            elif industry == "agency":
                html = self._generate_agency_website(business_name, theme_name, theme_config)
            elif industry == "education":
                html = self._generate_education_website(business_name, theme_name, theme_config)
            else:  # SaaS
                html = self._generate_saas_website(business_name, theme_name, theme_config)
            
            return {
                "html": html,
                "metadata": {
                    "business_name": business_name,
                    "industry": industry,
                    "theme": theme_name,
                    "theme_colors": theme_config["colors"],
                    "version": 1,
                    "status": "success"
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating website: {str(e)}")
            # Return fallback website
            return self._generate_fallback_website(business_name)
    
    def _generate_sports_website(self, business_name: str, theme_name: str, theme_config: Dict) -> str:
        """Generate sports website with 4 different styles"""
        style_variants = ["modern_light", "dark_bold", "minimalist", "energetic_neon"]
        style = random.choice(style_variants)
        
        hero_images = self.get_real_images("sports_hero", 1)
        player_images = self.get_real_images("sports_players", 8)
        
        colors = theme_config["colors"]
        
        if style == "modern_light":
            return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{business_name} - Professional Sports Team</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white text-gray-900">
    <!-- Navigation -->
    <nav class="bg-white shadow-lg sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <span class="text-2xl font-bold text-blue-600">{business_name}</span>
                </div>
                <div class="flex items-center space-x-8">
                    <a href="#schedule" class="text-gray-700 hover:text-blue-600">Schedule</a>
                    <a href="#players" class="text-gray-700 hover:text-blue-600">Players</a>
                    <a href="#stats" class="text-gray-700 hover:text-blue-600">Stats</a>
                    <a href="#tickets" class="text-gray-700 hover:text-blue-600">Tickets</a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="relative h-screen flex items-center justify-center">
        <img src="{hero_images[0]}" alt="Sports Action" class="absolute inset-0 w-full h-full object-cover">
        <div class="absolute inset-0 bg-black bg-opacity-40"></div>
        <div class="relative text-center text-white">
            <h1 class="text-6xl font-bold mb-4">WELCOME TO {business_name.upper()}</h1>
            <p class="text-xl mb-8">Experience the Thrill of Victory</p>
            <button class="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg text-lg font-semibold transition">
                BUY TICKETS NOW
            </button>
        </div>
    </section>

    <!-- Season Highlights -->
    <section class="py-20 bg-gray-50">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-4xl font-bold text-center mb-12">Season Highlights</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div class="bg-white p-8 rounded-lg shadow-lg">
                    <h3 class="text-2xl font-bold text-blue-600 mb-4">15 Wins</h3>
                    <p class="text-gray-600">Outstanding performance this season</p>
                </div>
                <div class="bg-white p-8 rounded-lg shadow-lg">
                    <h3 class="text-2xl font-bold text-blue-600 mb-4">3 Championships</h3>
                    <p class="text-gray-600">Building our legacy</p>
                </div>
                <div class="bg-white p-8 rounded-lg shadow-lg">
                    <h3 class="text-2xl font-bold text-blue-600 mb-4">Top Ranked</h3>
                    <p class="text-gray-600">Leading the league</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Player Roster -->
    <section id="players" class="py-20 bg-white">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-4xl font-bold text-center mb-12">Star Players</h2>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                {"".join([f'''
                <div class="text-center">
                    <img src="{img}" alt="Player" class="w-full h-64 object-cover rounded-lg mb-4">
                    <h3 class="text-xl font-bold">Player {i+1}</h3>
                    <p class="text-gray-600">Position</p>
                </div>
                ''' for i, img in enumerate(player_images[:4])])}
            </div>
        </div>
    </section>

    <!-- Upcoming Matches -->
    <section id="schedule" class="py-20 bg-gray-50">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-4xl font-bold text-center mb-12">Upcoming Matches</h2>
            <div class="space-y-4">
                <div class="bg-white p-6 rounded-lg shadow flex justify-between items-center">
                    <div>
                        <h3 class="text-xl font-bold">vs Rival Team</h3>
                        <p class="text-gray-600">Home Game</p>
                    </div>
                    <div class="text-right">
                        <p class="text-lg font-semibold">March 15, 2024</p>
                        <p class="text-gray-600">7:00 PM</p>
                    </div>
                </div>
                <div class="bg-white p-6 rounded-lg shadow flex justify-between items-center">
                    <div>
                        <h3 class="text-xl font-bold">vs Conference Leader</h3>
                        <p class="text-gray-600">Away Game</p>
                    </div>
                    <div class="text-right">
                        <p class="text-lg font-semibold">March 22, 2024</p>
                        <p class="text-gray-600">8:00 PM</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Stats Dashboard -->
    <section id="stats" class="py-20 bg-white">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-4xl font-bold text-center mb-12">Team Statistics</h2>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div class="text-center">
                    <h3 class="text-3xl font-bold text-blue-600">92%</h3>
                    <p class="text-gray-600">Win Rate</p>
                </div>
                <div class="text-center">
                    <h3 class="text-3xl font-bold text-blue-600">156</h3>
                    <p class="text-gray-600">Goals Scored</p>
                </div>
                <div class="text-center">
                    <h3 class="text-3xl font-bold text-blue-600">45</h3>
                    <p class="text-gray-600">Assists</p>
                </div>
                <div class="text-center">
                    <h3 class="text-3xl font-bold text-blue-600">12</h3>
                    <p class="text-gray-600">Clean Sheets</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Tickets CTA -->
    <section id="tickets" class="py-20 bg-blue-600 text-white">
        <div class="max-w-4xl mx-auto text-center px-4">
            <h2 class="text-4xl font-bold mb-4">Don't Miss the Action!</h2>
            <p class="text-xl mb-8">Get your tickets now and support {business_name}</p>
            <button class="bg-white text-blue-600 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-100 transition">
                PURCHASE TICKETS
            </button>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-900 text-white py-12">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <p>&copy; 2024 {business_name}. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>
"""
        
        elif style == "dark_bold":
            return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{business_name} - UNLEASH THE POWER</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-black text-white">
    <!-- Navigation -->
    <nav class="bg-black border-b border-red-600 sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <span class="text-3xl font-bold text-red-600">{business_name}</span>
                </div>
                <div class="flex items-center space-x-8">
                    <a href="#schedule" class="text-white hover:text-red-600 font-bold">SCHEDULE</a>
                    <a href="#players" class="text-white hover:text-red-600 font-bold">PLAYERS</a>
                    <a href="#stats" class="text-white hover:text-red-600 font-bold">STATS</a>
                    <a href="#tickets" class="text-white hover:text-red-600 font-bold">TICKETS</a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="relative h-screen flex items-center justify-center">
        <img src="{hero_images[0]}" alt="Sports Action" class="absolute inset-0 w-full h-full object-cover opacity-50">
        <div class="absolute inset-0 bg-gradient-to-b from-black via-transparent to-black"></div>
        <div class="relative text-center">
            <h1 class="text-7xl font-black mb-6 text-red-600">{business_name.upper()}</h1>
            <p class="text-2xl mb-8 font-bold">DOMINATE THE GAME</p>
            <button class="bg-red-600 hover:bg-red-700 text-white px-10 py-5 rounded-lg text-xl font-black transition transform hover:scale-105">
                GET YOUR TICKETS
            </button>
        </div>
    </section>

    <!-- Achievements -->
    <section class="py-20 bg-gray-900">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-5xl font-black text-center mb-12 text-red-600">CHAMPIONS</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div class="bg-black p-8 rounded-lg border-2 border-red-600 text-center">
                    <div class="text-6xl font-black text-red-600 mb-4">15</div>
                    <div class="text-xl font-bold">WINS</div>
                </div>
                <div class="bg-black p-8 rounded-lg border-2 border-red-600 text-center">
                    <div class="text-6xl font-black text-red-600 mb-4">3</div>
                    <div class="text-xl font-bold">TITLES</div>
                </div>
                <div class="bg-black p-8 rounded-lg border-2 border-red-600 text-center">
                    <div class="text-6xl font-black text-red-600 mb-4">#1</div>
                    <div class="text-xl font-bold">RANKED</div>
                </div>
            </div>
        </div>
    </section>

    <!-- Player Gallery -->
    <section id="players" class="py-20 bg-black">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-5xl font-black text-center mb-12 text-red-600">WARRIORS</h2>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                {"".join([f'''
                <div class="relative group overflow-hidden rounded-lg">
                    <img src="{img}" alt="Player" class="w-full h-80 object-cover group-hover:scale-110 transition duration-300">
                    <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-0 group-hover:opacity-100 transition duration-300">
                        <div class="absolute bottom-0 p-6">
                            <h3 class="text-2xl font-black text-white">WARRIOR {i+1}</h3>
                            <p class="text-red-600 font-bold">ELITE ATHLETE</p>
                        </div>
                    </div>
                </div>
                ''' for i, img in enumerate(player_images[:4])])}
            </div>
        </div>
    </section>

    <!-- Schedule -->
    <section id="schedule" class="py-20 bg-gray-900">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-5xl font-black text-center mb-12 text-red-600">BATTLE SCHEDULE</h2>
            <div class="space-y-6">
                <div class="bg-black p-8 rounded-lg border-2 border-red-600">
                    <div class="flex justify-between items-center">
                        <div>
                            <h3 class="text-3xl font-black text-red-600">VS RIVAL TEAM</h3>
                            <p class="text-xl font-bold">HOME ADVANTAGE</p>
                        </div>
                        <div class="text-right">
                            <p class="text-2xl font-black">MARCH 15</p>
                            <p class="text-xl font-bold text-red-600">7:00 PM</p>
                        </div>
                    </div>
                </div>
                <div class="bg-black p-8 rounded-lg border-2 border-red-600">
                    <div class="flex justify-between items-center">
                        <div>
                            <h3 class="text-3xl font-black text-red-600">VS CONFERENCE LEADER</h3>
                            <p class="text-xl font-bold">AWAY BATTLE</p>
                        </div>
                        <div class="text-right">
                            <p class="text-2xl font-black">MARCH 22</p>
                            <p class="text-xl font-bold text-red-600">8:00 PM</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Stats -->
    <section id="stats" class="py-20 bg-black">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-5xl font-black text-center mb-12 text-red-600">DOMINANCE STATS</h2>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div class="text-center">
                    <div class="text-6xl font-black text-red-600">92%</div>
                    <p class="text-xl font-bold mt-2">WIN RATE</p>
                </div>
                <div class="text-center">
                    <div class="text-6xl font-black text-red-600">156</div>
                    <p class="text-xl font-bold mt-2">GOALS</p>
                </div>
                <div class="text-center">
                    <div class="text-6xl font-black text-red-600">45</div>
                    <p class="text-xl font-bold mt-2">ASSISTS</p>
                </div>
                <div class="text-center">
                    <div class="text-6xl font-black text-red-600">12</div>
                    <p class="text-xl font-bold mt-2">SHUTOUTS</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Final CTA -->
    <section id="tickets" class="py-20 bg-gradient-to-b from-red-600 to-black">
        <div class="max-w-4xl mx-auto text-center px-4">
            <h2 class="text-6xl font-black mb-6">JOIN THE ARMY</h2>
            <p class="text-2xl mb-8 font-bold">SUPPORT {business_name.upper()}</p>
            <button class="bg-white text-black px-12 py-6 rounded-lg text-2xl font-black hover:bg-gray-200 transition transform hover:scale-105">
                BUY TICKETS NOW
            </button>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-black text-white py-12 border-t-2 border-red-600">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <p class="text-xl font-bold">&copy; 2024 {business_name}. ALL RIGHTS RESERVED.</p>
        </div>
    </footer>
</body>
</html>
"""
        
        elif style == "minimalist":
            return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{business_name} - Excellence in Sport</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white text-gray-900">
    <!-- Navigation -->
    <nav class="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-4">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <span class="text-xl font-light text-blue-600">{business_name}</span>
                </div>
                <div class="flex items-center space-x-12">
                    <a href="#schedule" class="text-gray-600 hover:text-blue-600 text-sm">Schedule</a>
                    <a href="#players" class="text-gray-600 hover:text-blue-600 text-sm">Players</a>
                    <a href="#standings" class="text-gray-600 hover:text-blue-600 text-sm">Standings</a>
                    <a href="#tickets" class="text-gray-600 hover:text-blue-600 text-sm">Tickets</a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Hero -->
    <section class="relative h-96 flex items-center justify-center">
        <img src="{hero_images[0]}" alt="Sports" class="absolute inset-0 w-full h-full object-cover">
        <div class="absolute inset-0 bg-white bg-opacity-80"></div>
        <div class="relative text-center">
            <h1 class="text-4xl font-light mb-2">{business_name}</h1>
            <p class="text-lg text-gray-600 mb-6">Pursuit of Excellence</p>
            <button class="border border-blue-600 text-blue-600 px-6 py-2 hover:bg-blue-600 hover:text-white transition">
                View Schedule
            </button>
        </div>
    </section>

    <!-- Schedule & Standings -->
    <section class="py-16">
        <div class="max-w-6xl mx-auto px-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-12">
                <div>
                    <h2 class="text-2xl font-light mb-6">Upcoming Matches</h2>
                    <div class="space-y-3">
                        <div class="border-b border-gray-200 pb-3">
                            <div class="flex justify-between items-center">
                                <span class="text-sm">vs Team A</span>
                                <span class="text-xs text-gray-500">Mar 15 • 7:00 PM</span>
                            </div>
                        </div>
                        <div class="border-b border-gray-200 pb-3">
                            <div class="flex justify-between items-center">
                                <span class="text-sm">vs Team B</span>
                                <span class="text-xs text-gray-500">Mar 22 • 8:00 PM</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div>
                    <h2 class="text-2xl font-light mb-6">League Standings</h2>
                    <div class="space-y-2">
                        <div class="flex justify-between items-center py-2">
                            <span class="text-sm font-medium">1. {business_name}</span>
                            <span class="text-sm text-blue-600">45 pts</span>
                        </div>
                        <div class="flex justify-between items-center py-2">
                            <span class="text-sm">2. Team B</span>
                            <span class="text-sm text-gray-600">42 pts</span>
                        </div>
                        <div class="flex justify-between items-center py-2">
                            <span class="text-sm">3. Team C</span>
                            <span class="text-sm text-gray-600">38 pts</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Players -->
    <section id="players" class="py-16 bg-gray-50">
        <div class="max-w-6xl mx-auto px-4">
            <h2 class="text-2xl font-light text-center mb-12">Team Roster</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-8">
                {"".join([f'''
                <div class="text-center">
                    <img src="{img}" alt="Player" class="w-24 h-24 rounded-full mx-auto mb-3 object-cover">
                    <h3 class="text-sm font-medium">Player {i+1}</h3>
                    <p class="text-xs text-gray-500">Position</p>
                </div>
                ''' for i, img in enumerate(player_images[:4])])}
            </div>
        </div>
    </section>

    <!-- Stats -->
    <section id="standings" class="py-16">
        <div class="max-w-6xl mx-auto px-4">
            <h2 class="text-2xl font-light text-center mb-12">Season Statistics</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-8">
                <div class="text-center">
                    <div class="text-3xl font-light text-blue-600">15</div>
                    <p class="text-xs text-gray-500 mt-1">Wins</p>
                </div>
                <div class="text-center">
                    <div class="text-3xl font-light text-blue-600">92%</div>
                    <p class="text-xs text-gray-500 mt-1">Win Rate</p>
                </div>
                <div class="text-center">
                    <div class="text-3xl font-light text-blue-600">156</div>
                    <p class="text-xs text-gray-500 mt-1">Goals</p>
                </div>
                <div class="text-center">
                    <div class="text-3xl font-light text-blue-600">45</div>
                    <p class="text-xs text-gray-500 mt-1">Assists</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Tickets -->
    <section id="tickets" class="py-16 bg-blue-50">
        <div class="max-w-4xl mx-auto text-center px-4">
            <h2 class="text-3xl font-light mb-4">Support the Team</h2>
            <p class="text-gray-600 mb-8">Join us for an unforgettable experience</p>
            <button class="bg-blue-600 text-white px-8 py-3 hover:bg-blue-700 transition">
                Purchase Tickets
            </button>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-white border-t border-gray-200 py-8">
        <div class="max-w-6xl mx-auto px-4 text-center">
            <p class="text-sm text-gray-500">&copy; 2024 {business_name}</p>
        </div>
    </footer>
</body>
</html>
"""
        
        else:  # energetic_neon
            return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{business_name} - ELECTRIC SPORTS</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @keyframes neon {{
            0%, 100% {{ text-shadow: 0 0 10px #ff00ff, 0 0 20px #ff00ff, 0 0 30px #ff00ff; }}
            50% {{ text-shadow: 0 0 20px #00ffff, 0 0 30px #00ffff, 0 0 40px #00ffff; }}
        }}
        .neon-text {{ animation: neon 2s infinite; }}
        .neon-border {{ box-shadow: 0 0 20px #ff00ff, inset 0 0 20px #00ffff; }}
    </style>
</head>
<body class="bg-black text-white">
    <!-- Navigation -->
    <nav class="bg-black border-b-2 border-cyan-400 sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <span class="text-3xl font-black neon-text">{business_name}</span>
                </div>
                <div class="flex items-center space-x-8">
                    <a href="#schedule" class="text-cyan-400 hover:text-magenta-400 font-bold text-lg">SCHEDULE</a>
                    <a href="#players" class="text-cyan-400 hover:text-magenta-400 font-bold text-lg">PLAYERS</a>
                    <a href="#stats" class="text-cyan-400 hover:text-magenta-400 font-bold text-lg">STATS</a>
                    <a href="#tickets" class="text-cyan-400 hover:text-magenta-400 font-bold text-lg">TICKETS</a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Hero -->
    <section class="relative h-screen flex items-center justify-center overflow-hidden">
        <img src="{hero_images[0]}" alt="Sports" class="absolute inset-0 w-full h-full object-cover opacity-30">
        <div class="absolute inset-0 bg-gradient-to-r from-purple-900 via-black to-cyan-900 opacity-70"></div>
        <div class="relative text-center">
            <h1 class="text-8xl font-black mb-6 neon-text bg-gradient-to-r from-cyan-400 to-magenta-500 bg-clip-text text-transparent">
                {business_name.upper()}
            </h1>
            <p class="text-3xl mb-8 font-bold text-cyan-400">ELECTRIFYING PERFORMANCE</p>
            <button class="bg-gradient-to-r from-cyan-500 to-magenta-500 text-white px-12 py-6 rounded-lg text-2xl font-black hover:scale-110 transition-transform neon-border">
                GET AMPED • BUY TICKETS
            </button>
        </div>
    </section>

    <!-- Highlights -->
    <section class="py-20 bg-gradient-to-b from-black to-purple-900">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-6xl font-black text-center mb-12 neon-text">SEASON HIGHLIGHTS</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div class="bg-black p-8 rounded-lg neon-border text-center transform hover:scale-105 transition">
                    <div class="text-7xl font-black text-cyan-400 mb-4">15</div>
                    <div class="text-2xl font-bold text-magenta-400">VICTORIES</div>
                </div>
                <div class="bg-black p-8 rounded-lg neon-border text-center transform hover:scale-105 transition">
                    <div class="text-7xl font-black text-cyan-400 mb-4">3</div>
                    <div class="text-2xl font-bold text-magenta-400">TITLES</div>
                </div>
                <div class="bg-black p-8 rounded-lg neon-border text-center transform hover:scale-105 transition">
                    <div class="text-7xl font-black text-cyan-400 mb-4">#1</div>
                    <div class="text-2xl font-bold text-magenta-400">RANKED</div>
                </div>
            </div>
        </div>
    </section>

    <!-- Players -->
    <section id="players" class="py-20 bg-gradient-to-b from-purple-900 to-black">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-6xl font-black text-center mb-12 neon-text">SUPERSTARS</h2>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                {"".join([f'''
                <div class="relative group overflow-hidden rounded-lg neon-border transform hover:scale-110 transition">
                    <img src="{img}" alt="Player" class="w-full h-96 object-cover opacity-80 group-hover:opacity-100 transition">
                    <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-0 group-hover:opacity-100 transition">
                        <div class="absolute bottom-0 p-6">
                            <h3 class="text-3xl font-black text-cyan-400">STAR {i+1}</h3>
                            <p class="text-xl font-bold text-magenta-400">LEGEND</p>
                        </div>
                    </div>
                </div>
                ''' for i, img in enumerate(player_images[:4])])}
            </div>
        </div>
    </section>

    <!-- Schedule -->
    <section id="schedule" class="py-20 bg-black">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-6xl font-black text-center mb-12 neon-text">BATTLE ZONE</h2>
            <div class="space-y-6">
                <div class="bg-gradient-to-r from-purple-900 to-cyan-900 p-8 rounded-lg neon-border transform hover:scale-105 transition">
                    <div class="flex justify-between items-center">
                        <div>
                            <h3 class="text-4xl font-black text-cyan-400">VS RIVAL TEAM</h3>
                            <p class="text-xl font-bold text-magenta-400">HOME DOMINATION</p>
                        </div>
                        <div class="text-right">
                            <p class="text-3xl font-black text-white">MARCH 15</p>
                            <p class="text-2xl font-bold text-cyan-400">7:00 PM</p>
                        </div>
                    </div>
                </div>
                <div class="bg-gradient-to-r from-cyan-900 to-purple-900 p-8 rounded-lg neon-border transform hover:scale-105 transition">
                    <div class="flex justify-between items-center">
                        <div>
                            <h3 class="text-4xl font-black text-cyan-400">VS CONFERENCE LEADER</h3>
                            <p class="text-xl font-bold text-magenta-400">AWAY INVASION</p>
                        </div>
                        <div class="text-right">
                            <p class="text-3xl font-black text-white">MARCH 22</p>
                            <p class="text-2xl font-bold text-cyan-400">8:00 PM</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Stats -->
    <section id="stats" class="py-20 bg-gradient-to-b from-black to-purple-900">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-6xl font-black text-center mb-12 neon-text">DOMINANCE METRICS</h2>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div class="text-center transform hover:scale-110 transition">
                    <div class="text-7xl font-black text-cyan-400 neon-text">92%</div>
                    <p class="text-xl font-bold text-magenta-400 mt-2">WIN RATE</p>
                </div>
                <div class="text-center transform hover:scale-110 transition">
                    <div class="text-7xl font-black text-cyan-400 neon-text">156</div>
                    <p class="text-xl font-bold text-magenta-400 mt-2">GOALS</p>
                </div>
                <div class="text-center transform hover:scale-110 transition">
                    <div class="text-7xl font-black text-cyan-400 neon-text">45</div>
                    <p class="text-xl font-bold text-magenta-400 mt-2">ASSISTS</p>
                </div>
                <div class="text-center transform hover:scale-110 transition">
                    <div class="text-7xl font-black text-cyan-400 neon-text">12</div>
                    <p class="text-xl font-bold text-magenta-400 mt-2">SHUTOUTS</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Final CTA -->
    <section id="tickets" class="py-20 bg-gradient-to-r from-cyan-500 via-purple-500 to-magenta-500">
        <div class="max-w-4xl mx-auto text-center px-4">
            <h2 class="text-7xl font-black mb-6 text-white neon-text">JOIN THE MOVEMENT</h2>
            <p class="text-3xl mb-8 font-bold text-white">EXPERIENCE THE ELECTRICITY</p>
            <button class="bg-black text-white px-16 py-8 rounded-lg text-3xl font-black hover:scale-110 transition-transform neon-border">
                BUY TICKETS NOW
            </button>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-black text-white py-12 border-t-2 border-cyan-400">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <p class="text-2xl font-bold neon-text">&copy; 2024 {business_name}. ELECTRIC EXCELLENCE.</p>
        </div>
    </footer>
</body>
</html>
"""

    def _generate_restaurant_website(self, business_name: str, theme_name: str, theme_config: Dict) -> str:
        """Generate restaurant website with 4 different styles"""
        style_variants = ["elegant_light", "dark_luxury", "casual_bright", "modern_minimalist"]
        style = random.choice(style_variants)
        
        hero_images = self.get_real_images("restaurant_hero", 1)
        dish_images = self.get_real_images("restaurant_dishes", 12)
        
        colors = theme_config["colors"]
        
        if style == "elegant_light":
            return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{business_name} - Fine Dining Experience</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-amber-50 text-gray-900">
    <!-- Navigation -->
    <nav class="bg-white shadow-lg sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <span class="text-2xl font-serif text-amber-800">{business_name}</span>
                </div>
                <div class="flex items-center space-x-8">
                    <a href="#menu" class="text-gray-700 hover:text-amber-800">Menu</a>
                    <a href="#chef" class="text-gray-700 hover:text-amber-800">Our Chef</a>
                    <a href="#ambiance" class="text-gray-700 hover:text-amber-800">Ambiance</a>
                    <a href="#reservations" class="text-gray-700 hover:text-amber-800">Reservations</a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="relative h-screen flex items-center justify-center">
        <img src="{hero_images[0]}" alt="Restaurant" class="absolute inset-0 w-full h-full object-cover">
        <div class="absolute inset-0 bg-amber-900 bg-opacity-30"></div>
        <div class="relative text-center text-white">
            <h1 class="text-6xl font-serif mb-4">Welcome to {business_name}</h1>
            <p class="text-xl mb-8">An Exquisite Culinary Journey</p>
            <button class="bg-amber-800 hover:bg-amber-900 text-white px-8 py-4 rounded-lg text-lg font-semibold transition">
                Make a Reservation
            </button>
        </div>
    </section>

    <!-- Featured Dishes -->
    <section id="menu" class="py-20 bg-white">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-4xl font-serif text-center mb-12">Featured Dishes</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                {"".join([f'''
                <div class="text-center">
                    <img src="{img}" alt="Dish" class="w-full h-64 object-cover rounded-lg mb-4">
                    <h3 class="text-xl font-serif mb-2">Signature Dish {i+1}</h3>
                    <p class="text-gray-600 mb-4">Exquisite flavors prepared with the finest ingredients</p>
                    <p class="text-amber-800 font-semibold">$45</p>
                </div>
                ''' for i, img in enumerate(dish_images[:3])])}
            </div>
        </div>
    </section>

    <!-- Chef Section -->
    <section id="chef" class="py-20 bg-amber-50">
        <div class="max-w-4xl mx-auto px-4 text-center">
            <h2 class="text-4xl font-serif mb-8">Meet Our Executive Chef</h2>
            <div class="bg-white p-8 rounded-lg shadow-lg">
                <p class="text-lg text-gray-700 mb-6">
                    With over 20 years of culinary excellence, our chef brings passion and creativity to every dish. 
                    Trained in the finest kitchens of Europe, now sharing that expertise with you.
                </p>
                <p class="text-amber-800 font-semibold">Chef Michael Rodriguez</p>
            </div>
        </div>
    </section>

    <!-- Menu Highlights -->
    <section class="py-20 bg-white">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-4xl font-serif text-center mb-12">Menu Highlights</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-12">
                <div>
                    <h3 class="text-2xl font-serif mb-6 text-amber-800">Appetizers</h3>
                    {"".join([f'''
                    <div class="mb-4">
                        <div class="flex justify-between">
                            <h4 class="font-semibold">Appetizer {i+1}</h4>
                            <span class="text-amber-800">$18</span>
                        </div>
                        <p class="text-gray-600 text-sm">Fresh ingredients, perfect preparation</p>
                    </div>
                    ''' for i in range(3)])}
                </div>
                <div>
                    <h3 class="text-2xl font-serif mb-6 text-amber-800">Main Courses</h3>
                    {"".join([f'''
                    <div class="mb-4">
                        <div class="flex justify-between">
                            <h4 class="font-semibold">Main Course {i+1}</h4>
                            <span class="text-amber-800">$38</span>
                        </div>
                        <p class="text-gray-600 text-sm">Premium ingredients, expertly crafted</p>
                    </div>
                    ''' for i in range(3)])}
                </div>
            </div>
        </div>
    </section>

    <!-- Ambiance -->
    <section id="ambiance" class="py-20 bg-amber-50">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-4xl font-serif text-center mb-12">Experience the Ambiance</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                {"".join([f'''
                <img src="{img}" alt="Restaurant Ambiance" class="w-full h-64 object-cover rounded-lg">
                ''' for i, img in enumerate(dish_images[3:6])])}
            </div>
        </div>
    </section>

    <!-- Testimonials -->
    <section class="py-20 bg-white">
        <div class="max-w-4xl mx-auto px-4">
            <h2 class="text-4xl font-serif text-center mb-12">What Our Guests Say</h2>
            <div class="space-y-8">
                <div class="bg-amber-50 p-8 rounded-lg">
                    <p class="text-lg text-gray-700 mb-4">"An absolutely incredible dining experience. Every dish was a masterpiece."</p>
                    <p class="text-amber-800 font-semibold">- Sarah Johnson</p>
                </div>
                <div class="bg-amber-50 p-8 rounded-lg">
                    <p class="text-lg text-gray-700 mb-4">"The ambiance, service, and food were all exceptional. We'll be back!"</p>
                    <p class="text-amber-800 font-semibold">- Michael Chen</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Reservations CTA -->
    <section id="reservations" class="py-20 bg-amber-800 text-white">
        <div class="max-w-4xl mx-auto text-center px-4">
            <h2 class="text-4xl font-serif mb-4">Reserve Your Table</h2>
            <p class="text-xl mb-8">Join us for an unforgettable dining experience</p>
            <button class="bg-white text-amber-800 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-amber-50 transition">
                Book Now
            </button>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-900 text-white py-12">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <p>&copy; 2024 {business_name}. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>
"""

    def _generate_fitness_website(self, business_name: str, theme_name: str, theme_config: Dict) -> str:
        """Generate fitness website with 4 different styles"""
        style_variants = ["energetic_bright", "dark_professional", "minimal_clean", "gym_gallery"]
        style = random.choice(style_variants)
        
        hero_images = self.get_real_images("fitness_hero", 1)
        gym_images = self.get_real_images("fitness_gym", 8)
        
        if style == "energetic_bright":
            return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{business_name} - Transform Your Life</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white text-gray-900">
    <!-- Navigation -->
    <nav class="bg-red-600 text-white sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <span class="text-2xl font-black">{business_name.upper()}</span>
                </div>
                <div class="flex items-center space-x-8">
                    <a href="#programs" class="hover:text-yellow-300 font-bold">PROGRAMS</a>
                    <a href="#transformations" class="hover:text-yellow-300 font-bold">TRANSFORMATIONS</a>
                    <a href="#schedule" class="hover:text-yellow-300 font-bold">SCHEDULE</a>
                    <a href="#trial" class="hover:text-yellow-300 font-bold">FREE TRIAL</a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="relative h-screen flex items-center justify-center">
        <img src="{hero_images[0]}" alt="Fitness" class="absolute inset-0 w-full h-full object-cover">
        <div class="absolute inset-0 bg-red-600 bg-opacity-80"></div>
        <div class="relative text-center text-white">
            <h1 class="text-6xl font-black mb-6">TRANSFORM YOUR BODY</h1>
            <p class="text-2xl mb-8 font-bold">JOIN THE FITNESS REVOLUTION</p>
            <button class="bg-yellow-400 hover:bg-yellow-300 text-black px-10 py-5 rounded-lg text-xl font-black transition">
                START FREE TRIAL
            </button>
        </div>
    </section>

    <!-- Training Programs -->
    <section id="programs" class="py-20 bg-gray-100">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-5xl font-black text-center mb-12 text-red-600">TRAINING PROGRAMS</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div class="bg-white p-8 rounded-lg shadow-lg transform hover:scale-105 transition">
                    <img src="{gym_images[0]}" alt="Program" class="w-full h-48 object-cover rounded-lg mb-4">
                    <h3 class="text-2xl font-black text-red-600 mb-4">STRENGTH TRAINING</h3>
                    <p class="text-gray-700 mb-6">Build muscle and increase power with our expert trainers</p>
                    <button class="bg-red-600 text-white px-6 py-3 rounded-lg font-bold hover:bg-red-700">LEARN MORE</button>
                </div>
                <div class="bg-white p-8 rounded-lg shadow-lg transform hover:scale-105 transition">
                    <img src="{gym_images[1]}" alt="Program" class="w-full h-48 object-cover rounded-lg mb-4">
                    <h3 class="text-2xl font-black text-red-600 mb-4">CARDIO BLAST</h3>
                    <p class="text-gray-700 mb-6">Burn calories and improve endurance with high-energy workouts</p>
                    <button class="bg-red-600 text-white px-6 py-3 rounded-lg font-bold hover:bg-red-700">LEARN MORE</button>
                </div>
                <div class="bg-white p-8 rounded-lg shadow-lg transform hover:scale-105 transition">
                    <img src="{gym_images[2]}" alt="Program" class="w-full h-48 object-cover rounded-lg mb-4">
                    <h3 class="text-2xl font-black text-red-600 mb-4">YOGA FLOW</h3>
                    <p class="text-gray-700 mb-6">Find balance and flexibility with our yoga programs</p>
                    <button class="bg-red-600 text-white px-6 py-3 rounded-lg font-bold hover:bg-red-700">LEARN MORE</button>
                </div>
            </div>
        </div>
    </section>

    <!-- Free Trial CTA -->
    <section id="trial" class="py-20 bg-red-600 text-white">
        <div class="max-w-4xl mx-auto text-center px-4">
            <h2 class="text-5xl font-black mb-6">START YOUR FREE TRIAL</h2>
            <p class="text-2xl mb-8 font-bold">7 DAYS FREE - NO CREDIT CARD REQUIRED</p>
            <button class="bg-yellow-400 hover:bg-yellow-300 text-black px-12 py-6 rounded-lg text-2xl font-black transition">
                GET STARTED NOW
            </button>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-900 text-white py-12">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <p class="text-xl font-bold">&copy; 2024 {business_name}. TRANSFORM YOUR LIFE.</p>
        </div>
    </footer>
</body>
</html>
"""

    def _generate_ecommerce_website(self, business_name: str, theme_name: str, theme_config: Dict) -> str:
        """Generate e-commerce website with 4 different styles"""
        style_variants = ["luxury_dark", "bright_playful", "minimalist_white", "bold_brand"]
        style = random.choice(style_variants)
        
        product_images = self.get_real_images("ecommerce_products", 12)
        
        if style == "luxury_dark":
            return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{business_name} - Premium Collection</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-black text-white">
    <nav class="bg-black border-b border-gray-800 sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4">
            <div class="flex justify-between h-16">
                <span class="text-2xl font-serif">{business_name}</span>
                <div class="flex items-center space-x-8">
                    <a href="#products" class="hover:text-yellow-400">Products</a>
                    <a href="#collections" class="hover:text-yellow-400">Collections</a>
                    <a href="#contact" class="hover:text-yellow-400">Contact</a>
                </div>
            </div>
        </div>
    </nav>

    <section class="relative h-screen flex items-center justify-center">
        <div class="text-center">
            <h1 class="text-6xl font-serif mb-6">Exclusive Collection</h1>
            <p class="text-xl mb-8 text-gray-400">Discover luxury redefined</p>
            <button class="bg-yellow-600 hover:bg-yellow-500 text-black px-8 py-4 rounded-lg font-semibold">
                Shop Now
            </button>
        </div>
    </section>

    <section id="products" class="py-20 bg-gray-900">
        <div class="max-w-7xl mx-auto px-4">
            <h2 class="text-4xl font-serif text-center mb-12">Featured Products</h2>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                {"".join([f'''
                <div class="text-center group">
                    <img src="{img}" alt="Product" class="w-full h-80 object-cover rounded-lg mb-4 group-hover:scale-105 transition">
                    <h3 class="text-lg font-serif mb-2">Premium Item {i+1}</h3>
                    <p class="text-yellow-600 font-bold">$299</p>
                </div>
                ''' for i, img in enumerate(product_images[:4])])}
            </div>
        </div>
    </section>

    <footer class="bg-black text-white py-12 border-t border-gray-800">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <p>&copy; 2024 {business_name}. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>
"""

    def _generate_fallback_website(self, business_name: str) -> Dict:
        """Generate fallback website if something goes wrong"""
        fallback_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{business_name}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <div class="min-h-screen flex items-center justify-center">
        <div class="text-center">
            <h1 class="text-4xl font-bold mb-4">Welcome to {business_name}</h1>
            <p class="text-xl text-gray-600 mb-8">Your professional website is being prepared</p>
            <button class="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700">
                Contact Us
            </button>
        </div>
    </div>
</body>
</html>
"""
        
        return {
            "html": fallback_html,
            "metadata": {
                "business_name": business_name,
                "industry": "unknown",
                "theme": "Fallback",
                "theme_colors": {"primary": "#3B82F6", "secondary": "#F3F4F6"},
                "version": 1,
                "status": "fallback"
            }
        }
