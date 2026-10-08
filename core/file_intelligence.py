import os
from pathlib import Path
from typing import Optional, List, Dict, Any


class FileIntelligence:

    def __init__(self):

        self.home = Path.home()

        # ====================================================
        # COMMON WINDOWS LOCATIONS
        # ====================================================

        self.locations = {

            "home": self.home,

            "desktop": self.home / "Desktop",

            "downloads": self.home / "Downloads",

            "documents": self.home / "Documents",

            "pictures": self.home / "Pictures",

            "music": self.home / "Music",

            "videos": self.home / "Videos",

            "luna": (
                self.home
                / "Downloads"
                / "program"
                / "project"
                / "LUNA"
            ),
        }

        # ====================================================
        # DIRECTORIES WE SHOULD NOT SCAN
        # ====================================================

        self.ignored_directories = {

            ".git",
            ".cache",
            "__pycache__",

            "node_modules",

            ".vscode",
            ".idea",

            "AppData",

            "site-packages",

            "dist",
            "build",

            "Temp",
            "tmp",

            "$Recycle.Bin",

            "System Volume Information",

        }

    # ========================================================
    # RESOLVE LOCATION
    # ========================================================

    def resolve_location(
        self,
        location: Optional[str]
    ) -> Path:

        if not location:

            return self.locations["downloads"]

        value = (
            str(location)
            .strip()
            .lower()
        )

        aliases = {

            "home": "home",
            "computer": "home",
            "my computer": "home",

            "desktop": "desktop",
            "my desktop": "desktop",

            "downloads": "downloads",
            "download": "downloads",
            "my downloads": "downloads",

            "documents": "documents",
            "document": "documents",
            "my documents": "documents",

            "pictures": "pictures",
            "picture": "pictures",
            "photos": "pictures",
            "images": "pictures",

            "music": "music",

            "videos": "videos",
            "video": "videos",

            "luna": "luna",
            "luna project": "luna",
            "my luna project": "luna",
            "luna folder": "luna",
        }

        if value in aliases:

            return self.locations[
                aliases[value]
            ]

        # Direct Windows path
        expanded = os.path.expandvars(
            value
        )

        path = Path(
            expanded
        ).expanduser()

        if path.exists():

            return path

        # Relative to home
        home_path = (
            self.home / value
        )

        if home_path.exists():

            return home_path

        return path

    # ========================================================
    # FAST RECURSIVE WALK
    # ========================================================

    def _walk_fast(
        self,
        root: Path,
        max_depth: int = 8
    ):

        """
        Fast recursive traversal using os.scandir().

        Searches only within the supplied location.
        Known heavy/irrelevant directories are skipped.
        """

        if not root.exists():

            return

        if not root.is_dir():

            return

        stack = [
            (
                root,
                0
            )
        ]

        while stack:

            current, depth = stack.pop()

            if depth > max_depth:

                continue

            try:

                with os.scandir(
                    current
                ) as entries:

                    for entry in entries:

                        try:

                            if entry.is_dir(
                                follow_symlinks=False
                            ):

                                if (
                                    entry.name
                                    in self.ignored_directories
                                ):

                                    continue

                                stack.append(
                                    (
                                        Path(
                                            entry.path
                                        ),
                                        depth + 1
                                    )
                                )

                            elif entry.is_file(
                                follow_symlinks=False
                            ):

                                yield entry

                        except (
                            PermissionError,
                            OSError
                        ):

                            continue

            except (
                PermissionError,
                OSError
            ):

                continue

    # ========================================================
    # EXACT FILE SEARCH
    # ========================================================

    def find_exact(
        self,
        filename: str,
        location: str = "luna",
        limit: int = 10
    ) -> List[Dict[str, Any]]:

        if not filename:

            return []

        filename = (
            str(filename)
            .strip()
            .lower()
        )

        root = self.resolve_location(
            location
        )

        if not root.exists():

            return []

        # ----------------------------------------------------
        # Direct child first
        # ----------------------------------------------------

        direct = (
            root / filename
        )

        if direct.exists() and direct.is_file():

            return [
                self._file_info(
                    direct
                )
            ]

        results = []

        for entry in self._walk_fast(
            root,
            max_depth=10
        ):

            if len(results) >= limit:

                break

            try:

                if (
                    entry.name.lower()
                    == filename
                ):

                    results.append(
                        self._entry_info(
                            entry
                        )
                    )

            except (
                PermissionError,
                OSError
            ):

                continue

        return results

    # ========================================================
    # SEARCH FILES BY NAME
    # ========================================================

    def search_files(
        self,
        query: str,
        location: str = "luna",
        extension: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:

        if not query:

            return []

        query = (
            str(query)
            .strip()
            .lower()
        )

        if extension:

            extension = (
                extension
                .strip()
                .lower()
            )

            if not extension.startswith("."):

                extension = "." + extension

        root = self.resolve_location(
            location
        )

        if not root.exists():

            return []

        # ----------------------------------------------------
        # Search optimization:
        # exact direct filename gets priority
        # ----------------------------------------------------

        direct_matches = []

        try:

            with os.scandir(
                root
            ) as entries:

                for entry in entries:

                    try:

                        if not entry.is_file(
                            follow_symlinks=False
                        ):

                            continue

                        name_lower = (
                            entry.name.lower()
                        )

                        if query in name_lower:

                            if (
                                not extension
                                or
                                name_lower.endswith(
                                    extension
                                )
                            ):

                                direct_matches.append(
                                    self._entry_info(
                                        entry
                                    )
                                )

                                if (
                                    len(direct_matches)
                                    >= limit
                                ):

                                    return direct_matches

                    except (
                        PermissionError,
                        OSError
                    ):

                        continue

        except (
            PermissionError,
            OSError
        ):

            pass

        # ----------------------------------------------------
        # Recursive search
        # ----------------------------------------------------

        results = direct_matches

        if len(results) >= limit:

            return results[:limit]

        for entry in self._walk_fast(
            root,
            max_depth=10
        ):

            if len(results) >= limit:

                break

            try:

                # Avoid duplicate direct matches
                if any(
                    item["path"]
                    == entry.path
                    for item in results
                ):

                    continue

                name_lower = (
                    entry.name.lower()
                )

                if query not in name_lower:

                    continue

                if (
                    extension
                    and
                    not name_lower.endswith(
                        extension
                    )
                ):

                    continue

                results.append(
                    self._entry_info(
                        entry
                    )
                )

            except (
                PermissionError,
                OSError
            ):

                continue

        return results

    # ========================================================
    # SEARCH BY EXTENSION
    # ========================================================

    def search_by_extension(
        self,
        extension: str,
        location: str = "luna",
        limit: int = 20
    ) -> List[Dict[str, Any]]:

        if not extension:

            return []

        extension = (
            str(extension)
            .strip()
            .lower()
        )

        if not extension.startswith("."):

            extension = "." + extension

        root = self.resolve_location(
            location
        )

        if not root.exists():

            return []

        results = []

        for entry in self._walk_fast(
            root,
            max_depth=10
        ):

            if len(results) >= limit:

                break

            try:

                if (
                    entry.name
                    .lower()
                    .endswith(extension)
                ):

                    results.append(
                        self._entry_info(
                            entry
                        )
                    )

            except (
                PermissionError,
                OSError
            ):

                continue

        return results

    # ========================================================
    # LIST DIRECTORY
    # ========================================================

    def list_directory(
        self,
        location: str = "downloads",
        limit: int = 50
    ) -> Dict[str, Any]:

        root = self.resolve_location(
            location
        )

        if not root.exists():

            return {
                "success": False,
                "path": str(root),
                "files": [],
                "folders": [],
                "error": "Folder does not exist.",
            }

        if not root.is_dir():

            return {
                "success": False,
                "path": str(root),
                "files": [],
                "folders": [],
                "error": "Path is not a folder.",
            }

        files = []
        folders = []

        try:

            with os.scandir(
                root
            ) as entries:

                for entry in entries:

                    if (
                        len(files) + len(folders)
                        >= limit
                    ):

                        break

                    try:

                        if entry.is_dir(
                            follow_symlinks=False
                        ):

                            folders.append(
                                entry.name
                            )

                        elif entry.is_file(
                            follow_symlinks=False
                        ):

                            files.append(
                                entry.name
                            )

                    except (
                        PermissionError,
                        OSError
                    ):

                        continue

        except (
            PermissionError,
            OSError
        ):

            return {
                "success": False,
                "path": str(root),
                "files": [],
                "folders": [],
                "error": "Permission denied.",
            }

        return {
            "success": True,
            "path": str(root),
            "files": files,
            "folders": folders,
            "error": None,
        }

    # ========================================================
    # LATEST FILE
    # ========================================================

    def latest_file(
        self,
        location: str = "downloads",
        extension: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:

        root = self.resolve_location(
            location
        )

        if not root.exists():

            return None

        if not root.is_dir():

            return None

        if extension:

            extension = (
                extension
                .strip()
                .lower()
            )

            if not extension.startswith("."):

                extension = "." + extension

        latest_path = None
        latest_time = -1

        # Latest usually means latest in the selected
        # folder itself, so don't recursively scan everything.

        try:

            with os.scandir(
                root
            ) as entries:

                for entry in entries:

                    try:

                        if not entry.is_file(
                            follow_symlinks=False
                        ):

                            continue

                        if (
                            extension
                            and
                            not entry.name.lower().endswith(
                                extension
                            )
                        ):

                            continue

                        modified = (
                            entry.stat().st_mtime
                        )

                        if modified > latest_time:

                            latest_time = modified

                            latest_path = Path(
                                entry.path
                            )

                    except (
                        PermissionError,
                        OSError
                    ):

                        continue

        except (
            PermissionError,
            OSError
        ):

            return None

        if latest_path is None:

            return None

        return self._file_info(
            latest_path
        )

    # ========================================================
    # FILE INFORMATION
    # ========================================================

    def get_file_info(
        self,
        path: str
    ) -> Dict[str, Any]:

        file_path = Path(
            os.path.expandvars(
                str(path)
            )
        ).expanduser()

        return self._file_info(
            file_path
        )

    # ========================================================
    # INTERNAL PATH INFO
    # ========================================================

    def _file_info(
        self,
        path: Path
    ) -> Dict[str, Any]:

        try:

            stat = path.stat()

            return {

                "name": path.name,

                "path": str(path),

                "extension": path.suffix,

                "size_bytes": stat.st_size,

                "size_kb": round(
                    stat.st_size / 1024,
                    2
                ),

                "is_file": path.is_file(),

                "is_folder": path.is_dir(),

                "modified": stat.st_mtime,

            }

        except (
            PermissionError,
            OSError
        ):

            return {

                "name": path.name,

                "path": str(path),

                "extension": path.suffix,

                "size_bytes": None,

                "size_kb": None,

                "is_file": False,

                "is_folder": False,

                "modified": None,

            }

    # ========================================================
    # INTERNAL ENTRY INFO
    # ========================================================

    def _entry_info(
        self,
        entry
    ) -> Dict[str, Any]:

        try:

            stat = entry.stat(
                follow_symlinks=False
            )

            path = Path(
                entry.path
            )

            return {

                "name": entry.name,

                "path": entry.path,

                "extension": path.suffix,

                "size_bytes": stat.st_size,

                "size_kb": round(
                    stat.st_size / 1024,
                    2
                ),

                "is_file": True,

                "is_folder": False,

                "modified": stat.st_mtime,

            }

        except (
            PermissionError,
            OSError
        ):

            return {

                "name": entry.name,

                "path": entry.path,

                "extension": Path(
                    entry.name
                ).suffix,

                "size_bytes": None,

                "size_kb": None,

                "is_file": True,

                "is_folder": False,

                "modified": None,

            }

    # ========================================================
    # OPEN FILE
    # ========================================================

    def open_file(
        self,
        path: str
    ) -> str:

        file_path = Path(
            os.path.expandvars(
                str(path)
            )
        ).expanduser()

        if not file_path.exists():

            return (
                f"I couldn't find "
                f"{file_path}."
            )

        if not file_path.is_file():

            return (
                f"{file_path} is not a file."
            )

        try:

            os.startfile(
                str(file_path)
            )

            return (
                f"Opened "
                f"{file_path.name}."
            )

        except Exception as error:

            return (
                f"I couldn't open "
                f"{file_path.name}: {error}"
            )

    # ========================================================
    # OPEN FOLDER
    # ========================================================

    def open_folder(
        self,
        path: str
    ) -> str:

        folder_path = Path(
            os.path.expandvars(
                str(path)
            )
        ).expanduser()

        if not folder_path.exists():

            return (
                f"I couldn't find "
                f"{folder_path}."
            )

        if not folder_path.is_dir():

            return (
                f"{folder_path} is not a folder."
            )

        try:

            os.startfile(
                str(folder_path)
            )

            return (
                f"Opened "
                f"{folder_path.name}."
            )

        except Exception as error:

            return (
                f"I couldn't open "
                f"{folder_path.name}: {error}"
            )