interface DataTableSkeletonProps {
  columnCount: number;
  rowCount: number;
}

/** Loading rows that preserve the table's column structure. */
export function DataTableSkeleton({
  columnCount,
  rowCount,
}: DataTableSkeletonProps): React.JSX.Element {
  return (
    <>
      {Array.from({ length: Math.min(rowCount, 8) }, (_, rowIndex) => (
        <tr key={rowIndex}>
          {Array.from({ length: columnCount }, (_, columnIndex) => (
            <td key={columnIndex} className="border-border border-b px-4 py-4">
              <div className="bg-surface-muted h-4 w-24 animate-pulse rounded" />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}
