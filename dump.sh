#!/bin/bash

# Check if at least one directory is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <directory> [output_file]"
    echo "       If output_file is not provided, project_dump.txt will be used"
    exit 1
fi

# Get the directory to search
directory="$1"

# Set the output file (default to project_dump.txt if not provided)
output_file="${2:-project_dump.txt}"

# Create or clear the output file
> "$output_file"

echo "Dumping all Python files from $directory to $output_file..."

# Find all .py files in the directory and its subdirectories
find "$directory" -type f \( -name "*.py" -o -name "*.tcss" \) | sort | while read -r file; do
    # Add file path as header with a clear format
    echo "############################################################" >> "$output_file"
    echo "# FILE: $file" >> "$output_file"
    echo "############################################################" >> "$output_file"
    echo "" >> "$output_file"  # Empty line for better readability

    # Append file content
    cat "$file" >> "$output_file"

    # Add a separator for better readability
    echo "" >> "$output_file"
    echo "" >> "$output_file"
done

echo "Done! Project code has been dumped to $output_file"
