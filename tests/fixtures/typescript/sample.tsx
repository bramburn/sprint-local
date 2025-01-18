import React, { useState, useEffect } from 'react';

// Props interface
interface UserListProps {
    initialUsers?: User[];
    onUserSelect?: (user: User) => void;
}

// User type from previous file
interface User {
    id: number;
    name: string;
    email?: string;
}

/**
 * Sample React component with TypeScript
 */
const UserList: React.FC<UserListProps> = ({ initialUsers = [], onUserSelect }) => {
    const [users, setUsers] = useState<User[]>(initialUsers);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchUsers = async () => {
            setLoading(true);
            try {
                const response = await fetch('/api/users');
                const data = await response.json();
                setUsers(data);
            } catch (error) {
                console.error('Failed to fetch users:', error);
            } finally {
                setLoading(false);
            }
        };

        if (users.length === 0) {
            fetchUsers();
        }
    }, []);

    if (loading) {
        return <div>Loading users...</div>;
    }

    return (
        <div className="user-list">
            {users.map((user) => (
                <div
                    key={user.id}
                    onClick={() => onUserSelect?.(user)}
                    className="user-item"
                >
                    <h3>{user.name}</h3>
                    {user.email && <p>{user.email}</p>}
                </div>
            ))}
        </div>
    );
};

// Higher-order component example
function withLogging<P extends object>(
    WrappedComponent: React.ComponentType<P>
): React.FC<P> {
    return function WithLoggingComponent(props: P) {
        useEffect(() => {
            console.log('Component mounted with props:', props);
            return () => console.log('Component will unmount');
        }, []);

        return <WrappedComponent {...props} />;
    };
}

// Custom hook with TypeScript
function useUserData(userId: number) {
    const [user, setUser] = useState<User | null>(null);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const response = await fetch(`/api/users/${userId}`);
                const data = await response.json();
                setUser(data);
            } catch (err) {
                setError(err instanceof Error ? err : new Error('Unknown error'));
            }
        };

        fetchUser();
    }, [userId]);

    return { user, error };
}

export { UserList, withLogging, useUserData }; 