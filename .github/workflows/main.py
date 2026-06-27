import { useState, useRef, useCallback } from "react";
import * as XLSX from "xlsx";
import {
  ScanLine, Upload, Download, Keyboard, X,
  BarChart3, FileSpreadsheet, Trash2, ChevronRight,
  CheckCircle2, Search, RotateCcw } from
"lucide-react";
import UploadExcel from "@/components/UploadExcel";
import QRScanner from "@/components/QRScanner";
import ResultTable from "@/components/ResultTable";

const TABS = ["Upload", "Scan", "Hasil"];

export default function Home() {
  const [activeTab, setActiveTab] = useState("Upload");
  const [excelData, setExcelData] = useState([]);
  const [excelFileName, setExcelFileName] = useState("");
  const [excelHeaderStyles, setExcelHeaderStyles] = useState({});
  const [columns, setColumns] = useState([]);
  const [matchKey, setMatchKey] = useState("");
  const [results, setResults] = useState([]);
  const [scannerOpen, setScannerOpen] = useState(false);
  const [manualCode, setManualCode] = useState("");
  const [lastScan, setLastScan] = useState(null);
  const [lastScanStatus, setLastScanStatus] = useState(null); // 'found' | 'notfound'
  const lastScanRef = useRef(null);
  const manualRef = useRef(null);

  // ── Sound effects ─────────────────────────────────────────────
  const playBeep = () => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.type = "sine";
      osc.frequency.setValueAtTime(1200, ctx.currentTime);
      gain.gain.setValueAtTime(0.5, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.15);
    } catch (_) {}
  };

  const playSalah = () => {
    try {
      const utter = new SpeechSynthesisUtterance("SALAH");
      utter.lang = "id-ID";
      utter.rate = 1;
      utter.pitch = 0.8;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utter);
    } catch (_) {}
  };

  // ── Excel loaded ──────────────────────────────────────────────
  const handleDataLoaded = (data, fname, headerStyles = {}) => {
    setExcelData(data);
    setExcelFileName(fname);
    setExcelHeaderStyles(headerStyles);
    const cols = data.length ? Object.keys(data[0]) : [];
    setColumns(cols);
    setMatchKey(cols[0] || "");
    setResults([]);
    setActiveTab("Scan");
  };

  // ── Core scan logic ───────────────────────────────────────────
  const processCode = useCallback(
    (code, method = "scan") => {
      if (!code.trim()) return;
      const trimmed = code.trim();

      // prevent duplicates within 1.5 s
      if (lastScanRef.current === trimmed) return;
      lastScanRef.current = trimmed;
      setTimeout(() => {lastScanRef.current = null;}, 1500);

      // check if already scanned before
      const alreadyScanned = results.some((r) => r.matched && r.barcode_value === trimmed);
      if (alreadyScanned) {
        setLastScan(trimmed);
        setLastScanStatus("duplicate");
        setManualCode("");
        try {
          const utter = new SpeechSynthesisUtterance("Sudah pernah scan");
          utter.lang = "id-ID";
          window.speechSynthesis.cancel();
          window.speechSynthesis.speak(utter);
        } catch (_) {}
        return;
      }

      const matched = excelData.find(
        (row) => String(row[matchKey] ?? "").trim() === trimmed
      );

      const newItem = {
        id: Date.now() + Math.random(),
        barcode_value: trimmed,
        row_data: matched || {},
        matched: !!matched,
        input_method: method
      };

      setResults((prev) => [...prev, newItem]);
      setLastScan(trimmed);
      setLastScanStatus(matched ? "found" : "notfound");
      setManualCode("");
      if (matched) playBeep();else playSalah();

      // auto-switch to result tab if scanning
      if (method === "scan") setActiveTab("Hasil");
    },
    [excelData, matchKey, results]
  );

  const handleManualSubmit = (e) => {
    e.preventDefault();
    processCode(manualCode, "manual");
  };

  const handleRemove = (idx) => {
    setResults((prev) => prev.filter((_, i) => i !== idx));
  };

  const [showConfirmReset, setShowConfirmReset] = useState(false);

  const handleReset = () => {
    setResults([]);
    setLastScan(null);
    setLastScanStatus(null);
    setShowConfirmReset(false);
  };

  // ── Build sorted full list: scanned rows first (in scan order), then unscanned ──
  const sortedFullData = (() => {
    if (!excelData.length) return [];
    // deduplicate: keep only the first scan per barcode value
    const seenBarcodes = new Set();
    const uniqueScanned = results.filter((r) => {
      if (!r.matched || seenBarcodes.has(r.barcode_value)) return false;
      seenBarcodes.add(r.barcode_value);
      return true;
    });

    const scannedRows = uniqueScanned.
    map((r, idx) => ({ ...r.row_data, _scan_order: idx + 1, _scanned: true, _barcode: r.barcode_value }));

    // collect which keys were already scanned
    const scannedKeys = new Set(uniqueScanned.map((r) => r.barcode_value));

    // unscanned rows from excel (preserve original order)
    const unscannedRows = excelData.
    filter((row) => !scannedKeys.has(String(row[matchKey] ?? "").trim())).
    map((row) => ({ ...row, _scan_order: null, _scanned: false, _barcode: String(row[matchKey] ?? "") }));

    return [...scannedRows, ...unscannedRows];
  })();

  // ── Export ────────────────────────────────────────────────────
  const handleExport = () => {
    if (!sortedFullData.length) return;

    // Build rows with empty row inserted every 15 scanned items
    const rows = [];
    let scannedCount = 0;
    let rowNum = 1;

    for (const item of sortedFullData) {
      const { _scan_order, _scanned, _barcode, ...rest } = item;
      rows.push({ _scanned, row: { No: rowNum++, ...rest } });

      if (_scanned) {
        scannedCount++;
        if (scannedCount % 15 === 0) {
          rows.push({ _scanned: null, row: null }); // empty separator row
        }
      }
    }

    const exportData = rows.map((r) => r.row || {});
    const ws = XLSX.utils.json_to_sheet(exportData);

    const range = XLSX.utils.decode_range(ws["!ref"]);
    const redFont = { rgb: "FF0000" };

    for (let r = range.s.r; r <= range.e.r; r++) {
      for (let c = range.s.c; c <= range.e.c; c++) {
        const cellAddr = XLSX.utils.encode_cell({ r, c });
        if (!ws[cellAddr]) continue;

        if (r === 0) {
          const origKey = XLSX.utils.encode_cell({ r: 0, c });
          ws[cellAddr].s = excelHeaderStyles[origKey] || {};
        } else {
          const dataItem = rows[r - 1];
          if (dataItem && dataItem._scanned === false) {
            ws[cellAddr].s = { font: { color: redFont } };
          }
        }
      }
    }

    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Hasil Scan");
    const baseName = excelFileName.replace(/\.[^.]+$/, "") || "hasil_scan";
    XLSX.writeFile(wb, `${baseName}_sorted.xlsx`, { cellStyles: true });
  };

  // ── UI helpers ────────────────────────────────────────────────
  const tabCount = { Upload: null, Scan: excelData.length ? excelData.length : null, Hasil: sortedFullData.length || null };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="bg-primary text-primary-foreground sticky top-0 z-30 shadow-lg shadow-primary/20">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-secondary flex items-center justify-center">
              <ScanLine className="w-5 h-5 text-secondary-foreground" />
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight leading-tight">ADEK HARIANTO</h1>
              <p className="text-primary-foreground/60 text-[10px] font-medium tracking-widest uppercase">SCAN LAGA TO</p>
            </div>
          </div>
          {sortedFullData.length > 0 &&
          <button
            onClick={handleExport}
            className="flex items-center gap-1.5 bg-secondary text-secondary-foreground px-3 py-1.5 rounded-xl text-xs font-semibold hover:bg-secondary/90 transition-colors">
            
              <Download className="w-3.5 h-3.5" />
              Export .xlsx
            </button>
          }
        </div>

        {/* Tabs */}
        <div className="max-w-2xl mx-auto px-4 pb-0 flex">
          {TABS.map((tab) =>
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`relative flex items-center gap-1.5 px-4 py-3 text-sm font-semibold transition-all duration-200 no-underline
                ${activeTab === tab ?
            "text-secondary border-b-2 border-secondary" :
            "text-primary-foreground/50 hover:text-primary-foreground/80"}`
            }>
            
              {tab}
              {tabCount[tab] ?
            <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold
                  ${activeTab === tab ? "bg-secondary/20 text-secondary" : "bg-primary-foreground/10 text-primary-foreground/60"}`}>
                  {tabCount[tab]}
                </span> :
            null}
            </button>
          )}
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 max-w-2xl mx-auto w-full px-4 py-6 flex flex-col gap-5">

        {/* ── TAB: UPLOAD ── */}
        {activeTab === "Upload" &&
        <div className="flex flex-col gap-5">
            <div>
              <h2 className="text-lg font-bold text-foreground">Upload Data Excel</h2>
              <p className="text-muted-foreground text-sm mt-0.5">
                Upload file Excel berisi data yang ingin dicocokkan dengan QR code.
              </p>
            </div>
            <UploadExcel onDataLoaded={handleDataLoaded} />

            {excelData.length > 0 && columns.length > 0 &&
          <div className="bg-card rounded-2xl border border-border p-4 flex flex-col gap-3">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-primary" />
                  <span className="font-semibold text-sm">Pilih Kolom Kode</span>
                </div>
                <p className="text-xs text-muted-foreground -mt-1">
                  Pilih kolom yang nilainya akan dicocokkan dengan hasil scan QR code.
                </p>
                <select
              value={matchKey}
              onChange={(e) => setMatchKey(e.target.value)}
              className="w-full bg-muted border border-border rounded-xl px-3 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-ring">
              
                  {columns.map((col) =>
              <option key={col} value={col}>{col}</option>
              )}
                </select>

                <button
              onClick={() => setActiveTab("Scan")}
              className="w-full flex items-center justify-center gap-2 bg-primary text-primary-foreground py-3 rounded-xl font-semibold text-sm hover:bg-primary/90 transition-colors">
              
                  Mulai Scan <ChevronRight className="w-4 h-4" />
                </button>
              </div>
          }

            {/* Preview */}
            {excelData.length > 0 &&
          <div className="bg-card rounded-2xl border border-border overflow-hidden">
                <div className="px-4 py-3 border-b border-border flex items-center gap-2">
                  <FileSpreadsheet className="w-4 h-4 text-primary" />
                  <span className="text-sm font-semibold">Preview Data ({excelData.length} baris)</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-muted/60 border-b border-border">
                        {columns.map((col) =>
                    <th key={col} className="text-left px-3 py-2 font-semibold text-muted-foreground whitespace-nowrap">{col}</th>
                    )}
                      </tr>
                    </thead>
                    <tbody>
                      {excelData.slice(0, 5).map((row, i) =>
                  <tr key={i} className="border-b border-border/60 last:border-0">
                          {columns.map((col) =>
                    <td key={col} className="px-3 py-2 whitespace-nowrap">{String(row[col] ?? "")}</td>
                    )}
                        </tr>
                  )}
                    </tbody>
                  </table>
                  {excelData.length > 5 &&
              <p className="text-center text-xs text-muted-foreground py-2">
                      +{excelData.length - 5} baris lainnya…
                    </p>
              }
                </div>
              </div>
          }
          </div>
        }

        {/* ── TAB: SCAN ── */}
        {activeTab === "Scan" &&
        <div className="flex flex-col gap-5">
            {excelData.length === 0 &&
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3">
                <Upload className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-amber-800">Data belum diupload</p>
                  <p className="text-xs text-amber-600 mt-0.5">Upload file Excel terlebih dahulu sebelum scan.</p>
                  <button
                onClick={() => setActiveTab("Upload")}
                className="mt-2 text-xs font-semibold text-amber-700 underline">
                
                    Upload Sekarang →
                  </button>
                </div>
              </div>
          }

            {/* Last scan feedback */}
            {lastScan &&
          <div className={`rounded-2xl p-4 flex items-center gap-3 transition-all
                ${lastScanStatus === "found" ? "bg-green-50 border border-green-200" :
          lastScanStatus === "duplicate" ? "bg-blue-50 border border-blue-200" :
          "bg-amber-50 border border-amber-200"}`}>
                {lastScanStatus === "found" ?
            <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" /> :
            lastScanStatus === "duplicate" ?
            <RotateCcw className="w-5 h-5 text-blue-500 flex-shrink-0" /> :
            <Search className="w-5 h-5 text-amber-500 flex-shrink-0" />
            }
                <div>
                  <p className={`text-sm font-semibold ${lastScanStatus === "found" ? "text-green-800" : lastScanStatus === "duplicate" ? "text-blue-800" : "text-amber-800"}`}>
                    {lastScanStatus === "found" ? "Data ditemukan!" : lastScanStatus === "duplicate" ? "Sudah pernah di-scan!" : "Data tidak ditemukan"}
                  </p>
                  <p className="text-xs text-muted-foreground font-mono mt-0.5">{lastScan}</p>
                </div>
              </div>
          }

            {/* Scanner */}
            <div className="bg-card rounded-2xl border border-border overflow-hidden">
              <div className="px-4 py-3 border-b border-border flex items-center gap-2">
                <ScanLine className="w-4 h-4 text-primary" />
                <span className="text-sm font-semibold">Kamera Scanner</span>
              </div>
              <div className="p-4">
                {scannerOpen ?
              <QRScanner
                onScan={(code) => processCode(code, "scan")}
                onClose={() => setScannerOpen(false)} /> :


              <button
                onClick={() => setScannerOpen(true)}
                disabled={excelData.length === 0}
                className="w-full flex flex-col items-center justify-center gap-3 py-10 rounded-xl border-2 border-dashed border-primary/30 bg-accent/40 hover:bg-accent hover:border-primary/60 transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                
                    <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center">
                      <ScanLine className="w-8 h-8 text-primary" />
                    </div>
                    <div className="text-center">
                      <p className="font-semibold text-sm text-foreground">Buka Kamera</p>
                      <p className="text-xs text-muted-foreground mt-0.5">Arahkan ke QR code / barcode</p>
                    </div>
                  </button>
              }
              </div>
            </div>

            {/* Manual input */}
            <div className="bg-card rounded-2xl border border-border overflow-hidden">
              <div className="px-4 py-3 border-b border-border flex items-center gap-2">
                <Keyboard className="w-4 h-4 text-primary" />
                <span className="text-sm font-semibold">Input Manual</span>
              </div>
              <div className="p-4">
                <form onSubmit={handleManualSubmit} className="flex gap-2">
                  <input
                  ref={manualRef}
                  type="text"
                  value={manualCode}
                  onChange={(e) => setManualCode(e.target.value)}
                  placeholder="Ketik kode barcode…"
                  disabled={excelData.length === 0}
                  className="flex-1 bg-muted border border-border rounded-xl px-3 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50" />
                
                  <button
                  type="submit"
                  disabled={!manualCode.trim() || excelData.length === 0}
                  className="bg-primary text-primary-foreground px-4 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-40 hover:bg-primary/90 transition-colors">
                  
                    Tambah
                  </button>
                </form>
              </div>
            </div>

            {results.length > 0 &&
          <button
            onClick={() => setActiveTab("Hasil")}
            className="w-full flex items-center justify-center gap-2 border border-primary/30 text-primary bg-accent py-3 rounded-xl font-semibold text-sm hover:bg-accent/80 transition-colors">
            
                Lihat {results.length} Hasil <ChevronRight className="w-4 h-4" />
              </button>
          }
          </div>
        }

        {/* ── TAB: HASIL ── */}
        {activeTab === "Hasil" &&
        <div className="flex flex-col gap-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-foreground">Hasil Scan</h2>
                <p className="text-muted-foreground text-sm mt-0.5">
                  {results.length} data tersusun sesuai urutan scan
                </p>
              </div>
              <div className="flex gap-2">
                {sortedFullData.length > 0 &&
              <>
                    <button
                  onClick={() => setShowConfirmReset(true)}
                  className="flex items-center gap-1.5 border border-destructive/40 text-destructive px-3 py-2 rounded-xl text-xs font-semibold hover:bg-destructive/10 transition-colors">
                  
                      <Trash2 className="w-3.5 h-3.5" />
                      Hapus Riwayat
                    </button>
                    <button
                  onClick={handleExport}
                  className="flex items-center gap-1.5 bg-primary text-primary-foreground px-3 py-2 rounded-xl text-xs font-semibold hover:bg-primary/90 transition-colors">
                  
                      <Download className="w-3.5 h-3.5" />
                      Export .xlsx
                    </button>
                  </>
              }
              </div>
            </div>

            {sortedFullData.length === 0 ?
          <div className="flex flex-col items-center justify-center py-16 gap-4">
                <div className="w-20 h-20 rounded-3xl bg-muted flex items-center justify-center">
                  <ScanLine className="w-9 h-9 text-muted-foreground/40" />
                </div>
                <div className="text-center">
                  <p className="font-semibold text-muted-foreground">Belum ada data</p>
                  <p className="text-sm text-muted-foreground/70 mt-1">Upload Excel lalu scan QR code</p>
                </div>
                <button
              onClick={() => setActiveTab("Upload")}
              className="flex items-center gap-2 bg-primary text-primary-foreground px-5 py-2.5 rounded-xl text-sm font-semibold hover:bg-primary/90 transition-colors">
              
                  <Upload className="w-4 h-4" />
                  Upload Excel
                </button>
              </div> :

          <>
                {/* Stats */}
                <div className="grid grid-cols-3 gap-3">
                  {[
              { label: "Total Data", value: sortedFullData.length, color: "text-primary" },
              { label: "Sudah Scan", value: sortedFullData.filter((r) => r._scanned).length, color: "text-green-600" },
              { label: "Belum Scan", value: sortedFullData.filter((r) => !r._scanned).length, color: "text-amber-600" }].
              map(({ label, value, color }) =>
              <div key={label} className="bg-card border border-border rounded-2xl p-3 text-center">
                      <p className={`text-xl font-bold ${color}`}>{value}</p>
                      <p className="text-[10px] text-muted-foreground font-medium mt-0.5 leading-tight">{label}</p>
                    </div>
              )}
                </div>

                {/* Full sorted table */}
                <div className="rounded-2xl border border-border overflow-hidden bg-card">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-primary/5 border-b border-border">
                          <th className="text-left px-3 py-2.5 text-xs font-semibold text-muted-foreground w-10">#</th>
                          {columns.map((col) =>
                      <th key={col} className="text-left px-3 py-2.5 text-xs font-semibold text-muted-foreground whitespace-nowrap">{col}</th>
                      )}
                          <th className="text-left px-3 py-2.5 text-xs font-semibold text-muted-foreground w-20">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {sortedFullData.map((item, idx) =>
                    <tr
                      key={idx}
                      className={`border-b border-border/60 last:border-0
                              ${item._scanned ? "bg-green-50/60" : "hover:bg-muted/30"}`}>
                      
                            <td className="px-3 py-2.5 text-muted-foreground font-mono text-xs">{idx + 1}</td>
                            {columns.map((col) =>
                      <td key={col} className="px-3 py-2.5 text-xs whitespace-nowrap">
                                {String(item[col] ?? "")}
                              </td>
                      )}
                            <td className="px-3 py-2.5">
                              {item._scanned ?
                        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-green-700 bg-green-100 px-2 py-0.5 rounded-full">
                                  <CheckCircle2 className="w-3 h-3" />
                                  Scan #{item._scan_order}
                                </span> :

                        <span className="inline-flex text-[10px] font-semibold text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                                  Belum
                                </span>
                        }
                            </td>
                          </tr>
                    )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
          }
          </div>
        }
      </main>

      {/* Confirm Reset Dialog */}
      {showConfirmReset &&
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="bg-card rounded-2xl border border-border p-6 w-full max-w-sm flex flex-col gap-4 shadow-xl">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-destructive/10 flex items-center justify-center flex-shrink-0">
                <Trash2 className="w-5 h-5 text-destructive" />
              </div>
              <div>
                <p className="font-bold text-foreground">Hapus Riwayat Scan?</p>
                <p className="text-xs text-muted-foreground mt-0.5">Semua urutan scan akan dihapus. Data Excel tetap ada.</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
              onClick={() => setShowConfirmReset(false)}
              className="flex-1 py-2.5 rounded-xl border border-border text-sm font-semibold text-muted-foreground hover:bg-muted transition-colors">
              
                Batal
              </button>
              <button
              onClick={handleReset}
              className="flex-1 py-2.5 rounded-xl bg-destructive text-destructive-foreground text-sm font-semibold hover:bg-destructive/90 transition-colors">
              
                Hapus
              </button>
            </div>
          </div>
        </div>
      }
    </div>);

}