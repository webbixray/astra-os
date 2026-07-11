export { TestRunner, describe } from './test-runner';
export type { TestConfig, TestResult, TestSuite, TestReport } from './test-runner';

export { ApiTestClient, runApiTests, expect } from './api-testing';
export type { ApiTestConfig, ApiTestResult, ApiTestCase } from './api-testing';

export {
  toMatchSnapshot,
  toMatchInlineSnapshot,
  createSnapshot,
  updateSnapshot,
  clearSnapshots,
  getSnapshot,
  hasSnapshot,
  toMatchObject,
  toContain,
  toHaveLength,
  toBeDefined,
  toBeNull,
  toBeTruthy,
  toBeFalsy,
  toEqual,
  toBeGreaterThan,
  toBeLessThan,
} from './snapshot-testing';

export { AccessibilityTester, testAccessibility, reportAccessibility } from './accessibility-testing';
export type { AccessibilityIssue, AccessibilityReport } from './accessibility-testing';

export { PerformanceTester, benchmark, measureMemory, measureAsyncMemory, reportPerformance } from './performance-testing';
export type { PerformanceTestConfig, PerformanceTestResult } from './performance-testing';

export {
  randomString,
  randomEmail,
  randomName,
  randomUrl,
  randomDate,
  randomInt,
  randomFloat,
  randomBoolean,
  randomArray,
  randomItem,
  generateUser,
  generateCampaign,
  generateContent,
  generateAnalyticsData,
  generateTeamMember,
  generateWorkflow,
  generateIntegration,
  generateInvoice,
  generateFAQItem,
} from './mock-generators';

export {
  generateJsonReport,
  generateHtmlReport,
  generateMarkdownReport,
  generateConsoleReport,
  saveReport,
} from './test-report';
export type { TestReportData } from './test-report';

export { VisualTester, visualTest, testVisualRegression, compareColors, analyzeScreenshot } from './visual-testing';
export type { VisualTestConfig, VisualTestResult } from './visual-testing';
