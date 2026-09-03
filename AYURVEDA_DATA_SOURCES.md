# IP-SAKTI — Ayurveda Dataset Sources

## Purpose

This document records authoritative sources that can be used to build
the Ayurveda and Traditional Knowledge knowledge base for IP-SAKTI.

The dataset should prioritize official Government of India and
authorized sources.

---

# 1. CCRAS — Database on Medicinal Plants

Authority:
Central Council for Research in Ayurvedic Sciences (CCRAS)
Ministry of Ayush, Government of India

Source:
Database on Medicinal Plants

URL:
https://ccras.nic.in/documents/database-on-medicinal-plants/

Use for:

- Medicinal plants
- Ayurveda-related plant information
- Published references
- Classical literature references
- Botanical information
- Traditional medicine references

Priority:
P0

---

# 2. AYUSH Research Portal

Authority:
Ministry of Ayush, Government of India

URL:
https://arp.ayush.gov.in/

Use for:

- Ayurveda research
- Research publications
- Medicinal plant research
- Ayurvedic drug research
- Traditional medicine research
- Evidence-based Ayurveda information

Priority:
P0

---

# 3. E-Charak Knowledge Resources

Authority:
Ministry of Ayush, Government of India

URL:
https://echarak.ayush.gov.in/knowledge_resources

Use for:

- Indian medicinal plants
- Botanical names
- Vernacular names
- Ayurveda plant information
- Plant identification references

Priority:
P0

---

# 4. Traditional Knowledge Digital Library (TKDL)

Authority:
CSIR and Ministry of Ayush, Government of India

URL:
https://www.tkdl.res.in/

Use for:

- Traditional knowledge context
- Ayurveda formulations
- Traditional uses
- Prior-art context
- Traditional knowledge classification
- Understanding the relationship between Ayurveda and IP protection

Priority:
P0

Important access note:

The full TKDL database is not a public unrestricted dataset.
The TKDL website states that full database access is available to
Patent Offices under TKDL Access Agreements.

Therefore, IP-SAKTI should not scrape or copy the full restricted TKDL
database.

Only publicly available or explicitly authorized material should be
used.

---

# 5. Ayurveda Data Categories

The initial dataset should focus on:

1. Medicinal plants
2. Botanical names
3. Vernacular names
4. Ayurvedic names
5. Traditional uses
6. Useful parts of plants
7. Ayurvedic formulations
8. Formulation ingredients
9. Traditional knowledge references
10. Source texts
11. Bibliographic references

---

# 6. Dataset Structure

Each record should contain, where available:

- Record ID
- Category
- Ayurveda Name
- Botanical Name
- Vernacular Names
- Useful Part
- Traditional Use
- Formulation Name
- Ingredients
- Source Text
- Source Organization
- Source URL
- Publication Year
- Language
- License / Access Status
- Legal Use Note
- Reference

---

# 7. Source Priority

Use sources in the following order:

1. Government of India / Ministry of Ayush
2. CCRAS
3. Official AYUSH Research Portal
4. Official E-Charak resources
5. TKDL public or authorized material
6. Public-domain or appropriately licensed classical texts
7. Other permitted datasets

Avoid:

- Random blogs
- Wikipedia as the primary source
- Quora
- Reddit
- Unverified PDFs
- AI-generated datasets
- Synthetic traditional knowledge
- Scraped restricted databases

---

# 8. Legal and Ethical Requirements

Traditional knowledge should not be invented or synthetically generated.

Every record should retain its source.

Where access or licensing restrictions apply, the dataset should record
those restrictions instead of copying restricted content.

Community-held or non-public traditional knowledge should only be
included where there is an appropriate legal and ethical basis for its
use.

---

# 9. Relationship With IP Dataset

The Ayurveda dataset and IP dataset have different purposes.

Ayurveda dataset:

Traditional knowledge, plants, formulations, traditional uses and
supporting references.

IP dataset:

Patentability, patent law, trademarks, geographical indications,
traditional knowledge-related patent issues and IP procedures.

The two datasets can be connected during RAG retrieval.

Example:

Ayurveda data:
A medicinal plant has a traditionally documented use.

IP data:
Section 3(p) and relevant guidelines may need to be considered when
assessing patentability.

---

# 10. Initial Goal

The first version should be a small, authoritative starter dataset.

Quality and traceability are more important than creating a very large
number of records.

Each record should have a source and should be traceable back to the
original authoritative material.