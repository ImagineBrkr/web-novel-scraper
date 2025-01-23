import sys
import re

def update_version(file_path, increment):
    """
    Updates the version in the specified file.

    Args:
        file_path (str): Path to the file containing the version.
        increment (str): The type of increment: "patch", "minor", or "major".
    """
    try:
        # Read the file
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Find the current version using regex
        match = re.search(r'__version__ = "(\d+)\.(\d+)\.(\d+)"', content)
        if not match:
            raise ValueError("Version not found in the file.")

        # Extract MAJOR, MINOR, and PATCH values
        major, minor, patch = map(int, match.groups())

        # Increment the appropriate part
        if increment == "major":
            major += 1
            minor = 0
            patch = 0
        elif increment == "minor":
            minor += 1
            patch = 0
        elif increment == "patch":
            patch += 1
        else:
            raise ValueError("Increment type must be 'major', 'minor', or 'patch'.")

        # Generate the new version
        new_version = f'{major}.{minor}.{patch}'

        # Update the file content with the new version
        updated_content = re.sub(r'__version__ = "(\d+)\.(\d+)\.(\d+)"',
                                 f'__version__ = "{new_version}"',
                                 content)

        # Write the updated content back to the file
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(updated_content)

        print(new_version)  # Print the new version for the workflow

    except Exception as e:
        print(f"Error updating the version: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python update_version.py <file_path> <increment>")
        print("Example: python update_version.py web_novel_scraper/version.py patch")
        sys.exit(1)

    file_path = sys.argv[1]
    increment = sys.argv[2].lower()
    update_version(file_path, increment)
