import {
  createColumnHelper,
  rowPaginationFeature,
  rowSortingFeature,
  tableFeatures,
  type CellData,
  type ColumnDef,
  type RowData,
  type SortingState,
} from "@tanstack/react-table";

export const dataTableFeatures = tableFeatures({
  rowPaginationFeature,
  rowSortingFeature,
});

export type DataTableColumn<TData extends RowData> = ColumnDef<
  typeof dataTableFeatures,
  TData,
  CellData
>;

export interface PaginatedData<TData extends RowData> {
  items: TData[];
  total: number;
  page: number;
  page_size: number;
}

export { type SortingState };

/** Create columns bound to the shared data-table feature set. */
export function createDataTableColumnHelper<TData extends RowData>() {
  return createColumnHelper<typeof dataTableFeatures, TData>();
}
