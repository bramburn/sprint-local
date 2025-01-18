/**
 * Sample TypeScript file demonstrating various language features
 */

// Interface definition
interface User {
    id: number;
    name: string;
    email?: string;
}

// Type alias with union type
type Status = 'active' | 'inactive' | 'pending';

// Generic interface
interface Response<T> {
    data: T;
    status: Status;
    timestamp: Date;
}

/**
 * Sample class implementation with TypeScript features
 */
class UserService {
    private users: Map<number, User>;

    constructor() {
        this.users = new Map();
    }

    /**
     * Gets a user by ID
     * @param id The user ID
     * @returns Promise resolving to the user
     * @throws Error if user not found
     */
    async getUser(id: number): Promise<User> {
        const user = this.users.get(id);
        if (!user) {
            throw new Error(`User ${id} not found`);
        }
        return user;
    }

    /**
     * Creates a new user
     * @param userData The user data
     * @returns The created user
     */
    createUser(userData: Omit<User, 'id'>): User {
        const id = this.users.size + 1;
        const user: User = { ...userData, id };
        this.users.set(id, user);
        return user;
    }
}

// Decorators
function log(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;
    descriptor.value = async function(...args: any[]) {
        console.log(`Calling ${propertyKey} with args:`, args);
        const result = await originalMethod.apply(this, args);
        console.log(`${propertyKey} returned:`, result);
        return result;
    };
    return descriptor;
}

// Enum example
enum UserRole {
    Admin = 'ADMIN',
    User = 'USER',
    Guest = 'GUEST'
}

// Export for module usage
export { User, UserService, UserRole, Status, Response }; 