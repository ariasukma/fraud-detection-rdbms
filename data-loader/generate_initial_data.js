import dotenv from 'dotenv';
import { createDbAdapter } from './db/index.js';
import { createBatch } from './transaction_factory.js';

dotenv.config();

const BATCH_SIZE = 500;
const TOTAL_ROWS = 5000;

async function main() {
  const adapter = await createDbAdapter();
  try {
    console.log(`Generating ${TOTAL_ROWS} training transactions for ${process.env.DB_TYPE || 'postgres'}...`);
    for (let inserted = 0; inserted < TOTAL_ROWS; inserted += BATCH_SIZE) {
      const rows = createBatch(Math.min(BATCH_SIZE, TOTAL_ROWS - inserted), { training: true });
      await adapter.insertTransactions(rows);
      console.log(`Inserted ${inserted + rows.length}/${TOTAL_ROWS}`);
    }
    console.log('Initial training data generated successfully.');
  } catch (error) {
    console.error('Failed to generate initial data:', error);
    process.exitCode = 1;
  } finally {
    await adapter.close();
  }
}

main();

