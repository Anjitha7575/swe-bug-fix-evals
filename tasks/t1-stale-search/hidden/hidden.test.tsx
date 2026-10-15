import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import { vi, it, expect } from "vitest";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));
vi.mock("@/lib/analytics-init", () => ({
  trackUserInteraction: vi.fn(),
  startPropertyDiscovery: vi.fn(),
  trackPropertyDiscoveryStep: vi.fn(),
}));
vi.mock("@/lib/savedPropertiesApi", () => ({
  fetchSavedListingIds: vi.fn().mockResolvedValue([]),
  setListingSaved: vi.fn(),
}));
vi.mock("@/components/virtualized-property-list", () => ({
  VirtualizedPropertyList: ({ properties }: any) => (
    <ul>{properties.map((p: any) => <li key={p.id}>{p.title}</li>)}</ul>
  ),
}));
const calls: Array<{ q?: string; resolve: (v: any) => void }> = [];
vi.mock("@/lib/propertiesApi", () => ({
  searchProperties: vi.fn((f: any) => new Promise((resolve) => calls.push({ q: f.query, resolve }))),
}));

import PropertiesClient from "./PropertiesClient";

const res = (title: string) => ({ data: [{ id: title, title }], total: 1, totalPages: 1 });

it("keeps results of the latest query when an older response arrives last", async () => {
  render(<PropertiesClient />);
  await waitFor(() => expect(calls.length).toBe(1)); // initial (empty query)
  const input = screen.getByPlaceholderText("Search by location or property name...");
  fireEvent.change(input, { target: { value: "aold" } });
  await waitFor(() => expect(calls.length).toBe(2), { timeout: 2000 });
  fireEvent.change(input, { target: { value: "bnew" } });
  await waitFor(() => expect(calls.length).toBe(3), { timeout: 2000 });
  await act(async () => { calls[2].resolve(res("BNEW")); });
  await act(async () => { calls[1].resolve(res("AOLD")); calls[0].resolve(res("ALL")); });
  expect(screen.queryByText("BNEW")).not.toBeNull();
  expect(screen.queryByText("AOLD")).toBeNull();
});
