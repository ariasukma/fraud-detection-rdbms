import dotenv from 'dotenv';
import { createDbAdapter } from './db/index.js';
import { createTransaction } from './transaction_factory.js';

dotenv.config();

async function main() {
  const adapter = await createDbAdapter();
  console.log(`Realtime transaction generator started for ${process.env.DB_TYPE || 'postgres'}.`);
  const tick = async () => {
    try {
      const row = createTransaction({ training: false });
      await adapter.insertTransactions([row]);
      console.log(`Inserted realtime transaction ${row.transaction_id}`);
    } catch (error) {
      console.error('Failed to insert realtime transaction:', error);
    }
  };

  await tick();
  setInterval(tick, 1000);
}

main().catch((error) => {
  console.error('Realtime generator failed to start:', error);
  process.exit(1);
});

