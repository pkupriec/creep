import { expect, test, type Locator, type Page } from '@playwright/test';
import path from 'node:path';

async function exportGraph(page: Page) {
  await page.getByRole('button', { name: 'Export JSON' }).click();
  return JSON.parse(await page.getByRole('textbox', { name: 'Graph JSON' }).inputValue());
}
async function connect(page: Page, source: Locator, target: Locator) {
  const a = await source.boundingBox(); const b = await target.boundingBox();
  if (!a || !b) throw new Error('Connection handles must be visible');
  await page.mouse.move(a.x + a.width / 2, a.y + a.height / 2);
  await page.mouse.down(); await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2, { steps: 15 }); await page.mouse.up();
}

test('React Flow renders loop, edits prompt/seed/exit and round-trips all data', async ({ page }) => {
  const errors: string[] = []; page.on('pageerror', e => errors.push(e.message));
  await page.goto('/');
  await expect(page.getByTestId('node-d')).toBeVisible();
  await expect(page.getByTestId('node-c')).toContainText('CONTROLLER');
  await expect(page.getByTestId('target-d-previous')).toBeVisible();
  await expect(page.locator('.react-flow__edge-feedback')).toHaveCount(1);
  await expect(page.getByRole('checkbox', { name: 'Member d', exact: true })).toBeChecked();
  await page.getByRole('textbox', { name: 'System prompt' }).fill('Draft from every named input.');
  await page.getByRole('textbox', { name: 'Feedback seed' }).fill('null');
  await page.getByRole('textbox', { name: 'Exit decision' }).fill('done');
  const exported = await exportGraph(page);
  expect(exported.nodes.find((n: { id: string }) => n.id === 'd').system_prompt).toBe('Draft from every named input.');
  expect(exported.edges.find((e: { kind: string }) => e.kind === 'feedback').initial_value).toBeNull();
  expect(exported.loops[0].exit_value).toBe('done');
  await page.getByRole('button', { name: 'Diamond', exact: true }).click();
  await expect(page.getByTestId('node-d')).toHaveCount(0);
  await page.getByRole('button', { name: 'Import JSON' }).click();
  expect(await exportGraph(page)).toEqual(exported);
  expect(errors).toEqual([]);
});

test('React Flow draws named fan-out, retains dragged position and deletes an edge', async ({ page }) => {
  await page.goto('/'); await page.getByRole('button', { name: 'Diamond', exact: true }).click();
  await expect(page.getByTestId('target-s-correctness')).toBeVisible();
  await expect(page.getByTestId('target-s-alternatives')).toBeVisible();
  await page.getByRole('textbox', { name: 'New port name' }).fill('peer');
  await connect(page, page.getByTestId('source-a'), page.getByTestId('target-b-extra'));
  await expect(page.getByTestId('target-b-peer')).toBeVisible();
  await expect(page.locator('.react-flow__edge[data-id="edge-a-b-peer"]')).toBeVisible();
  const before = await exportGraph(page);
  expect(before.edges.filter((e: { source: string }) => e.source === 'a')).toHaveLength(2);
  const title = page.getByTestId('node-a').getByText('a', { exact: true });
  const box = await title.boundingBox(); if (!box) throw new Error('Node title absent');
  await page.mouse.move(box.x + 20, box.y + 10); await page.mouse.down(); await page.mouse.move(box.x + 70, box.y + 30, { steps: 10 }); await page.mouse.up();
  const after = await exportGraph(page);
  expect(after.nodes.find((n: { id: string }) => n.id === 'a').position).not.toEqual(before.nodes.find((n: { id: string }) => n.id === 'a').position);
  await page.locator('.react-flow__edge[data-id="edge-a-b-peer"] .react-flow__edge-interaction').click({ force: true });
  await page.keyboard.press('Delete');
  expect((await exportGraph(page)).edges.some((e: { id: string }) => e.id === 'edge-a-b-peer')).toBe(false);
});

test('drawing feedback requires explicit scope/controller/seed/decisions before commit', async ({ page }) => {
  await page.goto('/');
  // Remove existing feedback through the graph import surface, retaining loop nodes and forward paths.
  const graph = await exportGraph(page); graph.edges = graph.edges.filter((e: { kind: string }) => e.kind !== 'feedback'); graph.loops = [];
  await page.getByRole('textbox', { name: 'Graph JSON' }).fill(JSON.stringify(graph));
  await page.getByRole('button', { name: 'Import JSON' }).click();
  await page.getByRole('combobox', { name: 'Connection type' }).selectOption('feedback');
  await page.getByRole('textbox', { name: 'New port name' }).fill('previous');
  await connect(page, page.getByTestId('source-c'), page.getByTestId('target-d-extra'));
  await expect(page.getByRole('button', { name: 'Commit feedback' })).toBeVisible();
  expect((await exportGraph(page)).edges.some((e: { kind: string }) => e.kind === 'feedback')).toBe(false);
  await page.getByRole('textbox', { name: 'Feedback seed' }).fill('"Initial critique"');
  await page.getByRole('button', { name: 'Commit feedback' }).click();
  const result = await exportGraph(page);
  await expect(page.locator('.react-flow__edge-feedback')).toBeVisible();
  expect(result.loops[0]).toMatchObject({ node_ids: ['d', 'c'], controller_node_id: 'c', continue_value: 'continue', exit_value: 'stop' });
  expect(result.edges.find((e: { kind: string }) => e.kind === 'feedback').initial_value).toBe('Initial critique');
});

test('Rete renders the same named-port graph with a styled feedback cycle and prompt controls', async ({ page }) => {
  const errors: string[] = []; page.on('pageerror', e => errors.push(e.message));
  await page.goto('/'); const initial = await exportGraph(page);
  await page.getByRole('button', { name: 'Rete.js', exact: true }).click();
  await expect(page.getByTestId('rete-canvas')).toHaveAttribute('data-ready', 'true');
  await expect(page.locator('[data-testid^="rete-node-"]')).toHaveCount(initial.nodes.length);
  await expect(page.locator('[data-testid^="rete-edge-"]')).toHaveCount(initial.edges.length);
  await expect(page.getByTestId('rete-edge-cd')).toHaveAttribute('data-kind', 'feedback');
  await expect(page.getByTestId('rete-edge-cd').locator('path')).toHaveAttribute('d', /M/);
  await expect(page.getByTestId('rete-node-s')).toContainText('correctness');
  await expect(page.getByTestId('rete-node-s')).toContainText('alternatives');
  await page.getByTestId('rete-node-d').locator('input').fill('Native Rete prompt edit');
  await expect(page.getByTestId('rete-canvas')).toHaveAttribute('data-ready', 'true');
  expect((await exportGraph(page)).nodes.find((n: { id: string }) => n.id === 'd').system_prompt).toBe('Native Rete prompt edit');
  await page.getByRole('textbox', { name: 'System prompt' }).fill('Rete uses the same canonical prompt.');
  await expect(page.getByTestId('rete-canvas')).toHaveAttribute('data-ready', 'true');
  const changed = await exportGraph(page);
  expect(changed.nodes.find((n: { id: string }) => n.id === 'd').system_prompt).toBe('Rete uses the same canonical prompt.');
  expect(changed.edges).toEqual(initial.edges); expect(changed.loops).toEqual(initial.loops);
  await page.getByRole('button', { name: 'Diamond', exact: true }).click();
  await page.getByRole('button', { name: 'Import JSON' }).click();
  expect(await exportGraph(page)).toEqual(changed);
  expect(errors).toEqual([]);
});

test('capture reproducible research screenshot', async ({ page }) => {
  await page.goto('/'); await expect(page.getByTestId('node-c')).toBeVisible();
  await expect(page.locator('.react-flow__edge')).toHaveCount(10);
  await page.screenshot({ path: path.resolve('../../docs/research/graph-editor.png'), fullPage: true });
});

test('Rete draws a named connection and exports moved node coordinates', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Diamond', exact: true }).click();
  await page.getByRole('button', { name: 'Rete.js', exact: true }).click();
  await expect(page.getByTestId('rete-canvas')).toHaveAttribute('data-ready', 'true');
  await page.getByRole('textbox', { name: 'New port name' }).fill('peer');
  await connect(page, page.getByTestId('rete-node-a').getByTestId('output-payload').getByTestId('output-socket'), page.getByTestId('rete-node-b').getByTestId('input-extra').getByTestId('input-socket'));
  await expect(page.getByTestId('rete-node-b').getByTestId('input-peer')).toBeVisible();
  const before = await exportGraph(page);
  expect(before.edges.at(-1)).toMatchObject({ source: 'a', target: 'b', target_port: 'peer', kind: 'forward' });
  const title = page.getByTestId('rete-node-a').getByTestId('title');
  const box = await title.boundingBox(); if (!box) throw new Error('Rete title must be visible');
  await page.mouse.move(box.x + 20, box.y + 10); await page.mouse.down(); await page.mouse.move(box.x + 70, box.y + 40, { steps: 10 }); await page.mouse.up();
  await expect(page.getByTestId('rete-canvas')).toHaveAttribute('data-ready', 'true');
  const after = await exportGraph(page);
  expect(after.nodes.find((n: { id: string }) => n.id === 'a').position).not.toEqual(before.nodes.find((n: { id: string }) => n.id === 'a').position);
});
