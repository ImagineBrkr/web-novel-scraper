import sys
import re


def update_version(current_version, increment):
    """
    Updates the version.

    Args:
        current_version (str): Current version.
        increment (str): The type of increment: "patch", "minor", or "major".
    """
    try:
        # Find the current version using regex
        match = re.search(r'(\d+)\.(\d+)\.(\d+)', current_version)
        if not match:
            raise ValueError("Could not parse version")

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
        new_version = f"{major}.{minor}.{patch}"

        print(new_version)  # Print the new version for the workflow

    except Exception as e:
        print(f"Error updating the version: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python update_version.py <current_version> <increment>")
        print("Example: python update_version.py 1.0.0 patch")
        sys.exit(1)

    current_version = sys.argv[1]
    increment = sys.argv[2].lower()
    update_version(current_version, increment)
