import React from 'react';

export interface Column<T> {
  header: string;
  accessor?: keyof T;
  render?: (row: T) => React.ReactNode;
  className?: string;
}

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyField: keyof T;
  emptyMessage?: string;
  onRowClick?: (row: T) => void;
}

export function Table<T>({
  columns,
  data,
  keyField,
  emptyMessage = 'No records found matching criteria.',
  onRowClick,
}: TableProps<T>) {
  if (data.length === 0) {
    return (
      <div className="p-12 text-center border border-dashed border-slate-800 rounded-xl bg-slate-900/30">
        <p className="text-sm text-slate-400 font-mono">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto border border-slate-800 rounded-xl shadow-lg bg-slate-900/60">
      <table className="w-full text-left text-xs border-collapse">
        <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-mono uppercase text-[10px] tracking-wider">
          <tr>
            {columns.map((col, idx) => (
              <th key={idx} className={`py-3.5 px-4 font-bold ${col.className || ''}`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60">
          {data.map((row) => {
            const rowKey = String(row[keyField]);
            return (
              <tr
                key={rowKey}
                onClick={() => onRowClick && onRowClick(row)}
                className={`hover:bg-slate-800/40 transition-colors ${
                  onRowClick ? 'cursor-pointer' : ''
                }`}
              >
                {columns.map((col, idx) => (
                  <td key={idx} className={`py-3.5 px-4 text-slate-200 ${col.className || ''}`}>
                    {col.render
                      ? col.render(row)
                      : col.accessor
                      ? String(row[col.accessor] ?? '')
                      : null}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
