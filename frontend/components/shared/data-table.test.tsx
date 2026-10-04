import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DataTable } from "@/components/shared/data-table";
import { createDataTableColumnHelper } from "@/components/shared/data-table-types";

interface TestRow {
  id: string;
  name: string;
}

const columnHelper = createDataTableColumnHelper<TestRow>();
const columns = columnHelper.columns([
  columnHelper.accessor("name", {
    header: "Name",
    cell: ({ getValue }) => getValue(),
  }),
]);

describe("DataTable", () => {
  it("renders server data and pagination context", () => {
    render(
      <DataTable
        columns={columns}
        data={{
          items: [{ id: "1", name: "Ayesha Khan" }],
          total: 21,
          page: 2,
          page_size: 20,
        }}
        onPageChange={vi.fn()}
      />,
    );

    expect(screen.getByText("Ayesha Khan")).toBeInTheDocument();
    expect(screen.getByText("21–21 of 21")).toBeInTheDocument();
    expect(screen.getByText("Page 2 of 2")).toBeInTheDocument();
  });

  it("uses the shared empty state", () => {
    render(
      <DataTable
        columns={columns}
        data={{ items: [], total: 0, page: 1, page_size: 20 }}
        onPageChange={vi.fn()}
      />,
    );

    expect(screen.getByRole("heading", { name: "No results" })).toBeVisible();
  });
});
