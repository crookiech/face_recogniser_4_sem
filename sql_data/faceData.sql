CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE face_models (
    model_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    model_data BYTEA NOT NULL
);