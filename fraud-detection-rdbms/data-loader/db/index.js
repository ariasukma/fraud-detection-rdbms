import dotenv from 'dotenv';
dotenv.config();

const adapters = {
  postgres: () => import('./postgres.js'),
  cockroachdb: () => import('./cockroachdb.js'),
  mysql: () => import('./mysql.js'),
  oracle: () => import('./oracle.js'),
  sqlserver: () => import('./sqlserver.js')
};

export async function createDbAdapter() {
  const dbType = process.env.DB_TYPE || 'postgres';
  const loader = adapters[dbType];
  if (!loader) {
    throw new Error(`Unsupported DB_TYPE: ${dbType}`);
  }
  const module = await loader();
  return module.createAdapter();
}

