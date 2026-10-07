from core.file_intelligence import FileIntelligence


files = FileIntelligence()


print()
print("=" * 80)
print("          🌙 LUNA FILE INTELLIGENCE TEST")
print("=" * 80)


# ============================================================
# TEST 1 - LIST DOWNLOADS
# ============================================================

print()
print("=" * 80)
print("TEST 1: List Downloads")
print("=" * 80)

result = files.list_directory(
    "downloads",
    limit=20
)

if result["success"]:

    print(
        "PATH:",
        result["path"]
    )

    print()
    print("FOLDERS:")

    for folder in result["folders"]:

        print(
            f"📁 {folder}"
        )

    print()
    print("FILES:")

    for file in result["files"]:

        print(
            f"📄 {file}"
        )

else:

    print(
        "❌",
        result["error"]
    )


# ============================================================
# TEST 2 - SEARCH PYTHON FILES
# ============================================================

print()
print("=" * 80)
print("TEST 2: Search Python files in LUNA")
print("=" * 80)

results = files.search_by_extension(
    ".py",
    location="luna",
    limit=20
)

if results:

    for item in results:

        print(
            f"🐍 {item['name']}"
        )

        print(
            f"   {item['path']}"
        )

else:

    print(
        "No Python files found."
    )


# ============================================================
# TEST 3 - SEARCH FILE NAME
# ============================================================

print()
print("=" * 80)
print("TEST 3: Search for agent.py")
print("=" * 80)

results = files.find_exact(
    "agent.py",
    location="luna",
    limit=10
)

if results:

    for item in results:

        print(
            f"✅ Found: {item['path']}"
        )

else:

    print(
        "agent.py not found."
    )


# ============================================================
# TEST 4 - SEARCH PROJECT FILES
# ============================================================

print()
print("=" * 80)
print("TEST 4: Search for 'voice'")
print("=" * 80)

results = files.search_files(
    "voice",
    location="luna",
    limit=20
)

if results:

    for item in results:

        print(
            f"🎙️ {item['name']}"
        )

        print(
            f"   {item['path']}"
        )

else:

    print(
        "No matching files found."
    )


# ============================================================
# TEST 5 - LATEST DOWNLOAD
# ============================================================

print()
print("=" * 80)
print("TEST 5: Latest file in Downloads")
print("=" * 80)

latest = files.latest_file(
    "downloads"
)

if latest:

    print(
        "Name:",
        latest["name"]
    )

    print(
        "Path:",
        latest["path"]
    )

    print(
        "Size:",
        latest["size_kb"],
        "KB"
    )

else:

    print(
        "No files found."
    )


# ============================================================
# TEST 6 - OPEN LUNA FOLDER
# ============================================================

print()
print("=" * 80)
print("TEST 6: Open LUNA project folder")
print("=" * 80)

luna_path = (
    files.locations["luna"]
)

if luna_path.exists():

    print(
        files.open_folder(
            str(luna_path)
        )
    )

else:

    print(
        "❌ LUNA project folder was not found:"
    )

    print(
        luna_path
    )


print()
print("=" * 80)
print("             ✅ FILE TEST COMPLETE")
print("=" * 80)