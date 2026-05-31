const express = require('express');
const mysql = require('mysql2/promise');

const app = express();
app.use(express.json());

const DB_HOST = process.env.DB_HOST || 'localhost';
const DB_USER = process.env.DB_USER || 'dbadmin';
const DB_PASS = process.env.DB_PASS || '';

let pool;

const SSL_OPTS = DB_HOST !== 'localhost' && DB_HOST !== 'db' ? { rejectUnauthorized: false } : false;

async function connect(retries = 60) {
  for (let i = 0; i < retries; i++) {
    try {
      // Try connecting directly to the database (works when it already exists)
      // Falls back to CREATE DATABASE for fresh servers where dbadmin has superuser rights
      try {
        pool = mysql.createPool({ host: DB_HOST, user: DB_USER, password: DB_PASS, database: 'inventory', ssl: SSL_OPTS });
        await pool.query('SELECT 1');
      } catch {
        await pool.end();
        const init = await mysql.createConnection({ host: DB_HOST, user: DB_USER, password: DB_PASS, ssl: SSL_OPTS });
        await init.query('CREATE DATABASE IF NOT EXISTS inventory');
        await init.end();
        pool = mysql.createPool({ host: DB_HOST, user: DB_USER, password: DB_PASS, database: 'inventory', ssl: SSL_OPTS });
      }

      await pool.query(`
        CREATE TABLE IF NOT EXISTS items (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(255) NOT NULL,
          quantity INT NOT NULL DEFAULT 0,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);
      console.log('Database ready');
      return;
    } catch (err) {
      if (pool) { try { await pool.end(); } catch (_) {} pool = null; }
      console.log(`DB not ready, retrying (${i + 1}/${retries})... ${err.message}`);
      await new Promise(r => setTimeout(r, 3000));
    }
  }
  throw new Error('Could not connect to database after retries');
}

app.get('/api/items', async (req, res) => {
  const [rows] = await pool.query('SELECT * FROM items ORDER BY created_at DESC');
  res.json(rows);
});

app.post('/api/items', async (req, res) => {
  const { name, quantity } = req.body;
  if (!name || quantity === undefined) {
    return res.status(400).json({ error: 'name and quantity required' });
  }
  const [result] = await pool.query(
    'INSERT INTO items (name, quantity) VALUES (?, ?)',
    [name, Number(quantity)]
  );
  res.status(201).json({ id: result.insertId, name, quantity: Number(quantity) });
});

app.delete('/api/items/:id', async (req, res) => {
  const [result] = await pool.query('DELETE FROM items WHERE id = ?', [req.params.id]);
  if (result.affectedRows === 0) return res.status(404).json({ error: 'item not found' });
  res.status(204).end();
});

connect().then(() => app.listen(3000, () => console.log('Backend running on :3000')));
