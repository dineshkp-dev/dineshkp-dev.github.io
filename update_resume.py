#!/usr/bin/env python3
"""
update_resume.py — re-scrape a .docx resume and push the new content into
the standalone resume page (Dinesh Kumar Resume - standalone.html).

Usage:
    python update_resume.py Resume.docx "Dinesh Kumar Resume - standalone.html" -o updated.html

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
PROJECT_RE = re.compile(r"^Project:\s*(.+)$")
YEAR_RE = re.compile(r"(\d{4})\s*$")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
URL_RE = re.compile(r"https?://\S+")


def split_bullets(paragraph):
    """A paragraph can contain several '• ' separated bullets run together."""
    parts = [b.strip() for b in paragraph.split("•") if b.strip()]
    return parts


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
                    items = [i.strip() for i in items.split(",") if i.strip()]
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
                current_job = {
                    "dates": m.group(1).replace("–", "\u2013"),
                    "company": m.group(2).strip(),
                    "role": m.group(3).strip(),
                    "projects": [],
                }
                data["jobs"].append(current_job)
                current_project = None
                continue
            pm = PROJECT_RE.match(stripped)
            if pm and current_job is not None:
                current_project = {"title": pm.group(1).strip(), "bullets": []}
                current_job["projects"].append(current_project)
                continue
            if current_project is not None:
                for b in split_bullets(stripped):
                    current_project["bullets"].append(b)
            continue

        if section == "education":
            if "|" in stripped:
                degree, school = stripped.split("|", 1)
                data["education"].append({"degree": degree.strip(), "school": school.strip()})
            continue

    return data


def js_string(s):
    return json.dumps(s, ensure_ascii=False)


def js_array_literal(name, items, indent="      "):
    def obj_lines(o, ind):
        lines = []
        for k, v in o.items():
            if isinstance(v, list):
                sub = ",\n".join(f"{ind}  {js_string(x)}" for x in v)
                lines.append(f"{ind}  {k}: [\n{sub}\n{ind}  ]")
            elif isinstance(v, dict):
                pass
            else:
                lines.append(f"{ind}  {k}: {js_string(v)}")
        return ",\n".join(lines)

    entries = []
    for item in items:
        if "projects" in item:
            proj_entries = []
            for proj in item["projects"]:
                bullets = ",\n".join(f"{indent}      {js_string(b)}" for b in proj["bullets"])
                proj_entries.append(
                    f"{indent}    {{ title: {js_string(proj['title'])}, bullets: [\n{bullets}\n{indent}    ]}}"
                )
            projects_block = ",\n".join(proj_entries)
            entries.append(
                f"{indent}  {{\n{indent}    dates: {js_string(item['dates'])}, role: {js_string(item['role'])}, company: {js_string(item['company'])},\n"
                f"{indent}    projects: [\n{projects_block}\n{indent}    ]\n{indent}  }}"
            )
        else:
            entries.append(f"{indent}  {{ {obj_lines(item, indent)} }}")
    body = ",\n".join(entries)
    return f"{name}: [\n{body}\n{indent}]"


def replace_array_block(source, array_name, new_literal):
    """Replace `name: [ ... ]` (balanced brackets) with new_literal, keeping trailing comma."""
    key = f"{array_name}: ["
    start = source.index(key)
    depth = 0
    i = start + len(key) - 1  # position of the opening '['
    for j in range(i, len(source)):
        if source[j] == "[":
            depth += 1
        elif source[j] == "]":
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    else:
        raise ValueError(f"Could not find end of array for {array_name}")
    return source[:start] + new_literal + source[end:]


def update_contact(source, contact):
    if not contact:
        return source

    if contact.get("name"):
        source = re.sub(
            r"(letter-spacing:0\.01em;\">)[^<]+(</div>)",
            lambda m: m.group(1) + contact["name"] + m.group(2),
            source,
            count=2,  # sidebar heading + mobile header link both use this text
        )
        # mobile header link has a different style string; swap by exact prior name text if still present
        source = re.sub(
            r'(font-size:16px; font-weight:600; white-space:nowrap;">)[^<]+(</a>)',
            lambda m: m.group(1) + contact["name"] + m.group(2),
            source,
        )

    if contact.get("location"):
        source = re.sub(
            r'(color:rgba\(255,255,255,0\.55\); margin-top:4px;\">)[^<]+(</div>)',
            lambda m: m.group(1) + contact["location"] + m.group(2),
            source,
        )

    phones = contact.get("phones") or []
    if phones:
        def digits(p):
            return re.sub(r"[^\d+]", "", p)
        # rebuild the PHONE table cell entirely so any number of phone lines works
        phone_links = "".join(
            f'<a href="tel:{digits(p)}" style="color:rgba(255,255,255,0.85); text-decoration:none; display:block;'
            + (' margin-top:4px;"' if i else '"') + f'>{p.strip()}</a>'
            for i, p in enumerate(phones)
        )
        source = re.sub(
            r'(<td style="padding:6px 0;"><a href="tel:).*?(</td>\s*</tr>\s*<tr>\s*<td[^>]*>MAIL)',
            lambda m: '<td style="padding:6px 0;">' + phone_links + m.group(2),
            source,
            flags=re.S,
        )

    if contact.get("email"):
        email = contact["email"]
        source = re.sub(
            r'href="mailto:[^"]+"',
            f'href="mailto:{email}"',
            source,
        )
        source = re.sub(
            r'(word-break:break-all;\"><a href="mailto:[^"]+" style="color:rgba\(255,255,255,0\.85\); text-decoration:none;\">)[^<]+(</a>)',
            lambda m: m.group(1) + email + m.group(2),
            source,
        )

    if contact.get("github"):
        gh = contact["github"].rstrip("/")
        handle = gh.rsplit("/", 1)[-1]
        source = re.sub(r'href="https://github\.com/[^"]+"', f'href="{gh}"', source)
        source = re.sub(
            r'(github\.com/[^"]+" target="_blank" rel="noopener" style="color:rgba\(255,255,255,0\.85\); text-decoration:none;\">)[^<]+(</a>)',
            lambda m: m.group(1) + handle + m.group(2),
            source,
        )

    if contact.get("linkedin"):
        li = contact["linkedin"].rstrip("/") + "/"
        handle = li.rstrip("/").rsplit("/", 1)[-1]
        source = re.sub(r'href="https://www\.linkedin\.com/[^"]+"', f'href="{li}"', source)
        source = re.sub(
            r'(linkedin\.com/[^"]+" target="_blank" rel="noopener" style="color:rgba\(255,255,255,0\.85\); text-decoration:none;\">)[^<]+(</a>)',
            lambda m: m.group(1) + handle + m.group(2),
            source,
        )

    return source


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("html")
    ap.add_argument("-o", "--output", default=None)
    args = ap.parse_args()

    paragraphs = extract_paragraphs(args.docx)
    data = parse_resume(paragraphs)

    with open(args.html, "r", encoding="utf-8") as f:
        html = f.read()

    marker = '<script type="__bundler/template">'
    start = html.index(marker) + len(marker)
    end = html.index("</script>", start)
    json_blob = html[start:end].strip()
    # bundler escapes "</" as "<\u002F" to keep the JSON string safe inside <script>;
    # json.loads handles \u002F natively, so decode directly.
    source = json.loads(json_blob)

    source = replace_array_block(source, "skillGroups", js_array_literal("skillGroups", data["skillGroups"]))
    source = replace_array_block(source, "jobs", js_array_literal("jobs", data["jobs"]))
    source = replace_array_block(source, "honors", js_array_literal("honors", data["honors"]))
    source = replace_array_block(source, "education", js_array_literal("education", data["education"]))
    source = update_contact(source, {**data["contact"], "name": data["name"]})

    new_blob = json.dumps(source, ensure_ascii=False)
    # re-apply the </script>-safe escaping the bundler uses
    new_blob = new_blob.replace("</script", "<\\u002Fscript").replace("</SCRIPT", "<\\u002FSCRIPT")

    new_html = html[: html.index(marker) + len(marker)] + new_blob + html[end:]

    out_path = args.output or args.html
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"Updated {len(data['jobs'])} jobs, {len(data['skillGroups'])} skill groups, "
          f"{len(data['honors'])} honors, {len(data['education'])} education entries.")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
