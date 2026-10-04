"use client";

import { FileText, Upload } from "lucide-react";
import { useRef, useState, type DragEvent, type KeyboardEvent } from "react";

import { cn } from "@/lib/utils/class-names";

interface FileDropzoneProps {
  accept: string;
  maxSize: number;
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function acceptsFile(file: File, accept: string): boolean {
  const rules = accept.split(",").map((rule) => rule.trim().toLowerCase());
  const extension = `.${file.name.split(".").pop()?.toLowerCase() ?? ""}`;
  const mimeType = file.type.toLowerCase();

  return rules.some((rule) => {
    if (rule.startsWith(".")) {
      return rule === extension;
    }
    if (rule.endsWith("/*")) {
      return mimeType.startsWith(rule.slice(0, -1));
    }
    return rule === mimeType;
  });
}

/** Keyboard-accessible file selector with drag-and-drop feedback. */
export function FileDropzone({
  accept,
  maxSize,
  onFileSelect,
  disabled = false,
}: FileDropzoneProps): React.JSX.Element {
  const inputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  function selectFile(file: File): void {
    if (!acceptsFile(file, accept)) {
      setError("Choose a supported file type.");
      return;
    }
    if (file.size > maxSize) {
      setError(`File must be ${formatFileSize(maxSize)} or smaller.`);
      return;
    }

    setError(null);
    setSelectedFile(file);
    onFileSelect(file);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>): void {
    event.preventDefault();
    setIsDragging(false);
    if (!disabled && event.dataTransfer.files[0]) {
      selectFile(event.dataTransfer.files[0]);
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>): void {
    if (!disabled && (event.key === "Enter" || event.key === " ")) {
      event.preventDefault();
      inputRef.current?.click();
    }
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled}
        aria-label="Choose or drop a file"
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={handleKeyDown}
        onDragEnter={(event) => {
          event.preventDefault();
          if (!disabled) setIsDragging(true);
        }}
        onDragOver={(event) => event.preventDefault()}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={cn(
          "rounded-card border-border bg-surface focus-visible:outline-ring flex min-h-48 cursor-pointer flex-col items-center justify-center border-2 border-dashed p-6 text-center transition-colors focus-visible:outline-2 focus-visible:outline-offset-2",
          isDragging && "border-primary bg-primary-soft",
          disabled && "cursor-not-allowed opacity-50",
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          disabled={disabled}
          className="sr-only"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) selectFile(file);
          }}
        />
        {selectedFile ? (
          <>
            <FileText
              aria-hidden="true"
              className="text-primary size-7"
              strokeWidth={1.75}
            />
            <p className="mt-3 font-medium">{selectedFile.name}</p>
            <p className="text-muted-foreground mt-1 text-xs">
              {formatFileSize(selectedFile.size)}
            </p>
          </>
        ) : (
          <>
            <Upload
              aria-hidden="true"
              className="text-primary size-7"
              strokeWidth={1.75}
            />
            <p className="mt-3 font-medium">
              Drop a file here or choose a file
            </p>
            <p className="text-muted-foreground mt-1 text-xs">
              Accepted: {accept}. Maximum {formatFileSize(maxSize)}.
            </p>
          </>
        )}
      </div>
      {error ? (
        <p className="text-danger mt-2 text-sm" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
