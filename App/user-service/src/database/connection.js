const { Client } = require('pg');
const logger = require('../utils/logger');

let client;

const connectDB = async () => {
  try {
    client = new Client({
      host: process.env.DB_HOST || 'localhost',
      port: process.env.DB_PORT || 5432,
      database: process.env.DB_NAME || 'taskmanager',
      user: process.env.DB_USER || 'dbadmin',
      password: process.env.DB_PASSWORD || 'SecurePassword123!',
      ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
    });

    await client.connect();
    logger.info('Connected to PostgreSQL database');
    
    // Create users table if it doesn't exist
    await initializeSchema();
    
    return client;
  } catch (error) {
    logger.error('Database connection error:', error);
    throw error;
  }
};

const initializeSchema = async () => {
  const createUsersTable = `
    CREATE TABLE IF NOT EXISTS users (
      id SERIAL PRIMARY KEY,
      username VARCHAR(50) UNIQUE NOT NULL,
      email VARCHAR(100) UNIQUE NOT NULL,
      password_hash VARCHAR(255) NOT NULL,
      first_name VARCHAR(50),
      last_name VARCHAR(50),
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
  `;

  try {
    await client.query(createUsersTable);
    logger.info('Users table initialized');
  } catch (error) {
    logger.error('Schema initialization error:', error);
    throw error;
  }
};

const query = async (text, params) => {
  try {
    const result = await client.query(text, params);
    return result;
  } catch (error) {
    logger.error('Database query error:', error);
    throw error;
  }
};

module.exports = {
  connectDB,
  query,
  client: () => client
};
