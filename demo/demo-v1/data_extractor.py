#!/usr/bin/env python3
"""
Data Extractor Script for ArchPal Student Data

This script processes student conversation data from two folders and creates a master CSV
containing student names and unique identifiers extracted from the data files.

Usage:
    python data_extractor.py <folder1_path> <folder2_path> [output_file.csv]

Arguments:
    folder1_path: Path to first folder containing student data
    folder2_path: Path to second folder containing student data
    output_file: Optional output CSV filename (default: master_student_list.csv)
"""

import csv
import os
import sys
import re
from pathlib import Path


def extract_student_info_from_filename(filename):
    """
    Extract student first name, last name, and session number from filename.

    Expected format: LastName_FirstName_SessionN.csv
    Returns: (first_name, last_name, session_number) or None if parsing fails
    """
    # Match pattern: LastName_FirstName_Session followed by digits
    pattern = r'^([^_]+)_([^_]+)_Session(\d+)\.csv$'
    match = re.match(pattern, filename)

    if match:
        last_name = match.group(1)
        first_name = match.group(2)
        session_number = int(match.group(3))
        return first_name, last_name, session_number

    return None


def extract_unique_id_from_csv(csv_path):
    """
    Extract the unique identifier from the second row of a CSV file.

    Returns: unique_id string or None if extraction fails
    """
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)

            # Check if we have at least a header + one data row
            if len(rows) < 2:
                print(f"Warning: {csv_path} has insufficient rows")
                return None

            # Second row (index 1), first column should contain unique ID
            unique_id = rows[1][0].strip()
            return unique_id if unique_id else None

    except Exception as e:
        print(f"Error reading {csv_path}: {e}")
        return None


def process_folder(folder_path):
    """
    Process all CSV files in a folder and extract student information.

    Returns: List of dictionaries with student data
    """
    student_data = []

    if not os.path.exists(folder_path):
        print(f"Warning: Folder {folder_path} does not exist")
        return student_data

    # Find all CSV files in the folder
    csv_files = list(Path(folder_path).glob("*.csv"))

    print(f"Found {len(csv_files)} CSV files in {folder_path}")

    for csv_file in csv_files:
        filename = csv_file.name

        # Extract student info from filename
        student_info = extract_student_info_from_filename(filename)

        if not student_info:
            print(f"Warning: Could not parse filename {filename}")
            continue

        first_name, last_name, session_number = student_info

        # Extract unique ID from CSV content
        unique_id = extract_unique_id_from_csv(str(csv_file))

        if not unique_id:
            print(f"Warning: Could not extract unique ID from {filename}")
            continue

        student_data.append({
            'first_name': first_name,
            'last_name': last_name,
            'unique_id': unique_id,
            'session_number': session_number
        })

    return student_data


def create_master_csv(folder1_path, folder2_path, output_file='master_student_list.csv'):
    """
    Process two folders and create a master CSV with all student data.
    """
    print("Processing student data folders...")

    # Process both folders
    folder1_data = process_folder(folder1_path)
    folder2_data = process_folder(folder2_path)

    # Combine all data
    all_student_data = folder1_data + folder2_data

    if not all_student_data:
        print("No valid student data found in the specified folders.")
        return

    print(f"Extracted data for {len(all_student_data)} students")

    # Keep all entries (including duplicates by unique_id)
    final_student_data = all_student_data
    print(f"Final dataset contains {len(final_student_data)} total entries")

    # Write to CSV
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['first_name', 'last_name', 'unique_id', 'session_number']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header
            writer.writeheader()

            # Sort by last name, then first name
            final_student_data.sort(key=lambda x: (x['last_name'], x['first_name']))

            # Write data rows
            for student in final_student_data:
                writer.writerow(student)

        print(f"Master student list created: {output_file}")
        print(f"Total students processed: {len(final_student_data)}")

    except Exception as e:
        print(f"Error writing output file: {e}")


def main():
    """Main function to handle command line arguments and run the script."""
    if len(sys.argv) < 3:
        print("Usage: python data_extractor.py <folder1_path> <folder2_path> [output_file.csv]")
        print("Example: python data_extractor.py ./data/folder1 ./data/folder2 master_list.csv")
        sys.exit(1)

    folder1_path = sys.argv[1]
    folder2_path = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else 'master_student_list.csv'

    # Validate folder paths
    if not os.path.isdir(folder1_path):
        print(f"Error: {folder1_path} is not a valid directory")
        sys.exit(1)

    if not os.path.isdir(folder2_path):
        print(f"Error: {folder2_path} is not a valid directory")
        sys.exit(1)

    # Process the data
    create_master_csv(folder1_path, folder2_path, output_file)


if __name__ == "__main__":
    main()
