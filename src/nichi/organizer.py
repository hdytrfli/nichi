"""
File organizer module
Handles grouping and organizing MP4 and subtitle files into folders
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional


class FileOrganizer:
    """Organizes MP4 files with their corresponding subtitle files into folders"""

    def __init__(self):
        self.processed_files = []

    def find_video_files(self, directory_path: str) -> List[str]:
        """
        Find all MP4 files in the specified directory

        Parameters:
            directory_path: Path to search for MP4 files

        Returns:
            List of MP4 filenames
        """
        return [
            filename
            for filename in os.listdir(directory_path)
            if filename.lower().endswith(".mp4")
        ]

    def find_subtitle_files(self, directory_path: str) -> List[str]:
        """
        Find all subtitle files in the specified directory

        Parameters:
            directory_path: Path to search for subtitle files

        Returns:
            List of subtitle filenames (.srt and .en.srt)
        """
        return [
            filename
            for filename in os.listdir(directory_path)
            if filename.lower().endswith((".srt", ".en.srt"))
        ]

    def extract_base_name(self, filename: str) -> str:
        """
        Extract base name from filename, handling .en.srt extension

        Parameters:
            filename: The filename to extract base name from

        Returns:
            Base name without extension
        """
        if filename.lower().endswith(".en.srt"):
            return filename[:-7]
        else:
            return os.path.splitext(filename)[0]

    def match_subtitle_to_video(
        self, video_filename: str, subtitle_files: List[str]
    ) -> Optional[str]:
        """
        Find matching subtitle file for a video file

        Parameters:
            video_filename: Name of the video file
            subtitle_files: List of available subtitle files

        Returns:
            Matching subtitle filename or None if not found
        """
        video_base_name = os.path.splitext(video_filename)[0]

        for subtitle_file in subtitle_files:
            subtitle_base_name = self.extract_base_name(subtitle_file)
            if subtitle_base_name == video_base_name:
                return subtitle_file

        return None

    def group_files(self, directory_path: str) -> Dict[str, Optional[str]]:
        """
        Group MP4 files with their matching subtitle files

        Parameters:
            directory_path: Directory path to scan for files

        Returns:
            Dictionary mapping MP4 filenames to their matching subtitle files (or None)
        """
        video_files = self.find_video_files(directory_path)
        subtitle_files = self.find_subtitle_files(directory_path)

        file_pairs = {}

        for video_file in video_files:
            matching_subtitle = self.match_subtitle_to_video(video_file, subtitle_files)
            file_pairs[video_file] = matching_subtitle

        used_subtitles = set(
            subtitle for subtitle in file_pairs.values() if subtitle is not None
        )

        for subtitle_file in subtitle_files:
            if subtitle_file not in used_subtitles:
                subtitle_base_name = self.extract_base_name(subtitle_file)
                placeholder_video = f"{subtitle_base_name}.mp4"

                if placeholder_video not in file_pairs:
                    file_pairs[placeholder_video] = subtitle_file

        return file_pairs

    def create_folder_structure(
        self, directory_path: str, file_pairs: Dict[str, Optional[str]]
    ) -> List[str]:
        """
        Create folder structure and move files into appropriate folders

        Parameters:
            directory_path: Base directory path
            file_pairs: Dictionary mapping video files to subtitle files

        Returns:
            List of created folder names
        """
        created_folders = []

        for video_filename, subtitle_filename in file_pairs.items():
            folder_base_name = os.path.splitext(video_filename)[0]
            folder_path = os.path.join(directory_path, folder_base_name)

            Path(folder_path).mkdir(exist_ok=True)
            created_folders.append(folder_base_name)

            video_source_path = os.path.join(directory_path, video_filename)
            if os.path.exists(video_source_path):
                video_destination_path = os.path.join(folder_path, video_filename)
                shutil.move(video_source_path, video_destination_path)
                self.processed_files.append(f"Moved video: {video_filename}")

            if subtitle_filename:
                subtitle_source_path = os.path.join(directory_path, subtitle_filename)
                if os.path.exists(subtitle_source_path):
                    subtitle_destination_path = os.path.join(
                        folder_path, subtitle_filename
                    )
                    shutil.move(subtitle_source_path, subtitle_destination_path)
                    self.processed_files.append(f"Moved subtitle: {subtitle_filename}")

        return created_folders

    def organize_directory(self, directory_path: str) -> Dict[str, List[str]]:
        """
        Complete organization process for a directory

        Parameters:
            directory_path: Directory to organize

        Returns:
            Dictionary containing organization results
        """
        self.processed_files = []

        file_pairs = self.group_files(directory_path)
        created_folders = self.create_folder_structure(directory_path, file_pairs)

        return {
            "file_pairs": list(file_pairs.keys()),
            "created_folders": created_folders,
            "processed_files": self.processed_files,
        }
