import type React from "react";

interface TableProps {
  title?: string;
  columns: string[];
  rows: React.ReactNode[][];
  onExport?: () => void;
}

export function Table({ title, columns, rows, onExport }: TableProps) {
  return (
    <div className="overflow-hidden rounded-xl bg-white shadow-sm">
      {(title || onExport) && (
        <div className="flex items-center justify-between border-b border-neutral-200 bg-neutral-50 px-4 py-2">
          {title && (
            <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-700">
              {title}
            </h2>
          )}
          {onExport && (
            <button
              type="button"
              onClick={onExport}
              className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-blue-900 text-white shadow-sm hover:bg-blue-800"
              aria-label="Export table"
            >
              <svg viewBox="0 0 20 20" className="h-4 w-4" aria-hidden="true">
                <path
                  d="M10 2a.75.75 0 01.75.75v7.19l2.22-2.22a.75.75 0 111.06 1.06l-3.5 3.5a.75.75 0 01-1.06 0l-3.5-3.5a.75.75 0 111.06-1.06l2.22 2.22V2.75A.75.75 0 0110 2z"
                  className="fill-current"
                />
                <path
                  d="M4 12.75a.75.75 0 011.5 0v1.5h9v-1.5a.75.75 0 011.5 0v2.25A1.25 1.25 0 0114.75 16H5.25A1.25 1.25 0 014 15.25z"
                  className="fill-current"
                />
              </svg>
            </button>
          )}
        </div>
      )}
      <table className="min-w-full divide-y divide-neutral-200">
        <thead className="bg-neutral-50">
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                scope="col"
                className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-neutral-200 bg-white text-sm">
          {rows.map((row, idx) => (
            <tr key={idx}>
              {row.map((cell, cIdx) => (
                <td key={cIdx} className="px-4 py-2 text-gray-800">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
