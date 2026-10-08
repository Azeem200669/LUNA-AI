import re
from typing import Optional

from core.file_intelligence import FileIntelligence


class FileRouter:

    def __init__(self):

        self.files = FileIntelligence()

    # ========================================================
    # DETECT FILE REQUEST
    # ========================================================

    def is_file_request(
        self,
        text: str
    ) -> bool:

        if not text:

            return False

        value = (
            text
            .lower()
            .strip()
        )

        patterns = [

            # Search
            r"\bfind\b",

            r"\bsearch\b",

            r"\blocate\b",

            # Open
            r"\bopen\b",

            # List
            r"\blist\b",

            r"\bshow\b",

            r"\bwhat files\b",

            r"\bwhat's in\b",

            r"\bwhats in\b",

            # File types
            r"\bpython files?\b",

            r"\bpdf files?\b",

            r"\bword files?\b",

            r"\bexcel files?\b",

            r"\bpowerpoint files?\b",

            r"\btext files?\b",

            r"\bimage files?\b",

            # Latest
            r"\blatest\b",

            # Direct extensions
            r"\.(py|pdf|docx|xlsx|pptx|txt|png|jpg|jpeg|csv|zip|mp3|mp4|msi|exe)\b",

        ]

        for pattern in patterns:

            if re.search(
                pattern,
                value,
                re.IGNORECASE
            ):

                return True

        return False

    # ========================================================
    # DETECT LOCATION
    # ========================================================

    def detect_location(
        self,
        text: str
    ) -> str:

        value = (
            text
            .lower()
            .strip()
        )

        # ----------------------------------------------------
        # Explicit Downloads
        # ----------------------------------------------------

        if (
            "downloads" in value
            or
            "download folder" in value
            or
            "in downloads" in value
            or
            "inside downloads" in value
        ):

            return "downloads"

        # ----------------------------------------------------
        # Explicit Documents
        # ----------------------------------------------------

        if (
            "documents" in value
            or
            "document folder" in value
            or
            "in documents" in value
            or
            "inside documents" in value
        ):

            return "documents"

        # ----------------------------------------------------
        # Explicit Desktop
        # ----------------------------------------------------

        if (
            "desktop" in value
            or
            "desktop folder" in value
        ):

            return "desktop"

        # ----------------------------------------------------
        # Pictures
        # ----------------------------------------------------

        if (
            "pictures" in value
            or
            "photos" in value
            or
            "image folder" in value
        ):

            return "pictures"

        # ----------------------------------------------------
        # Music
        # ----------------------------------------------------

        if "music" in value:

            return "music"

        # ----------------------------------------------------
        # Videos
        # ----------------------------------------------------

        if "videos" in value:

            return "videos"

        # ----------------------------------------------------
        # Explicit LUNA project
        # ----------------------------------------------------

        if (
            "luna project" in value
            or
            "luna folder" in value
            or
            "my luna project" in value
            or
            "my luna folder" in value
        ):

            return "luna"

        # ----------------------------------------------------
        # Code-related requests default to LUNA
        # ----------------------------------------------------

        if re.search(
            r"\.(py|js|ts|html|css|json|yaml|yml|"
            r"java|cpp|c|h|jsx|tsx)\b",
            value,
            re.IGNORECASE
        ):

            return "luna"

        if (
            "python files" in value
            or
            "python file" in value
            or
            "code files" in value
            or
            "source files" in value
            or
            "project files" in value
        ):

            return "luna"

        # ----------------------------------------------------
        # General searches default to Downloads
        # ----------------------------------------------------

        return "downloads"

    # ========================================================
    # DETECT EXTENSION
    # ========================================================

    def detect_extension(
        self,
        text: str
    ) -> Optional[str]:

        value = (
            text
            .lower()
        )

        extension_map = {

            "python files": ".py",
            "python file": ".py",
            "python": ".py",

            "pdf files": ".pdf",
            "pdf file": ".pdf",
            "pdf": ".pdf",

            "word files": ".docx",
            "word file": ".docx",
            "word document": ".docx",
            "word": ".docx",

            "excel files": ".xlsx",
            "excel file": ".xlsx",
            "spreadsheet files": ".xlsx",
            "spreadsheet": ".xlsx",
            "excel": ".xlsx",

            "powerpoint files": ".pptx",
            "powerpoint file": ".pptx",
            "powerpoint": ".pptx",
            "ppt files": ".pptx",

            "text files": ".txt",
            "text file": ".txt",

            "image files": ".png",
            "image file": ".png",

            "csv files": ".csv",
            "csv file": ".csv",

            "zip files": ".zip",
            "zip file": ".zip",

            "mp3 files": ".mp3",
            "mp3 file": ".mp3",

            "mp4 files": ".mp4",
            "mp4 file": ".mp4",

            "msi files": ".msi",
            "msi file": ".msi",

            "exe files": ".exe",
            "exe file": ".exe",
        }

        # Longest phrases first
        for phrase in sorted(
            extension_map,
            key=len,
            reverse=True
        ):

            if phrase in value:

                return extension_map[
                    phrase
                ]

        # Direct extension
        match = re.search(
            r"\.([a-zA-Z0-9]{1,8})\b",
            text
        )

        if match:

            return (
                "."
                + match.group(1).lower()
            )

        return None

    # ========================================================
    # REMOVE LUNA PREFIX
    # ========================================================

    def clean_prefix(
        self,
        text: str
    ) -> str:

        value = text.strip()

        # IMPORTANT:
        # "Luna," is only a wake-name/prefix.
        # It must NEVER affect the search location.

        value = re.sub(
            r"^\s*luna\s*[,;:!-]?\s*",
            "",
            value,
            flags=re.IGNORECASE
        )

        return value.strip()

    # ========================================================
    # EXTRACT EXACT FILENAME
    # ========================================================

    def extract_filename(
        self,
        text: str
    ) -> Optional[str]:

        value = self.clean_prefix(
            text
        )

        # ----------------------------------------------------
        # Quoted filename
        # ----------------------------------------------------

        match = re.search(
            r'["\']([^"\']+\.[A-Za-z0-9]{1,8})["\']',
            value
        )

        if match:

            return (
                match.group(1)
                .strip()
            )

        # ----------------------------------------------------
        # Filename after command word
        # ----------------------------------------------------

        extensions = (
            r"py|pdf|docx|xlsx|pptx|txt|"
            r"png|jpg|jpeg|csv|zip|mp3|"
            r"mp4|msi|exe|json|js|ts|html|css"
        )

        match = re.search(
            rf"\b(?:find|open|search|locate)\b"
            rf".*?"
            rf"([\w\-. ()']+\.({extensions}))"
            rf"\b",
            value,
            re.IGNORECASE
        )

        if match:

            return (
                match.group(1)
                .strip()
                .strip(".,!?;:")
            )

        # ----------------------------------------------------
        # Filename anywhere
        # ----------------------------------------------------

        match = re.search(
            rf"(?<![\w.-])"
            rf"([\w\-. ()']+\.({extensions}))"
            rf"(?![\w])",
            value,
            re.IGNORECASE
        )

        if match:

            return (
                match.group(1)
                .strip()
                .strip(".,!?;:")
            )

        return None

    # ========================================================
    # DETECT LANGUAGE
    # ========================================================

    def detect_language(
        self,
        text: str
    ) -> str:

        if re.search(
            r"[\u0C00-\u0C7F]",
            text
        ):

            return "te"

        if re.search(
            r"[\u0900-\u097F]",
            text
        ):

            return "hi"

        if re.search(
            r"[\u0B80-\u0BFF]",
            text
        ):

            return "ta"

        if re.search(
            r"[\u0C80-\u0CFF]",
            text
        ):

            return "kn"

        if re.search(
            r"[\u0D00-\u0D7F]",
            text
        ):

            return "ml"

        if re.search(
            r"[\u0980-\u09FF]",
            text
        ):

            return "bn"

        if re.search(
            r"[\u0A80-\u0AFF]",
            text
        ):

            return "gu"

        if re.search(
            r"[\u0A00-\u0A7F]",
            text
        ):

            return "pa"

        if re.search(
            r"[\u0600-\u06FF]",
            text
        ):

            return "ur"

        return "en"

    # ========================================================
    # HANDLE REQUEST
    # ========================================================

    def handle(
        self,
        text: str
    ) -> dict:

        if not self.is_file_request(
            text
        ):

            return {
                "handled": False,
                "success": False,
                "operation": None,
                "answer": "",
                "results": [],
                "language": "en",
                "error": None,
            }

        language = self.detect_language(
            text
        )

        clean_text = self.clean_prefix(
            text
        )

        lower = clean_text.lower()

        location = self.detect_location(
            clean_text
        )

        extension = self.detect_extension(
            clean_text
        )

        filename = self.extract_filename(
            clean_text
        )

        print()
        print(
            "[FILE ROUTER]"
        )

        print(
            "Text:",
            text
        )

        print(
            "Clean:",
            clean_text
        )

        print(
            "Location:",
            location
        )

        print(
            "Extension:",
            extension
        )

        print(
            "Filename:",
            filename
        )

        # ====================================================
        # 1. EXACT FILE SEARCH
        # ====================================================

        if (
            filename
            and
            (
                lower.startswith("find ")
                or
                lower.startswith("search ")
                or
                lower.startswith("locate ")
            )
        ):

            results = (
                self.files.find_exact(
                    filename,
                    location=location,
                    limit=10
                )
            )

            # If code file wasn't found in LUNA,
            # do a fast Downloads fallback.
            if (
                not results
                and
                location == "luna"
            ):

                results = (
                    self.files.find_exact(
                        filename,
                        location="downloads",
                        limit=10
                    )
                )

            if results:

                answer = (
                    f"I found {filename}."
                )

            else:

                answer = (
                    f"I couldn't find "
                    f"{filename}."
                )

            return {
                "handled": True,
                "success": bool(results),
                "operation": "find_file",
                "answer": answer,
                "results": results,
                "language": language,
                "error": (
                    None
                    if results
                    else "File not found."
                ),
            }

        # ====================================================
        # 2. OPEN EXACT FILE
        # ====================================================

        open_request = (
            lower.startswith("open ")
            or
            " open " in lower
        )

        if (
            filename
            and
            open_request
        ):

            results = (
                self.files.find_exact(
                    filename,
                    location=location,
                    limit=10
                )
            )

            if (
                not results
                and
                location != "downloads"
            ):

                results = (
                    self.files.find_exact(
                        filename,
                        location="downloads",
                        limit=10
                    )
                )

            if not results:

                return {
                    "handled": True,
                    "success": False,
                    "operation": "open_file",
                    "answer": (
                        f"I couldn't find "
                        f"{filename}."
                    ),
                    "results": [],
                    "language": language,
                    "error": "File not found.",
                }

            selected = results[0]

            open_result = (
                self.files.open_file(
                    selected["path"]
                )
            )

            return {
                "handled": True,
                "success": True,
                "operation": "open_file",
                "answer": open_result,
                "results": results,
                "language": language,
                "error": None,
            }

        # ====================================================
        # 3. LATEST FILE
        # ====================================================

        if "latest" in lower:

            latest = (
                self.files.latest_file(
                    location,
                    extension=extension
                )
            )

            if not latest:

                return {
                    "handled": True,
                    "success": False,
                    "operation": "latest_file",
                    "answer": (
                        "I couldn't find "
                        "the requested file."
                    ),
                    "results": [],
                    "language": language,
                    "error": "No file found.",
                }

            if open_request:

                open_result = (
                    self.files.open_file(
                        latest["path"]
                    )
                )

                return {
                    "handled": True,
                    "success": True,
                    "operation": "open_latest_file",
                    "answer": open_result,
                    "results": [latest],
                    "language": language,
                    "error": None,
                }

            return {
                "handled": True,
                "success": True,
                "operation": "latest_file",
                "answer": (
                    f"The latest file is "
                    f"{latest['name']}."
                ),
                "results": [latest],
                "language": language,
                "error": None,
            }

        # ====================================================
        # 4. EXTENSION SEARCH
        # ====================================================

        extension_search = (

            "python files" in lower
            or
            "python file" in lower

            or
            "pdf files" in lower
            or
            "pdf file" in lower

            or
            "word files" in lower
            or
            "word file" in lower

            or
            "excel files" in lower
            or
            "excel file" in lower

            or
            "powerpoint files" in lower
            or
            "powerpoint file" in lower

            or
            "text files" in lower
            or
            "text file" in lower

            or
            "image files" in lower
            or
            "image file" in lower
        )

        if (
            extension
            and
            extension_search
        ):

            results = (
                self.files.search_by_extension(
                    extension,
                    location=location,
                    limit=20
                )
            )

            answer = self._format_results(
                results,
                extension
            )

            return {
                "handled": True,
                "success": bool(results),
                "operation": "search_extension",
                "answer": answer,
                "results": results,
                "language": language,
                "error": (
                    None
                    if results
                    else "No matching files found."
                ),
            }

        # ====================================================
        # 5. DIRECTORY LISTING
        # ====================================================

        list_request = (

            "list files" in lower

            or
            "show files" in lower

            or
            "show me the files" in lower

            or
            "show me files" in lower

            or
            "show folder" in lower

            or
            "show contents" in lower

            or
            "what files" in lower

            or
            "what's in" in lower

            or
            "whats in" in lower

            or
            bool(
                re.search(
                    r"\bfiles?\b.*\bin\b.*"
                    r"(downloads?|documents?|desktop|"
                    r"pictures?|music|videos?|"
                    r"luna project|luna folder)",
                    lower
                )
            )
        )

        if list_request:

            result = (
                self.files.list_directory(
                    location,
                    limit=50
                )
            )

            if not result["success"]:

                return {
                    "handled": True,
                    "success": False,
                    "operation": "list_directory",
                    "answer": result["error"],
                    "results": [],
                    "language": language,
                    "error": result["error"],
                }

            return {
                "handled": True,
                "success": True,
                "operation": "list_directory",
                "answer": self._format_directory(
                    result
                ),
                "results": [],
                "language": language,
                "error": None,
            }

        # ====================================================
        # 6. GENERIC SEARCH
        # ====================================================

        query = self._extract_search_query(
            clean_text
        )

        if query:

            results = (
                self.files.search_files(
                    query,
                    location=location,
                    limit=20
                )
            )

            return {
                "handled": True,
                "success": bool(results),
                "operation": "search_files",
                "answer": self._format_results(
                    results
                ),
                "results": results,
                "language": language,
                "error": (
                    None
                    if results
                    else "No files found."
                ),
            }

        # ====================================================
        # UNKNOWN
        # ====================================================

        return {
            "handled": True,
            "success": False,
            "operation": None,
            "answer": (
                "I couldn't determine "
                "the file operation."
            ),
            "results": [],
            "language": language,
            "error": "Unknown file request.",
        }

    # ========================================================
    # GENERIC SEARCH QUERY
    # ========================================================

    def _extract_search_query(
        self,
        text: str
    ) -> Optional[str]:

        value = self.clean_prefix(
            text
        )

        # ----------------------------------------------------
        # files containing X
        # ----------------------------------------------------

        match = re.search(
            r"\b(?:find|search|locate)\b"
            r".*?\bfiles?\b"
            r"\s+(?:containing|named|called|matching)\s+"
            r"(.+)",
            value,
            re.IGNORECASE
        )

        if match:

            query = (
                match.group(1)
                .strip()
            )

            query = re.sub(
                r"\b(?:in|inside|within)\s+"
                r"(?:my\s+)?"
                r"(downloads?|documents?|desktop|"
                r"pictures?|videos?|music|"
                r"luna project|luna folder)\b",
                "",
                query,
                flags=re.IGNORECASE
            )

            query = query.strip(
                " .,!?"
            )

            return query or None

        # ----------------------------------------------------
        # find X
        # ----------------------------------------------------

        match = re.search(
            r"\b(?:find|search|locate)\b"
            r"\s+(?:my\s+)?(.+)",
            value,
            re.IGNORECASE
        )

        if match:

            query = (
                match.group(1)
                .strip()
            )

            query = re.sub(
                r"\b(?:in|inside|within)\s+"
                r"(?:my\s+)?"
                r"(downloads?|documents?|desktop|"
                r"pictures?|videos?|music|"
                r"luna project|luna folder)\b",
                "",
                query,
                flags=re.IGNORECASE
            )

            query = re.sub(
                r"\b(?:my\s+)?files?\b",
                "",
                query,
                flags=re.IGNORECASE
            )

            query = query.strip(
                " .,!?"
            )

            if query:

                return query

        return None

    # ========================================================
    # FORMAT DIRECTORY
    # ========================================================

    def _format_directory(
        self,
        result: dict
    ) -> str:

        files = result.get(
            "files",
            []
        )

        folders = result.get(
            "folders",
            []
        )

        parts = [

            f"I found {len(files)} files "
            f"and {len(folders)} folders."
        ]

        if files:

            parts.append(
                "Files: "
                + ", ".join(
                    files[:10]
                )
            )

        if folders:

            parts.append(
                "Folders: "
                + ", ".join(
                    folders[:10]
                )
            )

        return " ".join(
            parts
        )

    # ========================================================
    # FORMAT RESULTS
    # ========================================================

    def _format_results(
        self,
        results,
        extension=None
    ):

        if not results:

            if extension:

                return (
                    f"I couldn't find any "
                    f"{extension} files."
                )

            return (
                "I couldn't find any matching files."
            )

        if extension:

            prefix = (
                f"I found {len(results)} "
                f"{extension} files."
            )

        else:

            prefix = (
                f"I found {len(results)} "
                f"matching files."
            )

        names = [
            item["name"]
            for item in results[:10]
        ]

        return (
            prefix
            + " "
            + ", ".join(
                names
            )
        )