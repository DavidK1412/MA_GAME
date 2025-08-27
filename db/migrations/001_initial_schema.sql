-- Initial database schema for Frog Game
-- Migration: 001_initial_schema

-- Create difficulty table
CREATE TABLE IF NOT EXISTS difficulty (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    number_of_blocks INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create game table
CREATE TABLE IF NOT EXISTS game (
    id VARCHAR(36) PRIMARY KEY,
    is_finished BOOLEAN NOT NULL DEFAULT FALSE,
    buclicity_avg FLOAT DEFAULT 0,
    branch_factor_avg FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create game_attempts table
CREATE TABLE IF NOT EXISTS game_attempts (
    id VARCHAR(36) PRIMARY KEY,
    game_id VARCHAR(36) NOT NULL,
    difficulty_id INT NOT NULL,
    last_buclicity FLOAT NOT NULL DEFAULT 0,
    last_branch_factor FLOAT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    total_steps INT DEFAULT 0,
    successful_moves INT DEFAULT 0,
    failed_moves INT DEFAULT 0,
    FOREIGN KEY (game_id) REFERENCES game(id) ON DELETE CASCADE,
    FOREIGN KEY (difficulty_id) REFERENCES difficulty(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create movements table
CREATE TABLE IF NOT EXISTS movements (
    id VARCHAR(36) PRIMARY KEY,
    attempt_id VARCHAR(36) NOT NULL,
    movement_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    step INT NOT NULL,
    movement VARCHAR(255) NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE,
    interuption BOOLEAN NOT NULL DEFAULT FALSE,
    execution_time FLOAT NULL,
    FOREIGN KEY (attempt_id) REFERENCES game_attempts(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create movements_misses table
CREATE TABLE IF NOT EXISTS movements_misses (
    id VARCHAR(36) PRIMARY KEY,
    game_attempt_id VARCHAR(36) NOT NULL,
    count INT NOT NULL DEFAULT 1,
    FOREIGN KEY (game_attempt_id) REFERENCES game_attempts(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_game_attempts_game_id ON game_attempts(game_id);
CREATE INDEX IF NOT EXISTS idx_game_attempts_active ON game_attempts(is_active);
CREATE INDEX IF NOT EXISTS idx_movements_attempt_id ON movements(attempt_id);
CREATE INDEX IF NOT EXISTS idx_movements_step ON movements(step);
CREATE INDEX IF NOT EXISTS idx_movements_misses_attempt_id ON movements_misses(game_attempt_id);

-- Insert initial difficulty levels
INSERT INTO difficulty (name, number_of_blocks) VALUES 
    ('easy', 7),
    ('medium', 9), 
    ('hard', 11)
ON CONFLICT (id) DO NOTHING;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_game_updated_at 
    BEFORE UPDATE ON game 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_game_attempts_updated_at 
    BEFORE UPDATE ON game_attempts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_movements_misses_updated_at 
    BEFORE UPDATE ON movements_misses 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
