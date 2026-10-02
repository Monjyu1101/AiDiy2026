const assert = require('node:assert/strict');
const vscode = require('vscode');
const { writeFileSync } = require('node:fs');
exports.run = async () => {
  const extension = vscode.extensions.getExtension('aidiy.aidiy-hermes');
  assert.ok(extension, '拡張機能が登録されている');
  await extension.activate();
  assert.ok(extension.isActive);
  const commands = await vscode.commands.getCommands(true);
  for (const command of ['open', 'newChat', 'attachSelection', 'settings', 'terminal']) {
    assert.ok(commands.includes(`aidiyHermes.${command}`), command);
  }
  await vscode.commands.executeCommand('aidiyHermes.open');
  await vscode.commands.executeCommand('aidiyHermes.newChat');
  await new Promise(resolve => setTimeout(resolve, 1500));
  if (process.env.AIDIY_TEST_RESULT) writeFileSync(process.env.AIDIY_TEST_RESULT, 'extension host: passed\n');
};
