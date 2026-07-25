#!/usr/bin/env python3
"""
update_resume.py — re-scrape a .docx resume and push the new content into
the resume page (index.html).

Usage:
    python update_resume.py            # reads Pulikesi_Dinesh_Kumar.docx, rewrites index.html in place
    python update_resume.py other.docx other.html -o updated.html   # override any of them

How it works:
  1. Reads word/document.xml straight out of the .docx zip and pulls out
     paragraph text (no python-docx dependency needed).
  2. Parses that text into the same shape the page expects: skill groups,
     jobs (with nested projects/bullets), honors, and education.
  3. The page embeds its own original source as one big JSON string inside
     a <script type="__bundler/template"> tag. This script decodes that
     string, replaces the data arrays inside the embedded Component class
     via regex, re-encodes it, and writes a new HTML file.

NOTE: this only updates the four data arrays (skillGroups / jobs / honors /
education). If you restructure the resume sections drastically, re-check
the regexes below — they expect the same paragraph patterns as the
original resume (see PATTERNS section).
"""
import argparse
import json
import re
import sys
import zipfile
from xml.sax.saxutils import unescape

W_T_RE = re.compile(r"<w:t[^>]*>([^<]*)</w:t>")
NUMPR_RE = re.compile(r"<w:numPr>")


def extract_paragraphs(docx_path):
    with zipfile.ZipFile(docx_path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    paras = xml.split("</w:p>")
    out = []
    for p in paras:
        texts = W_T_RE.findall(p)
        text = unescape("".join(texts))
        if text.strip():
            out.append(text)
    return out


# ---------- PATTERNS ----------
DATE_RANGE_RE = re.compile(
    r"^([A-Za-z]{3,4}\.?\s+\d{4}\s*[–-]\s*[A-Za-z]{3,4}\.?\s*\d{4})\s*\|\s*([^|]+)\|\s*(.+)$"
)
# Same date-range header, but findable mid-string. Some docx paragraphs glue a
# job header onto the tail of the previous job's last bullet (no paragraph
# break); the trailing "| Company |" is what distinguishes it from prose dates.
DATE_HEADER_SEARCH = re.compile(
    r"[A-Za-z]{3,4}\.?\s+\d{4}\s*[–-]\s*[A-Za-z]{3,4}\.?\s*\d{4}\s*\|"
)
PROJECT_RE = re.compile(r"^Project:\s*(.+)$")
YEAR_RE = re.compile(r"(\d{4})\s*$")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
URL_RE = re.compile(r"https?://\S+")


def split_bullets(paragraph):
    """A paragraph can contain several '• ' separated bullets run together."""
    parts = [b.strip() for b in paragraph.split("•") if b.strip()]
    return parts


def split_top_level_commas(s):
    """Split on commas that are not inside parentheses, e.g. keep
    'GitHub Copilot (development, production debugging)' as one item."""
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            depth += 1
            cur += ch
        elif ch == ")":
            depth = max(0, depth - 1)
            cur += ch
        elif ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def start_job(data, m):
    """Build a job from a DATE_RANGE_RE match, append it, and return
    (job, current_project). Splits a "Project: X" that the docx glued onto
    the role into its own project so following bullets have somewhere to go."""
    role = m.group(3).strip()
    job = {
        "dates": m.group(1).replace("–", "–"),
        "company": m.group(2).strip(),
        "role": role,
        "projects": [],
    }
    data["jobs"].append(job)
    project = None
    if "Project:" in role:
        role_part, proj_title = role.split("Project:", 1)
        job["role"] = role_part.strip()
        project = {"title": proj_title.strip(), "bullets": []}
        job["projects"].append(project)
    return job, project


def parse_resume(paragraphs):
    data = {
        "name": "",
        "contact": {},
        "skillGroups": [],
        "honors": [],
        "jobs": [],
        "education": [],
    }

    section = None
    current_job = None
    current_project = None

    for para in paragraphs:
        stripped = para.strip()

        if stripped.upper().startswith("SKILLS"):
            section = "skills"
            continue
        if stripped.upper().startswith("WORK EXPERIENCE"):
            section = "experience"
            continue
        if stripped.upper().startswith("EDUCATIONAL PROFILE"):
            section = "education"
            continue
        if "PROFESSIONAL CERTIFICATIONS" in stripped.upper() or "HONORS" in stripped.upper() and section != "experience":
            section = "honors"
            continue
        if "KEY TECHNICAL SKILLS" in stripped.upper():
            continue

        if section is None:
            # first paragraph: name, location, phone(s), email, github, linkedin all run together
            if not data["name"] and "(" in stripped:
                data["name"] = stripped.split("(")[0].strip()
                m = re.search(r"\(([^)]+)\)", stripped)
                if m:
                    data["contact"]["location"] = m.group(1).strip()
                data["contact"]["phones"] = PHONE_RE.findall(stripped)
                em = EMAIL_RE.search(stripped)
                if em:
                    data["contact"]["email"] = em.group(0)
                for url in URL_RE.findall(stripped):
                    if "github.com" in url:
                        data["contact"]["github"] = url.rstrip("|").strip()
                    elif "linkedin.com" in url:
                        data["contact"]["linkedin"] = url.rstrip("|").strip()
            continue

        if section == "skills":
            for chunk in split_bullets(stripped):
                if ":" in chunk:
                    label, items = chunk.split(":", 1)
                    items = split_top_level_commas(items)
                    data["skillGroups"].append({"label": label.strip(), "items": items})
            continue

        if section == "honors":
            for chunk in split_bullets(stripped) or [stripped]:
                m = YEAR_RE.search(chunk)
                if m:
                    year = m.group(1)
                    name = chunk[: m.start()].strip()
                    data["honors"].append({"name": name, "year": year})
            continue

        if section == "experience":
            m = DATE_RANGE_RE.match(stripped)
            if m:
                current_job, current_project = start_job(data, m)
                continue
            pm = PROJECT_RE.match(stripped)
            if pm and current_job is not None:
                current_project = {"title": pm.group(1).strip(), "bullets": []}
                current_job["projects"].append(current_project)
                continue
            if current_project is not None:
                for b in split_bullets(stripped):
                    # A bullet can have the next job's header glued onto its end
                    # (docx has no paragraph break). Split it off and start that
                    # job so its projects/bullets aren't swallowed by this one.
                    dm = DATE_HEADER_SEARCH.search(b)
                    if dm and dm.start() > 0:
                        lead = b[: dm.start()].strip()
                        if lead:
                            current_project["bullets"].append(lead)
                        hm = DATE_RANGE_RE.match(b[dm.start():].strip())
                        if hm:
                            current_job, current_project = start_job(data, hm)
                    else:
                        current_project["bullets"].append(b)
            continue

        if section == "education":
            if "|" in stripped:
                degree, school = stripped.split("|", 1)
                data["education"].append({"degree": degree.strip(), "school": school.strip()})
            continue

    return data


def add_headline(data):
    """Sidebar headline = the most recent job's role."""
    if data["jobs"]:
        data["headline"] = data["jobs"][0]["role"]
    return data


DATA_SCRIPT_RE = re.compile(r'(<script[^>]*id="resume-data"[^>]*>)(.*?)(</script>)', re.S)


def inject_data(html, data):
    """Replace the JSON in the #resume-data island with the parsed resume."""
    if not DATA_SCRIPT_RE.search(html):
        raise ValueError('Could not find <script id="resume-data"> in the HTML')
    blob = json.dumps(data, ensure_ascii=False)
    # Keep it safe inside <script>: escape "</" so no literal </script> can appear.
    # json.loads / JSON.parse both accept the "<\/" escape.
    blob = blob.replace("</", "<\\/")
    return DATA_SCRIPT_RE.sub(lambda m: m.group(1) + blob + m.group(3), html, count=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx", nargs="?", default="Pulikesi_Dinesh_Kumar.docx")
    ap.add_argument("html", nargs="?", default="index.html")
    ap.add_argument("-o", "--output", default=None)
    args = ap.parse_args()

    data = add_headline(parse_resume(extract_paragraphs(args.docx)))

    with open(args.html, "r", encoding="utf-8") as f:
        html = f.read()

    new_html = inject_data(html, data)

    out_path = args.output or args.html
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_html)
    print(f"Updated {len(data['jobs'])} jobs, {len(data['skillGroups'])} skill groups, "
          f"{len(data['honors'])} honors, {len(data['education'])} education entries.")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
