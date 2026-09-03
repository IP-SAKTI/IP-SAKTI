from pathlib import Path
import json
from pypdf import PdfReader


RAW_DIR = Path("data/raw/ip")
PROCESSED_DIR = Path("data/processed/ip")


def extract_pdf_text(pdf_path):
    reader = PdfReader(str(pdf_path))
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        pages.append({
            "page": page_number,
            "text": text.strip()
        })

    return pages


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(RAW_DIR.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found.")
        return

    print(f"Found {len(pdf_files)} PDF files.")

    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")

        pages = extract_pdf_text(pdf_path)

        output = {
            "document_id": pdf_path.stem.split("_")[0],
            "file_name": pdf_path.name,
            "source_path": str(pdf_path),
            "page_count": len(pages),
            "pages": pages
        }

        output_path = PROCESSED_DIR / f"{pdf_path.stem}.json"

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()