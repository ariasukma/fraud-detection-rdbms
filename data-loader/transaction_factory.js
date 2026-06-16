import { faker } from '@faker-js/faker';

const highRiskCountries = ['North Korea', 'Iran', 'Syria', 'Russia'];
const countries = ['Indonesia', 'Singapore', 'Malaysia', 'United States', 'United Kingdom', 'Japan', ...highRiskCountries];
const fraudTypes = [
  'HIGH_AMOUNT_ANOMALY',
  'NEW_DEVICE_FRAUD',
  'ACCOUNT_TAKEOVER',
  'NEW_BENEFICIARY_FRAUD',
  'VELOCITY_FRAUD',
  'GEO_ANOMALY',
  'CROSS_BORDER_HIGH_RISK',
  'VPN_PROXY_FRAUD',
  'HIGH_RISK_MERCHANT',
  'DORMANT_ACCOUNT_FRAUD'
];

function pick(items) {
  return faker.helpers.arrayElement(items);
}

function evaluateFraud(row) {
  const checks = [
    ['HIGH_AMOUNT_ANOMALY', row.amount > row.avg_transaction_amount_30d * 5],
    ['NEW_DEVICE_FRAUD', row.is_new_device && row.device_change_count_24h >= 3],
    ['ACCOUNT_TAKEOVER', row.failed_login_count_24h >= 5 && row.password_change_recently],
    ['NEW_BENEFICIARY_FRAUD', row.beneficiary_is_new && row.beneficiary_age_days <= 3],
    ['VELOCITY_FRAUD', row.transaction_count_1h >= 8 || row.transaction_count_24h >= 30],
    ['GEO_ANOMALY', row.distance_from_last_location_km > 1200 && row.minutes_since_last_transaction <= 15],
    ['CROSS_BORDER_HIGH_RISK', row.is_cross_border && highRiskCountries.includes(row.destination_country)],
    ['VPN_PROXY_FRAUD', row.is_vpn || row.is_proxy || row.ip_risk_score >= 80],
    ['HIGH_RISK_MERCHANT', row.merchant_risk_level === 'HIGH'],
    ['DORMANT_ACCOUNT_FRAUD', row.days_since_last_transaction >= 180 && row.amount > row.avg_transaction_amount_30d * 3]
  ];
  const hit = checks.find(([, matched]) => matched);
  const randomNoise = faker.number.float({ min: 0, max: 1 }) > 0.985;
  return {
    isFraud: Boolean(hit || randomNoise),
    fraudType: hit ? hit[0] : randomNoise ? pick(fraudTypes) : null
  };
}

export function createTransaction({ training = false } = {}) {
  const now = faker.date.recent({ days: 10 });
  const sourceCountry = pick(countries);
  const destinationCountry = faker.helpers.maybe(() => pick(countries), { probability: 0.25 }) || sourceCountry;
  const avg = faker.number.float({ min: 20, max: 1200, fractionDigits: 2 });
  const spike = faker.helpers.maybe(() => faker.number.float({ min: avg * 5, max: avg * 20, fractionDigits: 2 }), { probability: 0.08 });
  const row = {
    transaction_id: faker.string.uuid(),
    customer_id: `CUST-${faker.string.alphanumeric({ length: 10, casing: 'upper' })}`,
    customer_name: faker.person.fullName(),
    email: faker.internet.email(),
    phone_number: faker.phone.number(),
    amount: spike || faker.number.float({ min: 5, max: avg * 2.5, fractionDigits: 2 }),
    currency: pick(['IDR', 'USD', 'SGD', 'MYR', 'EUR']),
    transaction_type: pick(['TRANSFER', 'PAYMENT', 'WITHDRAWAL', 'PURCHASE']),
    transaction_channel: pick(['MOBILE', 'WEB', 'ATM', 'POS', 'API']),
    transaction_time: now,
    hour_of_day: now.getHours(),
    day_of_week: now.getDay(),
    account_age_days: faker.number.int({ min: 1, max: 2500 }),
    kyc_status: pick(['VERIFIED', 'PENDING', 'REJECTED']),
    customer_risk_level: pick(['LOW', 'MEDIUM', 'HIGH']),
    merchant_id: `MER-${faker.string.alphanumeric({ length: 8, casing: 'upper' })}`,
    merchant_category: pick(['RETAIL', 'TRAVEL', 'CRYPTO', 'GAMING', 'ELECTRONICS']),
    merchant_country: pick(countries),
    merchant_risk_level: pick(['LOW', 'MEDIUM', 'HIGH']),
    device_id: `DEV-${faker.string.uuid()}`,
    device_type: pick(['PHONE', 'TABLET', 'LAPTOP', 'DESKTOP']),
    device_os: pick(['iOS', 'Android', 'Windows', 'macOS', 'Linux']),
    is_new_device: faker.datatype.boolean({ probability: 0.16 }),
    device_change_count_24h: faker.number.int({ min: 0, max: 6 }),
    ip_address: faker.internet.ip(),
    ip_country: pick(countries),
    ip_city: faker.location.city(),
    is_vpn: faker.datatype.boolean({ probability: 0.08 }),
    is_proxy: faker.datatype.boolean({ probability: 0.06 }),
    ip_risk_score: faker.number.float({ min: 0, max: 100, fractionDigits: 2 }),
    source_country: sourceCountry,
    destination_country: destinationCountry,
    is_cross_border: sourceCountry !== destinationCountry,
    avg_transaction_amount_30d: avg,
    transaction_count_1h: faker.number.int({ min: 0, max: 12 }),
    transaction_count_24h: faker.number.int({ min: 1, max: 45 }),
    failed_login_count_24h: faker.number.int({ min: 0, max: 8 }),
    password_change_recently: faker.datatype.boolean({ probability: 0.08 }),
    beneficiary_is_new: faker.datatype.boolean({ probability: 0.18 }),
    beneficiary_age_days: faker.number.int({ min: 0, max: 1500 }),
    distance_from_last_location_km: faker.number.float({ min: 0, max: 5000, fractionDigits: 2 }),
    minutes_since_last_transaction: faker.number.int({ min: 1, max: 10080 }),
    days_since_last_transaction: faker.number.int({ min: 0, max: 365 })
  };
  const label = evaluateFraud(row);
  return {
    ...row,
    is_fraud: training ? label.isFraud : null,
    fraud_type: training ? label.fraudType : null,
    fraud_score: training ? (label.isFraud ? faker.number.float({ min: 0.75, max: 0.99, fractionDigits: 4 }) : faker.number.float({ min: 0.01, max: 0.45, fractionDigits: 4 })) : null,
    prediction_status: training ? 'TRAINING' : 'PENDING',
    predicted_at: null,
    created_at: new Date()
  };
}

export function createBatch(size, options) {
  return Array.from({ length: size }, () => createTransaction(options));
}

