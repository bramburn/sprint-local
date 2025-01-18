/**
 * @typedef {Object} Product
 * @property {number} id - The product ID
 * @property {string} name - The product name
 * @property {number} price - The product price
 * @property {string[]} categories - Product categories
 */

/**
 * @typedef {Object} CartItem
 * @property {Product} product - The product in the cart
 * @property {number} quantity - Quantity of the product
 */

/**
 * Represents a shopping cart
 */
class ShoppingCart {
    constructor() {
        /** @type {CartItem[]} */
        this.items = [];
    }

    /**
     * Add a product to the cart
     * @param {Product} product - The product to add
     * @param {number} [quantity=1] - The quantity to add
     * @returns {void}
     * @throws {Error} If product is invalid
     */
    addItem(product, quantity = 1) {
        if (!product || !product.id) {
            throw new Error('Invalid product');
        }

        const existingItem = this.items.find(item => item.product.id === product.id);
        if (existingItem) {
            existingItem.quantity += quantity;
        } else {
            this.items.push({ product, quantity });
        }
    }

    /**
     * Calculate the total price of items in the cart
     * @returns {number} The total price
     */
    getTotal() {
        return this.items.reduce((total, item) => {
            return total + (item.product.price * item.quantity);
        }, 0);
    }

    /**
     * Get a summary of the cart
     * @returns {Object} Cart summary
     * @property {number} totalItems - Total number of items
     * @property {number} totalPrice - Total price
     * @property {string[]} uniqueCategories - List of unique categories
     */
    getSummary() {
        const totalItems = this.items.reduce((sum, item) => sum + item.quantity, 0);
        const totalPrice = this.getTotal();
        const uniqueCategories = [...new Set(
            this.items.flatMap(item => item.product.categories)
        )];

        return {
            totalItems,
            totalPrice,
            uniqueCategories
        };
    }
}

// Example async function with JSDoc
/**
 * Fetch product data from API
 * @async
 * @param {number} productId - The ID of the product to fetch
 * @returns {Promise<Product>} The product data
 * @throws {Error} If the product is not found
 */
async function fetchProduct(productId) {
    const response = await fetch(`/api/products/${productId}`);
    if (!response.ok) {
        throw new Error(`Product ${productId} not found`);
    }
    return response.json();
}

export { ShoppingCart, fetchProduct }; 