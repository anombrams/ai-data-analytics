# AI Data Portal

Portal analisis data berbasis AI yang dibangun dengan Streamlit, menggunakan Claude AI (Anthropic) untuk menghasilkan insight otomatis, menjawab pertanyaan tentang data, dan merekomendasikan visualisasi.

## Fitur

- **Multi-file Upload** — Upload beberapa file CSV/Excel sekaligus
- **Spreadsheet Editor** — Edit data langsung di browser dengan dukungan formula
- **Dashboard Builder** — Generate dashboard otomatis dengan AI
- **AI Chat** — Tanya jawab tentang data menggunakan bahasa alami
- **Visualisasi** — Buat chart interaktif dengan Plotly
- **AI Insights** — Analisis dan rekomendasi otomatis dari Claude AI
- **Export** — Ekspor dashboard ke PDF atau PowerPoint

## Struktur Proyek

```
ai_data_portal/
├── app.py                        # Entry point aplikasi Streamlit
├── requirements.txt              # Dependensi Python
├── components/
│   ├── chat_interface.py         # Komponen chat AI
│   ├── dashboard_builder.py      # Builder dashboard otomatis
│   ├── data_table.py             # Tabel data dengan filter
│   ├── spreadsheet.py            # Editor spreadsheet
│   └── visualizer.py             # Komponen visualisasi chart
├── utils/
│   ├── ai_engine.py              # Integrasi Claude AI (Anthropic)
│   ├── data_analyzer.py          # Analisis statistik data
│   ├── data_loader.py            # Load file CSV/Excel
│   └── exporter.py               # Export ke PDF/PowerPoint
└── deploy/
    ├── nginx.conf                # Konfigurasi Nginx
    ├── ai-data-portal.service    # Systemd service
    ├── install.sh                # Script instalasi server
    ├── README.md                 # Panduan deploy
    └── QUICK_REFERENCE.md        # Referensi cepat perintah
```

## Prasyarat

- Python 3.10+
- Anthropic API Key ([dapatkan di sini](https://console.anthropic.com/))

## Instalasi

1. Clone repository:
   ```bash
   git clone https://github.com/acndigitalenterprise/ai-data-portal.git
   cd ai-data-portal
   ```

2. Buat virtual environment dan install dependensi:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. (Opsional) Buat file `.env` untuk menyimpan API key:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

## Menjalankan Aplikasi

```bash
streamlit run app.py
```

Aplikasi akan berjalan di `http://localhost:8501`.

## Cara Penggunaan

1. Masukkan **Anthropic API Key** di sidebar
2. **Upload file** CSV atau Excel (bisa multiple file)
3. Lihat **Overview** untuk ringkasan dan insight otomatis
4. Edit data di tab **Spreadsheet**
5. Generate **Dashboard** otomatis dengan AI
6. Gunakan **AI Chat** untuk bertanya tentang data
7. **Export** hasil ke PDF atau PowerPoint

## Tech Stack

| Komponen | Teknologi |
|---|---|
| UI Framework | [Streamlit](https://streamlit.io/) |
| AI Model | [Claude (Anthropic)](https://www.anthropic.com/) |
| Visualisasi | [Plotly](https://plotly.com/) |
| Data Processing | [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/) |
| Export PDF | [fpdf2](https://py-fpdf2.readthedocs.io/) |
| Export PPT | [python-pptx](https://python-pptx.readthedocs.io/) |

## Deploy ke Server

Lihat panduan lengkap di [`deploy/README.md`](deploy/README.md) untuk instruksi deploy menggunakan Nginx + systemd.

## Lisensi

Proyek ini dikembangkan untuk keperluan internal Boyolali.
