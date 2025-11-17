import type React from "react";

interface ExportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (format: "pdf" | "csv" | "bundle") => void;
}

export function ExportDialog({ isOpen, onClose, onConfirm }: ExportDialogProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-sm rounded-xl bg-white p-4 shadow-lg">
        <h2 className="mb-2 text-sm font-semibold text-gray-900">Export as</h2>
        <p className="mb-3 text-xs text-gray-600">
          Choose the format for this export. PDF includes full page context (header,
          charts, tables, and AI Analysis &amp; Insights where available). CSV includes
          only structured table/chart data without descriptions or insights. Bundle
          produces a ZIP containing both.
        </p>
        <div className="flex flex-col gap-2 text-xs font-medium">
          <button
            type="button"
            onClick={() => {
              onConfirm("pdf");
              onClose();
            }}
            className="w-full rounded-full bg-blue-900 px-3 py-2 text-white hover:bg-blue-800"
          >
            PDF
          </button>
          <button
            type="button"
            onClick={() => {
              onConfirm("csv");
              onClose();
            }}
            className="w-full rounded-full border border-neutral-300 px-3 py-2 text-gray-800 hover:bg-neutral-100"
          >
            CSV
          </button>
          <button
            type="button"
            onClick={() => {
              onConfirm("bundle");
              onClose();
            }}
            className="w-full rounded-full border border-neutral-300 px-3 py-2 text-gray-800 hover:bg-neutral-100"
          >
            Bundle (PDF + CSV)
          </button>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="mt-3 w-full rounded-full px-3 py-2 text-[11px] font-medium text-gray-600 hover:bg-neutral-100"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
