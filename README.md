# Çoklu Kaynak ve Metadata Destekli RAG Sistemi

Farklı formatlardaki şirket dokümanlarını (TXT, CSV, JSON) birleştirerek kullanıcı sorularına doğru ve kaynak gösteren cevaplar üreten bir RAG (Retrieval-Augmented Generation) pipeline'ı.

Sistem, çakışan bilgilerde tarih bazlı çakışma çözümü yapar: `guncellemeler.json` dosyasındaki en güncel kayıt, `sozlesme.txt` veya `paket_fiyatlari.csv` içindeki eski bilginin önüne geçer.

---

## Özellikler

- **Hibrit Veri İşleme**: TXT (sözleşme), CSV (fiyat tablosu), JSON (güncelleme logları) tek pipeline'da birleştirilir.
- **Tablo Verisi Koruma**: CSV satırları, sütun başlıklarıyla birlikte yapısal cümleye dönüştürülerek chunk'lanır — tablo bağlamı bozulmaz.
- **Çakışma Çözümü**: Aynı konuya değinen kaynaklar arasında JSON (en yeni tarih) önceliklidir. Hem retrieval seviyesinde sıralama hem de prompt seviyesinde LLM talimatı ile uygulanır.
- **Otomatik Re-indexing**: Startup'ta her data dosyasının MD5 hash'i kontrol edilir. Dosyalar manuel değiştirildiğinde sistem otomatik olarak yeniden indexler.
- **Metadata Filtreleme & Kaynak Gösterimi**: Her cevabın sonunda hangi dosyalardan ve tarihlerden yararlanıldığı referans olarak gösterilir.

---

## Teknoloji Stack

| Katman | Seçim | Neden |
|---|---|---|
| Framework | LangChain 0.3.x (LCEL) | Olgun RAG ekosistemi, modüler yapı |
| Embedding | `paraphrase-multilingual-mpnet-base-v2` | Türkçe desteği, local & ücretsiz |
| Vector Store | ChromaDB (persistent) | Local, kolay kurulum |
| LLM | `openai/gpt-4o` (OpenRouter veya OpenAI) | Kullanıcı tarafından sağlanan API |
| Arayüz | Python CLI (argparse) | Hızlı test ve gösterim |

---

## Kurulum

### 1. Bağımlılıkları yükle

```bash
# Sanal ortam (önerilen)
python3 -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

> **Not:** İlk çalıştırmada HuggingFace embedding modeli (~1GB) indirilecek. Bir kez indirilir, sonraki çalıştırmalarda cache'den kullanılır.

### 2. API key'ini ayarla

```bash
cp .env.example .env
```

**Seçenek A — OpenRouter** (test edildi, önerilen):

```
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxx
OPENROUTER_MODEL=openai/gpt-4o
```

**Seçenek B — Doğrudan OpenAI** (kod destekliyor, test edilmedi):

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o
```

> **Not:** Bu proje OpenRouter API ile geliştirilip test edilmiştir. Doğrudan OpenAI API desteği kod seviyesinde eklenmiş olmakla birlikte, OpenAI key'i bulunmadığından test edilememiştir. LangChain'in standart `ChatOpenAI` sınıfını kullandığından OpenAI ile de sorunsuz çalışması beklenmektedir.

### 3. Çalıştır

```bash
# İnteraktif mod (sorular sor)
python main.py

# Tek soru
python main.py -q "Pro paketin aylık fiyatı nedir?"

# Debug: retrieval sonucu alınan chunk'ları göster
python main.py --debug

# Veriyi zorla yeniden indexle
python main.py --reindex
```

İlk çalıştırmada `ingest` adımı otomatik olarak tetiklenir ve tüm veri dosyaları ChromaDB'ye yüklenir.

---

## Kullanım Örnekleri

### Örnek 1: Tek kaynaklı soru (CSV)

```
Soru > Pro paketin aylık fiyatı nedir?

Pro paketinin aylık fiyatı 299 TL'dir.

---
Kaynaklar:
• paket_fiyatlari.csv | Pro satırı
```

### Örnek 2: Hibrit soru (CSV + TXT + JSON çakışması)

```
Soru > Pro paketin fiyatı nedir ve iptal edersem param ne zaman iade edilir?

Pro paketinin aylık fiyatı 299 TL'dir. İptal etmeniz durumunda iade süreniz
30 gündür (Pro paket için 01.06.2024 tarihinde güncellenmiştir — önceki süre
14 gündü). İade işlemi onaylandıktan sonra 5 iş günü içinde ödeme yöntemine
iade edilir.

---
Kaynaklar:
• paket_fiyatlari.csv | Pro satırı
• guncellemeler.json  | 2024-06-01 | Pro paketi iade süresi
• guncellemeler.json  | 2024-11-20 | Tüm paketler iade işlem süresi
```

### Örnek 3: Dinamik test (veriyi manuel değiştirme)

```bash
# CSV'de Pro paket fiyatını değiştir (örn. 299 → 399)
# Sonra tekrar çalıştır:
python main.py -q "Pro paketin aylık fiyatı nedir?"
# Sistem hash değişikliğini algılar ve otomatik re-index yapar.
# Cevap: 399 TL
```

---

## Mimari

Detaylı mimari kararlar için [`ARCHITECTURE.md`](ARCHITECTURE.md) dosyasına bakın.

### Veri Akışı

```
                  ┌────────────────┐
                  │  data/*.txt    │
                  │  data/*.csv    │
                  │  data/*.json   │
                  └────────┬───────┘
                           │
                  ┌────────▼───────┐
                  │ Loader'lar     │  ── Metadata eklenir
                  │ (src/loaders/) │     (source, date, article_id...)
                  └────────┬───────┘
                           │
                  ┌────────▼───────┐
                  │ HuggingFace    │  ── paraphrase-multilingual-mpnet
                  │ Embeddings     │
                  └────────┬───────┘
                           │
                  ┌────────▼───────┐
                  │  ChromaDB      │  ── Persistent, hash-checked
                  └────────┬───────┘
                           ▲
                           │
      (sorgu) ──► Embedder ──► Similarity Search
                                      │
                                      ▼
                        ┌──────────────────────┐
                        │  Retriever           │
                        │  (priority + date    │
                        │   sorting)           │
                        └──────────┬───────────┘
                                   │
                        ┌──────────▼───────────┐
                        │  ChatOpenAI          │
                        │  (OpenRouter GPT-4o) │
                        │  + system prompt     │
                        └──────────┬───────────┘
                                   │
                                   ▼
                              [ Cevap ]
                         + Kaynaklar bölümü
```

### Dosya Yapısı

```
.
├── data/
│   ├── sozlesme.txt            # Müşteri sözleşmesi (madde bazlı)
│   ├── paket_fiyatlari.csv     # Basic / Pro / Enterprise fiyatları
│   └── guncellemeler.json      # Tarihli değişiklik logları
├── src/
│   ├── loaders/
│   │   ├── txt_loader.py       # Madde bazlı chunking
│   │   ├── csv_loader.py       # Satır → yapısal cümle
│   │   └── json_loader.py      # Log → tarihli chunk
│   ├── embedder.py             # HuggingFace multilingual embedding
│   ├── vector_store.py         # ChromaDB yönetimi
│   ├── hash_check.py           # MD5 tabanlı değişiklik algılama
│   ├── retriever.py            # Similarity + priority sorting
│   ├── llm.py                  # OpenRouter ChatOpenAI
│   └── rag_chain.py            # Retrieval + Generation (LCEL)
├── chroma_db/                  # ChromaDB persistent storage (gitignore)
├── ingest.py                   # Indexleme pipeline'ı
├── main.py                     # CLI giriş noktası
├── requirements.txt
├── .env.example
├── PLAN.md                     # Uygulama planı
├── ARCHITECTURE.md             # Mimari kararlar
├── DATA_SCHEMA.md              # Veri şeması
└── README.md
```

---

## Mimari Öne Çıkanlar

### 1. CSV Verisi Nasıl Vektörize Edilir?

Standart text chunking CSV tablolarını bozar. Bu projede her satır, sütun başlıklarıyla birleştirilerek tek bir bağlamlı cümleye dönüştürülür:

```
[Paket Bilgisi] Paket Adi: Pro | Aylik Fiyat Tl: 299 | Yillik Fiyat Tl: 2990 |
Kullanici Limiti: 10 | Depolama Gb: 100 | Destek Turu: Oncelikli E-posta ve Chat |
Api Erisimi: Evet | Api Aylik Limit: 10000
```

Bu şekilde embedding modeli, "Pro paket fiyatı" gibi sorguları doğru satıra eşleştirebilir.

### 2. Çakışma Çözümü Nasıl Çalışır?

İkili strateji:

**(A) Retrieval seviyesinde** — `src/retriever.py` içinde her chunk bir `(priority, date)` tuple'ıyla sıralanır:
- `guncellemeler.json` en yüksek öncelik (yeni tarih → önce)
- `sozlesme.txt` orta
- `paket_fiyatlari.csv` düşük

**(B) Prompt seviyesinde** — System prompt (`src/rag_chain.py`) LLM'e açıkça çakışma kuralını söyler: "Eğer hem sözleşme hem güncelleme aynı konuya değiniyorsa, en yüksek tarihli güncellemeyi esas al, eskiyi cevabında tekrar etme."

### 3. Dinamik Veri Testi

`src/hash_check.py` her data dosyasının MD5 hash'ini `chroma_db/hashes.json` içinde saklar. `main.py` her başlatmada `ingest()` çağırır; `ingest()` hash'leri karşılaştırır ve farklıysa collection'ı sıfırlayıp yeniden indexler. Böylece evaluator CSV/JSON dosyasını manuel değiştirdikten sonra hiçbir ekstra komut çalıştırmak zorunda kalmaz.

### 4. Metadata Şeması

Her chunk'ın metadata'sında şu alanlar bulunur (detay için [`DATA_SCHEMA.md`](DATA_SCHEMA.md)):

```python
{
  "source_file": "sozlesme.txt | paket_fiyatlari.csv | guncellemeler.json",
  "chunk_type":  "contract_article | pricing_row | update_log",
  "chunk_id":    "benzersiz ID",
  "date":        "YYYY-MM-DD"  # sadece JSON chunk'larda
  "article_id":  "4.1"         # sadece TXT chunk'larda
  "paket_adi":   "Pro"         # CSV ve JSON chunk'larda
}
```

---

## Test Senaryoları

Sistem aşağıdaki dinamik senaryolar için tasarlandı:

| Senaryo | Test |
|---|---|
| CSV'de fiyat değişikliği | `paket_fiyatlari.csv` içindeki Pro fiyatını değiştir → sistem yeni fiyatı döner |
| JSON'a yeni log eklenmesi | `guncellemeler.json`'a "Basic iade süresi 7 güne düşürüldü" ekle → sistem yeni süreyi döner |
| TXT vs JSON çakışması | Sözleşmede 14 gün yazılıyken JSON'da 30 gün olması → sistem 30 günü döner |
| Statik cevap yok | Data dosyaları değiştiğinde cevap gerçekten değişir (otomatik re-index sayesinde) |

---

## Bilinen Sınırlamalar

- İlk çalıştırma: HuggingFace embedding modeli indirilirken ~1-2 dakika sürebilir.
- ChromaDB sıfırlama: Herhangi bir data dosyası değişirse TÜM collection yeniden oluşturulur (partial re-indexing yok). Bu projeye uygun çünkü veri boyutu küçük.
- Dil: Sistem Türkçe için optimize edilmiştir. İngilizce sorular da çalışır ancak embedding modeli Türkçe içerikle daha iyi eşleşir.
