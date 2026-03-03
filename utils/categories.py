"""Keyword-based item categorizer for grocery deals."""

CATEGORY_KEYWORDS = {
    "Produce": [
        "apple", "banana", "orange", "grape", "strawberr", "blueberr", "raspberr",
        "avocado", "tomato", "potato", "onion", "lettuce", "spinach", "broccoli",
        "carrot", "pepper", "cucumber", "celery", "mushroom", "garlic", "lemon",
        "lime", "mango", "pineapple", "watermelon", "cantaloupe", "peach", "pear",
        "plum", "cherry", "kiwi", "zucchini", "squash", "corn", "cabbage", "salad",
        "herb", "cilantro", "parsley", "basil", "fruit", "vegetable", "veggie",
        "clementine", "nectarine", "grapefruit", "asparagus", "cauliflower", "beet",
    ],
    "Meat & Seafood": [
        "chicken", "beef", "pork", "steak", "ground", "salmon", "shrimp", "fish",
        "turkey", "sausage", "bacon", "ham", "lamb", "ribs", "roast", "tenderloin",
        "sirloin", "drumstick", "thigh", "breast", "wing", "tilapia", "cod", "tuna",
        "crab", "lobster", "meatball", "pepperoni", "deli meat", "prosciutto",
    ],
    "Dairy": [
        "milk", "cheese", "yogurt", "yoghurt", "butter", "cream", "egg", "sour cream",
        "cottage", "mozzarella", "cheddar", "parmesan", "whip", "margarine",
    ],
    "Bakery": [
        "bread", "bun", "bagel", "muffin", "croissant", "cake", "donut", "doughnut",
        "tortilla", "wrap", "pita", "roll", "loaf", "pastry", "cookie", "biscuit",
    ],
    "Pantry": [
        "rice", "pasta", "noodle", "sauce", "soup", "can", "bean", "oil", "vinegar",
        "flour", "sugar", "cereal", "oat", "granola", "honey", "jam", "peanut butter",
        "ketchup", "mustard", "mayo", "spice", "seasoning", "salt", "pepper",
        "broth", "stock", "canned", "taco", "salsa",
    ],
    "Snacks": [
        "chip", "cracker", "popcorn", "pretzel", "nut", "trail mix", "bar",
        "chocolate", "candy", "gummy", "snack", "granola bar", "protein bar",
    ],
    "Beverages": [
        "water", "juice", "pop", "soda", "coffee", "tea", "drink", "beverage",
        "kombucha", "smoothie", "lemonade", "energy drink", "sparkling",
    ],
    "Frozen": [
        "frozen", "ice cream", "pizza", "fries", "waffle", "popsicle", "freezer",
        "pierog", "pot pie",
    ],
    "Household": [
        "paper towel", "toilet paper", "tissue", "detergent", "soap", "cleaner",
        "garbage bag", "trash bag", "foil", "wrap", "sponge", "bleach", "lysol",
        "dish", "laundry", "dryer sheet", "fabric softener",
    ],
    "Baby & Personal": [
        "diaper", "wipe", "baby", "formula", "shampoo", "conditioner", "body wash",
        "deodorant", "toothpaste", "toothbrush", "lotion", "sunscreen", "razor",
    ],
}


def categorize_item(name: str) -> str:
    """Return a category for the given item name based on keyword matching."""
    lower = name.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                return category
    return "Other"
