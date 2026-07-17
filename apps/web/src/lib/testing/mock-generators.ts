export function randomString(length: number = 10): string {
  return Math.random().toString(36).substring(2, 2 + length);
}

export function randomEmail(): string {
  return `${randomString(8)}@example.com`;
}

export function randomName(): string {
  const firstNames = ['John', 'Jane', 'Bob', 'Alice', 'Charlie', 'Diana', 'Eve', 'Frank'];
  const lastNames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis'];
  return `${firstNames[Math.floor(Math.random() * firstNames.length)]} ${lastNames[Math.floor(Math.random() * lastNames.length)]}`;
}

export function randomUrl(): string {
  return `https://${randomString(10)}.com`;
}

export function randomDate(start: Date = new Date(2020, 0, 1), end: Date = new Date()): Date {
  return new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime()));
}

export function randomInt(min: number = 0, max: number = 1000): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

export function randomFloat(min: number = 0, max: number = 100, decimals: number = 2): number {
  return parseFloat((Math.random() * (max - min) + min).toFixed(decimals));
}

export function randomBoolean(): boolean {
  return Math.random() > 0.5;
}

export function randomArray<T>(length: number, generator: (index: number) => T): T[] {
  return Array.from({ length }, (_, i) => generator(i));
}

export function randomItem<T>(array: T[]): T {
  return array[Math.floor(Math.random() * array.length)]!;
}

export function generateUser(overrides: Partial<{
  id: string;
  name: string;
  email: string;
  avatar: string;
  role: string;
  createdAt: Date;
}> = {}) {
  return {
    id: randomString(12),
    name: randomName(),
    email: randomEmail(),
    avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${randomString(5)}`,
    role: randomItem(['admin', 'editor', 'viewer']),
    createdAt: randomDate(),
    ...overrides,
  };
}

export function generateCampaign(overrides: Partial<{
  id: string;
  name: string;
  status: string;
  budget: number;
  spent: number;
  startDate: Date;
  endDate: Date;
}> = {}) {
  const startDate = randomDate(new Date(2024, 0, 1));
  const endDate = new Date(startDate.getTime() + randomInt(30, 90) * 24 * 60 * 60 * 1000);

  return {
    id: randomString(12),
    name: `Campaign ${randomString(5)}`,
    status: randomItem(['draft', 'active', 'paused', 'completed']),
    budget: randomInt(1000, 50000),
    spent: randomInt(0, 10000),
    startDate,
    endDate,
    ...overrides,
  };
}

export function generateContent(overrides: Partial<{
  id: string;
  title: string;
  type: string;
  status: string;
  author: string;
  publishedAt: Date;
  tags: string[];
}> = {}) {
  return {
    id: randomString(12),
    title: `Content ${randomString(5)}`,
    type: randomItem(['blog', 'social', 'email', 'video']),
    status: randomItem(['draft', 'review', 'published']),
    author: randomName(),
    publishedAt: randomDate(),
    tags: randomArray(randomInt(1, 4), () => randomString(6)),
    ...overrides,
  };
}

export function generateAnalyticsData() {
  return {
    visitors: randomInt(10000, 100000),
    pageViews: randomInt(50000, 500000),
    bounceRate: randomFloat(20, 60),
    avgSessionDuration: randomInt(60, 300),
    conversions: randomInt(100, 1000),
    conversionRate: randomFloat(1, 5),
    revenue: randomInt(10000, 100000),
    topPages: randomArray(5, (_i) => ({
      path: `/page-${randomString(5)}`,
      views: randomInt(1000, 10000),
      percentage: randomFloat(5, 25),
    })),
    trafficSources: [
      { source: 'Organic', visitors: randomInt(5000, 20000), percentage: randomFloat(30, 50) },
      { source: 'Direct', visitors: randomInt(2000, 10000), percentage: randomFloat(15, 25) },
      { source: 'Social', visitors: randomInt(1000, 5000), percentage: randomFloat(5, 15) },
      { source: 'Referral', visitors: randomInt(500, 3000), percentage: randomFloat(3, 10) },
    ],
  };
}

export function generateTeamMember(overrides: Partial<{
  id: string;
  name: string;
  email: string;
  role: string;
  status: string;
  lastActive: Date;
}> = {}) {
  return {
    id: randomString(12),
    name: randomName(),
    email: randomEmail(),
    role: randomItem(['owner', 'admin', 'editor', 'viewer']),
    status: randomItem(['active', 'invited', 'inactive']),
    lastActive: randomDate(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)),
    ...overrides,
  };
}

export function generateWorkflow(overrides: Partial<{
  id: string;
  name: string;
  status: string;
  steps: Array<{ id: string; type: string; name: string }>;
  createdAt: Date;
  runCount: number;
  successRate: number;
}> = {}) {
  return {
    id: randomString(12),
    name: `Workflow ${randomString(5)}`,
    status: randomItem(['draft', 'active', 'paused']),
    steps: randomArray(randomInt(3, 8), (i) => ({
      id: randomString(8),
      type: randomItem(['trigger', 'action', 'condition', 'delay']),
      name: `Step ${i + 1}`,
    })),
    createdAt: randomDate(),
    runCount: randomInt(0, 100),
    successRate: randomFloat(80, 100),
    ...overrides,
  };
}

export function generateIntegration(overrides: Partial<{
  id: string;
  name: string;
  description: string;
  category: string;
  status: string;
}> = {}) {
  return {
    id: randomString(12),
    name: `Integration ${randomString(5)}`,
    description: `Description for integration ${randomString(5)}`,
    category: randomItem(['advertising', 'analytics', 'crm', 'email', 'social']),
    status: randomItem(['connected', 'available', 'coming_soon']),
    ...overrides,
  };
}

export function generateInvoice(overrides: Partial<{
  id: string;
  date: Date;
  amount: number;
  status: string;
  description: string;
}> = {}) {
  return {
    id: randomString(12),
    date: randomDate(),
    amount: randomFloat(10, 500),
    status: randomItem(['paid', 'pending', 'failed']),
    description: `Invoice for ${randomString(5)}`,
    ...overrides,
  };
}

export function generateFAQItem(overrides: Partial<{
  id: string;
  question: string;
  answer: string;
  category: string;
}> = {}) {
  return {
    id: randomString(12),
    question: `Question ${randomString(5)}?`,
    answer: `Answer for question ${randomString(5)}. This is a detailed explanation.`,
    category: randomItem(['General', 'Billing', 'Technical', 'Account']),
    ...overrides,
  };
}
