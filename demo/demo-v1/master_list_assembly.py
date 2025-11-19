#!/usr/bin/env python3
"""
Master List Assembly Script for ArchPal Student Data

This script takes an original master list CSV file and appends all single row
identifier CSV files from a specified folder path.

Usage:
    python master_list_assembly.py <master_list_file> <identifier_folder_path> [output_file.csv]

Arguments:
    master_list_file: Path to the original master list CSV file
    identifier_folder_path: Path to folder containing single row identifier CSV files
    output_file: Optional output CSV filename (default: master_list_updated.csv)
"""

import csv
import os
import sys
from pathlib import Path


def read_master_list(master_list_path):
    """
    Read the original master list CSV file.

    Returns: List of dictionaries with student data
    """
    student_data = []

    if not os.path.exists(master_list_path):
        print(f"Warning: Master list file {master_list_path} does not exist")
        return student_data

    try:
        with open(master_list_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                student_data.append(row)
        print(f"Read {len(student_data)} entries from master list")
    except Exception as e:
        print(f"Error reading master list file: {e}")
        return []

    return student_data


def read_identifier_csv(csv_path):
    """
    Read a single row identifier CSV file.

    Expected columns: first_name, last_name, unique_id
    Returns: Dictionary with student data or None if reading fails
    """
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

            if len(rows) == 0:
                print(f"Warning: {csv_path} has no data rows")
                return None

            if len(rows) > 1:
                print(f"Warning: {csv_path} has multiple rows, using first row only")

            row = rows[0]

            required_fields = ['first_name', 'last_name', 'unique_id']
            if not all(field in row for field in required_fields):
                print(f"Warning: {csv_path} missing required fields")
                return None

            return {
                'first_name': row['first_name'].strip(),
                'last_name': row['last_name'].strip(),
                'unique_id': row['unique_id'].strip()
            }

    except Exception as e:
        print(f"Error reading {csv_path}: {e}")
        return None


def process_identifier_folder(folder_path):
    """
    Process all CSV files in the identifier folder.

    Returns: List of dictionaries with student data
    """
    student_data = []

    if not os.path.exists(folder_path):
        print(f"Warning: Folder {folder_path} does not exist")
        return student_data

    csv_files = list(Path(folder_path).glob("*.csv"))

    print(f"Found {len(csv_files)} CSV files in {folder_path}")

    for csv_file in csv_files:
        student_info = read_identifier_csv(str(csv_file))

        if student_info:
            student_data.append(student_info)

    return student_data


def write_master_list(student_data, output_file):
    """
    Write the combined master list to a CSV file.
    """
    if not student_data:
        print("No student data to write")
        return

    fieldnames = ['first_name', 'last_name', 'unique_id']

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            sorted_data = sorted(student_data, key=lambda x: (x.get('last_name', ''), x.get('first_name', '')))

            for student in sorted_data:
                writer.writerow({
                    'first_name': student.get('first_name', ''),
                    'last_name': student.get('last_name', ''),
                    'unique_id': student.get('unique_id', '')
                })

        print(f"Master list created: {output_file}")
        print(f"Total entries: {len(sorted_data)}")

    except Exception as e:
        print(f"Error writing output file: {e}")


def assemble_master_list(master_list_path, identifier_folder_path, output_file='master_list_updated.csv'):
    """
    Assemble master list by combining original master list with identifier CSVs.
    """
    print("Assembling master list...")

    master_list_data = read_master_list(master_list_path)
    identifier_data = process_identifier_folder(identifier_folder_path)

    all_student_data = master_list_data + identifier_data

    if not all_student_data:
        print("No student data found")
        return

    write_master_list(all_student_data, output_file)


def main():
    """Main function to handle command line arguments and run the script."""
    if len(sys.argv) < 3:
        print("Usage: python master_list_assembly.py <master_list_file> <identifier_folder_path> [output_file.csv]")
        print("Example: python master_list_assembly.py master_list.csv ./identifiers updated_master_list.csv")
        sys.exit(1)

    master_list_path = sys.argv[1]
    identifier_folder_path = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else 'master_list_updated.csv'

    if not os.path.isfile(master_list_path):
        print(f"Error: {master_list_path} is not a valid file")
        sys.exit(1)

    if not os.path.isdir(identifier_folder_path):
        print(f"Error: {identifier_folder_path} is not a valid directory")
        sys.exit(1)

    assemble_master_list(master_list_path, identifier_folder_path, output_file)


if __name__ == "__main__":
    main()

