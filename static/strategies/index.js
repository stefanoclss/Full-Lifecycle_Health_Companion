import { BaseStrategy } from './base_strategy.js?v=8';
import { HomeTriageStrategy } from './home_triage.js?v=8';

// Strategy Registry
const strategies = {
    'home_triage': HomeTriageStrategy,
    // Add others here as needed, falling back to BaseStrategy if not found
    'default': BaseStrategy
};

export function getStrategy(id, metadata) {
    const StrategyClass = strategies[id] || strategies['default'];
    return new StrategyClass(metadata);
}
