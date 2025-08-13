const bcrypt = require('bcryptjs');
const { query } = require('../database/connection');

class User {
  constructor(data) {
    this.id = data.id;
    this.username = data.username;
    this.email = data.email;
    this.firstName = data.first_name;
    this.lastName = data.last_name;
    this.createdAt = data.created_at;
    this.updatedAt = data.updated_at;
  }

  static async create({ username, email, password, firstName, lastName }) {
    const hashedPassword = await bcrypt.hash(password, 12);
    
    const result = await query(`
      INSERT INTO users (username, email, password_hash, first_name, last_name)
      VALUES ($1, $2, $3, $4, $5)
      RETURNING id, username, email, first_name, last_name, created_at, updated_at
    `, [username, email, hashedPassword, firstName, lastName]);

    return new User(result.rows[0]);
  }

  static async findByEmail(email) {
    const result = await query(`
      SELECT * FROM users WHERE email = $1
    `, [email]);

    return result.rows.length > 0 ? new User(result.rows[0]) : null;
  }

  static async findByUsername(username) {
    const result = await query(`
      SELECT * FROM users WHERE username = $1
    `, [username]);

    return result.rows.length > 0 ? new User(result.rows[0]) : null;
  }

  static async findById(id) {
    const result = await query(`
      SELECT * FROM users WHERE id = $1
    `, [id]);

    return result.rows.length > 0 ? new User(result.rows[0]) : null;
  }

  static async validatePassword(email, password) {
    const result = await query(`
      SELECT id, username, email, password_hash, first_name, last_name, created_at, updated_at 
      FROM users WHERE email = $1
    `, [email]);

    if (result.rows.length === 0) {
      return null;
    }

    const user = result.rows[0];
    const isValidPassword = await bcrypt.compare(password, user.password_hash);
    
    return isValidPassword ? new User(user) : null;
  }

  static async update(id, updates) {
    const allowedUpdates = ['first_name', 'last_name', 'email'];
    const setClause = [];
    const values = [];
    let paramIndex = 1;

    for (const [key, value] of Object.entries(updates)) {
      if (allowedUpdates.includes(key)) {
        setClause.push(`${key} = $${paramIndex}`);
        values.push(value);
        paramIndex++;
      }
    }

    if (setClause.length === 0) {
      throw new Error('No valid fields to update');
    }

    setClause.push(`updated_at = CURRENT_TIMESTAMP`);
    values.push(id);

    const result = await query(`
      UPDATE users 
      SET ${setClause.join(', ')}
      WHERE id = $${paramIndex}
      RETURNING id, username, email, first_name, last_name, created_at, updated_at
    `, values);

    return result.rows.length > 0 ? new User(result.rows[0]) : null;
  }

  static async delete(id) {
    const result = await query(`
      DELETE FROM users WHERE id = $1 RETURNING id
    `, [id]);

    return result.rows.length > 0;
  }

  toJSON() {
    return {
      id: this.id,
      username: this.username,
      email: this.email,
      firstName: this.firstName,
      lastName: this.lastName,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt
    };
  }
}

module.exports = User;