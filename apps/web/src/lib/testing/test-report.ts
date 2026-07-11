export interface TestReportData {
  timestamp: number;
  duration: number;
  totalTests: number;
  passed: number;
  failed: number;
  skipped: number;
  suites: {
    name: string;
    tests: {
      name: string;
      status: 'passed' | 'failed' | 'skipped';
      duration: number;
      error?: string;
    }[];
  }[];
}

export function generateJsonReport(data: TestReportData): string {
  return JSON.stringify(data, null, 2);
}

export function generateHtmlReport(data: TestReportData): string {
  const passRate = ((data.passed / data.totalTests) * 100).toFixed(1);

  return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Test Report</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }
    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    h1 { color: #333; margin-bottom: 8px; }
    .summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 24px 0; }
    .stat { padding: 20px; border-radius: 8px; text-align: center; }
    .stat-value { font-size: 32px; font-weight: bold; }
    .stat-label { font-size: 14px; color: #666; margin-top: 4px; }
    .passed { background: #d4edda; color: #155724; }
    .failed { background: #f8d7da; color: #721c24; }
    .skipped { background: #fff3cd; color: #856404; }
    .total { background: #d1ecf1; color: #0c5460; }
    .suite { margin: 24px 0; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }
    .suite-header { padding: 16px; background: #f8f9fa; border-bottom: 1px solid #ddd; font-weight: 600; }
    .test { padding: 12px 16px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
    .test:last-child { border-bottom: none; }
    .test-name { flex: 1; }
    .test-status { padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 500; }
    .test-status.passed { background: #d4edda; color: #155724; }
    .test-status.failed { background: #f8d7da; color: #721c24; }
    .test-status.skipped { background: #fff3cd; color: #856404; }
    .test-duration { color: #666; font-size: 12px; margin-left: 16px; }
    .error { margin-top: 8px; padding: 12px; background: #f8f9fa; border-radius: 4px; font-family: monospace; font-size: 12px; color: #721c24; }
    .footer { margin-top: 32px; padding-top: 16px; border-top: 1px solid #ddd; color: #666; font-size: 12px; text-align: center; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Test Report</h1>
    <p>Generated: ${new Date(data.timestamp).toLocaleString()}</p>
    
    <div class="summary">
      <div class="stat total">
        <div class="stat-value">${data.totalTests}</div>
        <div class="stat-label">Total Tests</div>
      </div>
      <div class="stat passed">
        <div class="stat-value">${data.passed}</div>
        <div class="stat-label">Passed (${passRate}%)</div>
      </div>
      <div class="stat failed">
        <div class="stat-value">${data.failed}</div>
        <div class="stat-label">Failed</div>
      </div>
      <div class="stat skipped">
        <div class="stat-value">${data.skipped}</div>
        <div class="stat-label">Skipped</div>
      </div>
    </div>

    ${data.suites
      .map(
        (suite) => `
      <div class="suite">
        <div class="suite-header">${suite.name}</div>
        ${suite.tests
          .map(
            (test) => `
          <div class="test">
            <div class="test-name">
              ${test.name}
              ${test.error ? `<div class="error">${test.error}</div>` : ''}
            </div>
            <span class="test-duration">${test.duration}ms</span>
            <span class="test-status ${test.status}">${test.status}</span>
          </div>
        `,
          )
          .join('')}
      </div>
    `,
      )
      .join('')}

    <div class="footer">
      <p>Duration: ${data.duration}ms | Pass Rate: ${passRate}%</p>
    </div>
  </div>
</body>
</html>
  `;
}

export function generateMarkdownReport(data: TestReportData): string {
  const passRate = ((data.passed / data.totalTests) * 100).toFixed(1);

  let report = `# Test Report\n\n`;
  report += `Generated: ${new Date(data.timestamp).toLocaleString()}\n\n`;
  report += `## Summary\n\n`;
  report += `| Metric | Value |\n|--------|-------|\n`;
  report += `| Total Tests | ${data.totalTests} |\n`;
  report += `| Passed | ${data.passed} (${passRate}%) |\n`;
  report += `| Failed | ${data.failed} |\n`;
  report += `| Skipped | ${data.skipped} |\n`;
  report += `| Duration | ${data.duration}ms |\n\n`;

  report += `## Test Suites\n\n`;

  data.suites.forEach((suite) => {
    report += `### ${suite.name}\n\n`;
    report += `| Test | Status | Duration |\n|------|--------|----------|\n`;
    suite.tests.forEach((test) => {
      const statusIcon = test.status === 'passed' ? '✅' : test.status === 'failed' ? '❌' : '⏭️';
      report += `| ${test.name} | ${statusIcon} ${test.status} | ${test.duration}ms |\n`;
      if (test.error) {
        report += `\n\`\`\`\n${test.error}\n\`\`\`\n`;
      }
    });
    report += '\n';
  });

  return report;
}

export function generateConsoleReport(data: TestReportData): string {
  const passRate = ((data.passed / data.totalTests) * 100).toFixed(1);

  let report = '\n';
  report += '═══════════════════════════════════════\n';
  report += '           TEST REPORT                 \n';
  report += '═══════════════════════════════════════\n\n';
  report += `Total:   ${data.totalTests}\n`;
  report += `Passed:  ${data.passed} (${passRate}%)\n`;
  report += `Failed:  ${data.failed}\n`;
  report += `Skipped: ${data.skipped}\n`;
  report += `Duration: ${data.duration}ms\n\n`;

  data.suites.forEach((suite) => {
    report += `┌─ ${suite.name}\n`;
    suite.tests.forEach((test) => {
      const icon = test.status === 'passed' ? '✓' : test.status === 'failed' ? '✗' : '○';
      report += `│  ${icon} ${test.name} (${test.duration}ms)\n`;
      if (test.error) {
        report += `│    Error: ${test.error}\n`;
      }
    });
    report += '└─────────────────────────────────────\n\n';
  });

  return report;
}

export async function saveReport(
  data: TestReportData,
  format: 'json' | 'html' | 'markdown' | 'console',
  filename?: string,
): Promise<void> {
  if (typeof window !== 'undefined') {
    console.log('Report generation only available in Node.js environment');
    return;
  }

  const fs = await import('fs');
  const path = await import('path');

  const reportsDir = path.join(process.cwd(), 'test-reports');
  if (!fs.existsSync(reportsDir)) {
    fs.mkdirSync(reportsDir, { recursive: true });
  }

  const timestamp = new Date(data.timestamp).toISOString().replace(/[:.]/g, '-');
  const baseName = filename || `report-${timestamp}`;

  let content: string;
  let extension: string;

  switch (format) {
    case 'json':
      content = generateJsonReport(data);
      extension = 'json';
      break;
    case 'html':
      content = generateHtmlReport(data);
      extension = 'html';
      break;
    case 'markdown':
      content = generateMarkdownReport(data);
      extension = 'md';
      break;
    case 'console':
      content = generateConsoleReport(data);
      extension = 'txt';
      break;
  }

  const filePath = path.join(reportsDir, `${baseName}.${extension}`);
  fs.writeFileSync(filePath, content);
  console.log(`Report saved to: ${filePath}`);
}
