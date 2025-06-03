CREATE TABLE difficulty (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    number_of_blocks INT NOT NULL
);

CREATE TABLE game (
    id VARCHAR(36) PRIMARY KEY,
    is_finished BOOLEAN NOT NULL DEFAULT FALSE,
    buclicity_avg FLOAT DEFAULT 0,
    branch_factor_avg FLOAT DEFAULT 0,
);

CREATE TABLE game_attempts (
    id VARCHAR(36) PRIMARY KEY,
    game_id VARCHAR(36) NOT NULL,
    difficulty_id INT NOT NULL,
    last_buclicity FLOAT NOT NULL DEFAULT 0,
    last_branch_factor FLOAT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (game_id) REFERENCES game(id),
    FOREIGN KEY (difficulty_id) REFERENCES difficulty(id)
)

CREATE TABLE movements (
    id VARCHAR(36) PRIMARY KEY,
    attempt_id VARCHAR(36) NOT NULL,
    movement_time TIME(0) DEFAULT CURRENT_TIME,
    step INT NOT NULL,
    movement VARCHAR(20),
    is_correct BOOLEAN NOT NULL DEFAULT FALSE,
    interuption BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (attempt_id) REFERENCES game_attempts(id)
);

CREATE TABLE movements_misses (
    id VARCHAR(36) PRIMARY KEY,
    game_attempt_id VARCHAR(36) NOT NULL,
    count INT NOT NULL,
    FOREIGN KEY (game_attempt_id) REFERENCES game_attempts(id)
)

-- [_, _, _, _, _, _, _] easy
-- [_, _, _, _, _, _, _, _, _] medium
-- [_, _, _, _, _, _, _, _, _, _, _] hard
-- [10, 9, 8, 7, 6, 0, 1, 2, 3, 4, 5]

INSERT INTO difficulty (name, number_of_blocks) VALUES ('easy', 7);
INSERT INTO difficulty (name, number_of_blocks) VALUES ('medium', 9);
INSERT INTO difficulty (name, number_of_blocks) VALUES ('hard', 12);