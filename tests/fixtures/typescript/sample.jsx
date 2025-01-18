import React from 'react';

// Simple React component in JSX
function Greeting({ name, onGreet }) {
    const handleClick = () => {
        onGreet(`Hello, ${name}!`);
    };

    return (
        <div className="greeting">
            <h2>Welcome, {name}!</h2>
            <button onClick={handleClick}>
                Say Hello
            </button>
        </div>
    );
}

// Class component example
class Counter extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            count: props.initialCount || 0
        };
    }

    increment = () => {
        this.setState(prevState => ({
            count: prevState.count + 1
        }));
    };

    render() {
        return (
            <div className="counter">
                <p>Count: {this.state.count}</p>
                <button onClick={this.increment}>
                    Increment
                </button>
            </div>
        );
    }
}

// Higher-order component
function withTheme(Component) {
    return function ThemedComponent(props) {
        const theme = {
            background: '#f0f0f0',
            color: '#333'
        };

        return (
            <div style={theme}>
                <Component {...props} />
            </div>
        );
    };
}

export { Greeting, Counter, withTheme }; 