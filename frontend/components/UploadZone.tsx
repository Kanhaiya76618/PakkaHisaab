"use client";

import { Camera, FileAudio, FileSpreadsheet, FileText, UploadCloud } from "lucide-react";
import { motion } from "framer-motion";
import { useDropzone } from "react-dropzone";
import { useState } from "react";

const accepted = { "image/*": [".jpg", ".jpeg", ".png"], "application/pdf": [".pdf"], "text/csv": [".csv"], "audio/*": [".m4a", ".webm"] };

export function UploadZone() {
  const [message, setMessage] = useState<string | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({ accept: accepted, noClick: true, maxSize: 10 * 1024 * 1024, onDropAccepted: (next) => { setFiles(next); setMessage(`${next.length} document${next.length > 1 ? "s" : ""} ready for processing.`); }, onDropRejected: (rejected) => { const failed = rejected[0]?.file; setMessage(failed ? `${failed.name} is too large or unsupported — the limit is 10 MB.` : "That file type is not supported."); } });
  return <section><motion.div className={`upload-zone ${isDragActive ? "upload-active" : ""}`} animate={{ scale: isDragActive ? 1.01 : 1 }} transition={{ duration: 0.2 }}><div {...getRootProps({ className: "upload-zone-inner" })}><input {...getInputProps()} /><div className="upload-icon"><UploadCloud aria-hidden="true" /></div><h2>Bring your records together</h2><p>Photos, PDFs, CSVs, UPI screenshots, or Hindi voice notes.</p><p className="upload-helper">Accepted: JPG, PNG, PDF, CSV, M4A, and WebM · up to 10 MB.</p><button type="button" className="button button-primary" onClick={open}>Choose files</button></div></motion.div>{message && <p className={`inline-message ${files.length ? "message-success" : "message-error"}`} role="status">{message}</p>}{files.length > 0 && <div className="uploaded-files">{files.map((file) => <UploadedFile key={file.name} name={file.name} />)}</div>}</section>;
}

function UploadedFile({ name }: { name: string }) {
  const Icon = name.endsWith(".csv") ? FileSpreadsheet : name.match(/m4a|webm/) ? FileAudio : name.endsWith(".pdf") ? FileText : Camera;
  return <article className="uploaded-file"><Icon aria-hidden="true" /><div><strong>{name}</strong><span>Ready to process · source preserved</span></div><span className="kind-badge kind-csv">Document</span></article>;
}
