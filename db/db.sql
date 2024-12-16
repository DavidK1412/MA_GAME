CREATE TABLE difficulty (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    number_of_blocks INT NOT NULL
);

CREATE TABLE game (
    id VARCHAR(36) PRIMARY KEY,
    difficulty_id INT NOT NULL,
    created_at DATE DEFAULT CURRENT_DATE,
    init_time TIME(0) DEFAULT CURRENT_TIME,
    FOREIGN KEY (difficulty_id) REFERENCES difficulty(id)
);

CREATE TABLE movements (
    id VARCHAR(36) PRIMARY KEY,
    game_id VARCHAR(36) NOT NULL,
    movement_time TIME(0) DEFAULT CURRENT_TIME,
    step INT NOT NULL,
    movement VARCHAR(13)
);

INSERT INTO difficulty (name, number_of_blocks) VALUES ('easy', 7);