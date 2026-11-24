import type { ReactNode } from "react";

export interface DataTableColumn<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
}

interface DataTableProps<T> {
  rows: T[];
  columns: DataTableColumn<T>[];
  getRowKey: (row: T) => string;
  emptyState?: ReactNode;
}

export function DataTable<T>({ rows, columns, getRowKey, emptyState = "데이터가 없습니다." }: DataTableProps<T>) {
  if (rows.length === 0) return <div className="table-empty">{emptyState}</div>;

  return (
    <div className="table-scroll" tabIndex={0} role="region" aria-label="데이터 표">
      <table className="data-table">
        <thead><tr>{columns.map((column) => <th key={column.key} scope="col">{column.header}</th>)}</tr></thead>
        <tbody>{rows.map((row) => <tr key={getRowKey(row)}>{columns.map((column) => <td key={column.key}>{column.render(row)}</td>)}</tr>)}</tbody>
      </table>
    </div>
  );
}
