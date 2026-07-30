"use client";

import { Camera, FileAudio, FileSpreadsheet, FileText, Loader2, UploadCloud } from "lucide-react";
import { motion } from "framer-motion";
import { useDropzone } from "react-dropzone";
import { useState } from "react";
import { documentKind, uploadDocument, type UploadResult } from "@/lib/api";

const accepted = {
  "image/*": [".jpg", ".jpeg", ".png"],
  "application/pdf": [".pdf"],
  "text/csv": [".csv"],
  "audio/*": [".m4a", ".webm", ".wav"],
};

const KIND_LABEL: Record<string, string> = {
  upi_csv: "UPI CSV",
  khaata_photo: "Khaata photo",
  invoice_image: "Invoice",
  voice_note: "Voice note",
  manual: "Document",
};

type Processed = { name: string; kind: string; result?: UploadResult; error?: string; busy: boolean };

export function UploadZone({ storeId }: { storeId: string }) {
  const [items, setItems] = useState<Processed[]>([]);

  async function process(files: File[]) {
    // Seed the list first so each file shows a processing state immediately.
    setItems((current) => [
      ...files.map((file) => ({ name: file.name, kind: documentKind(file), busy: true })),
      ...current,
    ]);

    for (const file of files) {
      const kind = documentKind(file);
      try {
        const result = await uploadDocument(storeId, file, kind);
        setItems((current) =>
          current.map((item) => (item.name === file.name && item.busy ? { ...item, busy: false, result } : item)),
        );
      } catch (cause) {
        setItems((current) =>
          current.map((item) =>
            item.name === file.name && item.busy
              ? { ...item, busy: false, error: cause instanceof Error ? cause.message : "Upload failed." }
              : item,
          ),
        );
      }
    }
  }

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    accept: accepted,
    noClick: true,
    maxSize: 10 * 1024 * 1024,
    onDropAccepted: (files) => void process(files),
    onDropRejected: (rejected) => {
      const failed = rejected[0]?.file;
      setItems((current) => [
        {
          name: failed?.name ?? "file",
          kind: "manual",
          busy: false,
          error: failed
            ? `${failed.name} is ${(failed.size / 1_048_576).toFixed(1)} MB or an unsupported type — the limit is 10 MB.`
            : "That file type is not supported.",
        },
        ...current,
      ]);
    },
  });

  return (
    <section>
      <motion.div
        className={`upload-zone ${isDragActive ? "upload-active" : ""}`}
        animate={{ scale: isDragActive ? 1.01 : 1 }}
        transition={{ duration: 0.2 }}
      >
        <div {...getRootProps({ className: "upload-zone-inner" })}>
          <input {...getInputProps()} />
          <div className="upload-icon">
            <UploadCloud aria-hidden="true" />
          </div>
          <h2>Bring your records together</h2>
          <p>Upload your own khaata photo, invoice, UPI CSV, or Hindi voice note — it is read live.</p>
          <p className="upload-helper">Accepted: JPG, PNG, PDF, CSV, M4A, WAV, and WebM · up to 10 MB.</p>
          <button type="button" className="button button-primary" onClick={open}>
            Choose files
          </button>
        </div>
      </motion.div>

      {items.length > 0 && (
        <div className="uploaded-files">
          {items.map((item, index) => (
            <article className="uploaded-file upload-result" key={`${item.name}-${index}`}>
              <header>
                <Icon name={item.name} />
                <div>
                  <strong>{item.name}</strong>
                  <span>
                    {item.busy
                      ? "Reading the document…"
                      : item.error
                        ? "Could not be read"
                        : `${item.result?.entry_count ?? 0} entr${item.result?.entry_count === 1 ? "y" : "ies"} extracted`}
                  </span>
                </div>
                <span className={`kind-badge kind-${item.kind}`}>{KIND_LABEL[item.kind] ?? item.kind}</span>
              </header>

              {item.busy && (
                <p className="inline-message" role="status">
                  <Loader2 className="spin" aria-hidden="true" /> Extracting…
                </p>
              )}

              {item.error && (
                <p className="inline-message message-error" role="alert">
                  {item.error}
                </p>
              )}

              {item.result && item.result.entries.length > 0 && (
                <div className="extract-scroll">
                  <table className="ledger-table">
                    <thead>
                      <tr>
                        <th>Type</th>
                        <th>Party</th>
                        <th>Amount</th>
                        <th>Where</th>
                        <th>Model</th>
                      </tr>
                    </thead>
                    <tbody>
                      {item.result.entries.map((entry, row) => (
                        <tr key={row}>
                          <td>{entry.entry_type}</td>
                          <td>{entry.party_name ?? "—"}</td>
                          <td>{entry.amount ?? "—"}</td>
                          <td>{entry.ref ?? "—"}</td>
                          <td>
                            <span className="model-badge">{entry.extraction_model}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function Icon({ name }: { name: string }) {
  const Glyph = name.endsWith(".csv")
    ? FileSpreadsheet
    : /m4a|webm|wav|mp3/.test(name)
      ? FileAudio
      : name.endsWith(".pdf")
        ? FileText
        : Camera;
  return <Glyph aria-hidden="true" />;
}
