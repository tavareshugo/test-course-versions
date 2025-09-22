#!/usr/bin/env python3
"""
Post-render script to inject version dropdown and archive versions into Quarto-generated HTML files.
Designed for Cambridge Informatics Training course materials with versioning.
"""

import re
import glob
from pathlib import Path
from datetime import datetime
import sys


def get_available_versions():
    """
    Scan the _site directory for available versions.
    Returns a list of versions in YYYY.MM.DD format, sorted newest first.
    """
    versions = []
    archive_path = Path("_site/archive")

    if archive_path.exists():
        for item in archive_path.iterdir():
            if item.is_dir():
                # Validate YYYY.MM.DD format
                if re.match(r"^\d{4}\.\d{2}\.\d{2}$", item.name):
                    versions.append(item.name)

    # Sort versions in reverse chronological order (newest first)
    versions.sort(reverse=True)
    return versions


def generate_dropdown_html(versions, prefix, current_version=None):
    """
    Generate the HTML for the version dropdown.
    If current_version is provided (e.g. 'Latest' or '2025.01.15'),
    a small badge showing the current version will be appended to the label.
    """
    display_versions = versions[:3] if versions else []
    has_more = len(versions) > 3

    # Prepare badge HTML (small, aria-hidden so screen-readers read the menu label itself)
    badge_html = ""
    if current_version:
        # escape current_version if necessary (here it's safe)
        badge_html = (
            f' <span class="version-badge" aria-hidden="true">{current_version}</span>'
        )

    dropdown_html = f"""
  <li id="version-dropdown" class="nav-item dropdown">
    <a class="nav-link dropdown-toggle" href="#" id="nav-menu-versions" role="link" data-bs-toggle="dropdown" aria-expanded="false">
      <span class="menu-text">Version:</span>{badge_html}
    </a>
    <ul class="dropdown-menu" aria-labelledby="nav-menu-versions">
      <li>
        <a class="dropdown-item" href="/{prefix}/index.html">
          <span class="dropdown-text">Latest</span>
        </a>
      </li>"""

    for version in display_versions:
        dropdown_html += f"""
      <li>
        <a class="dropdown-item" href="/{prefix}/archive/{version}/index.html">
          <span class="dropdown-text">{version}</span>
        </a>
      </li>"""

    if has_more:
        dropdown_html += f"""
      <li><hr class="dropdown-divider"></li>
      <li>
        <a class="dropdown-item" href="/{prefix}/versions.html">
          <span class="dropdown-text">More versions...</span>
        </a>
      </li>"""

    dropdown_html += """
    </ul>
  </li>"""

    return dropdown_html


def detect_current_version_from_path(file_path):
    """
    Return 'Latest' or 'YYYY.MM.DD' based on the file path.
    """
    p = Path(file_path).as_posix()
    m = re.search(r"/archive/(\d{4}\.\d{2}\.\d{2})(?:/|$)", p)
    if m:
        return m.group(1)
    return "Latest"


def generate_archive_versions_html(versions, prefix):
    """
    Generate HTML for archive versions to be injected into versions.html files.

    Args:
        versions: List of available versions

    Returns:
        HTML string for archive versions
    """
    if not versions:
        return ""

    archive_html = ""

    for version in versions:
        try:
            # Parse date for better display
            date_obj = datetime.strptime(version, "%Y.%m.%d")
            formatted_date = date_obj.strftime("%B %d, %Y")
        except ValueError:
            formatted_date = version

        archive_html += f"""

<div class="list-group-item list-group-item-action">
<div class="d-flex w-100 justify-content-between">
<h5 class="mb-1 anchored">Version {version}</h5>
<p><small class="text-muted">{formatted_date}</small></p>
</div>
<p><a href="/{prefix}/archive/{version}/index.html">View Version {version}</a></p>
</div>"""

    return archive_html


def inject_dropdown_into_html(file_path, dropdown_html):
    """
    Inject the provided dropdown_html immediately before the closing </nav> tag.
    Raises an exception if </nav> is not found.

    Returns True on success.
    """
    # Add some CSS to remove bullet points from the dropdown list
    marker_css = """
    <style>
    #version-dropdown {
      list-style: none;
    }
    </style>
    """
    dropdown_html = marker_css + "\n" + dropdown_html

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Remove any existing version dropdown
        content = re.sub(
            r'<li id="version-dropdown" class="nav-item dropdown">.*?</ul>\s*</li>',
            "",
            content,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Inject directly before the last </nav>
        if "</nav>" in content:
            content = content.replace("</nav>", dropdown_html + "\n</nav>", 1)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        else:
            raise RuntimeError(f"⚠ Could not find closing </nav> tag in: {file_path}")

    except Exception as e:
        print(f"✗ Error updating {file_path}: {e}")
        return False


def inject_archive_versions_into_versions_html(file_path, archive_html):
    """
    Inject archive versions HTML into versions.html files.
    Looks for the closing </div> of the list-group and inserts before it.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Remove any existing archive versions (everything after the "Latest Version" item)
        # Look for the pattern: Latest Version item followed by archive versions
        latest_pattern = r'(<div class="list-group-item list-group-item-action">.*?<p><a href="[./]*">View Latest Version</a></p>\s*</div>).*?(?=</div>\s*</div>)'

        if re.search(latest_pattern, content, re.DOTALL):
            # Replace with just the Latest Version item plus our new archive versions
            content = re.sub(
                latest_pattern, r"\1" + archive_html, content, flags=re.DOTALL
            )

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return True
        else:
            print(f"⚠ Could not find versions pattern in: {file_path}")
            return False

    except Exception as e:
        print(f"✗ Error updating versions in {file_path}: {e}")
        return False


def inject_deprecation_warning(file_path, prefix):
    """
    Inject a deprecation warning banner at the top of the HTML file.
    """
    warning_html = f"""
<div id="deprecation-warning" class="callout callout-style-default callout-warning callout-titled">
<div class="callout-header d-flex align-content-center">
<div class="callout-icon-container">
<i class="callout-icon"></i>
</div>
<div class="callout-title-container flex-fill">
Warning
</div>
</div>
<div class="callout-body-container callout-body">
<p><font size="+2">This is an archived version of the course - please consider using the <a href="/{prefix}/index.html">latest version</a>.</font></p>
</div>
</div>
"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Skip if warning already present
        if 'id="deprecation-warning"' in content:
            return True

        # Inject warning right after the main content tag
        content = re.sub(
            r"(<main class=\"content\" id=\"quarto-document-content\">)",
            r"\1" + warning_html,
            content,
            count=1,
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"✗ Error injecting warning in {file_path}: {e}")
        return False


def main():
    """
    Main function to update all HTML files with version dropdowns and archive versions.
    """

    # read user input prefix
    if len(sys.argv) > 1:
        prefix = sys.argv[1]
    else:
        print("❗ Error: No prefix argument provided.")
        sys.exit(1)

    print("🔄 Post-render: Starting dropdown injection and versions update...")

    # Get available versions
    versions = get_available_versions()
    print(f"📁 Found {len(versions)} archived versions: {versions}")

    # Generate dropdown HTML
    dropdown_html = generate_dropdown_html(versions, prefix)

    # Generate archive versions HTML
    archive_html = generate_archive_versions_html(versions, prefix)

    # Find all HTML files to update
    html_files = glob.glob("_site/**/*.html", recursive=True)

    # Update dropdowns in all HTML files
    dropdown_success_count = 0
    versions_success_count = 0

    for html_file in html_files:
        current_version = detect_current_version_from_path(html_file)
        dropdown_html = generate_dropdown_html(
            versions, prefix, current_version=current_version
        )

        if inject_dropdown_into_html(html_file, dropdown_html):
            dropdown_success_count += 1

        if html_file.endswith("versions.html"):
            if inject_archive_versions_into_versions_html(html_file, archive_html):
                versions_success_count += 1
                print(f"✓ Updated archive versions in: {html_file}")

    # find all archive HTML files to update with warning
    archive_html_files = glob.glob("_site/archive/**/*.html", recursive=True)
    warning_successs_count = 0

    for archive_file in archive_html_files:
        if inject_deprecation_warning(archive_file, prefix):
            warning_successs_count += 1

    print(
        f"🎉 Successfully updated {dropdown_success_count}/{len(html_files)} HTML files with version dropdown!"
    )
    print(
        f"🎉 Successfully updated {versions_success_count} versions.html files with archive versions!"
    )
    print(
        f"🎉 Successfully updated {warning_successs_count}/{len(archive_html_files)} archive HTML files with deprecation warning!"
    )


if __name__ == "__main__":
    main()
