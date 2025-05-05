import csv
import subprocess
import json

def get_role_arn(role_name):
    """Retrieves the ARN of an IAM role using the AWS CLI."""
    try:
        command = f"aws iam get-role --role-name {role_name}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        output = json.loads(result.stdout)
        arn = output['Role']['Arn']
        return arn
    except subprocess.CalledProcessError as e:
        print(f"Error getting ARN for role {role_name}: {e}")
        print(f"Stderr: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response for role {role_name}: {e} - Raw Output: {result.stdout}")
        return None
    except KeyError as e:
        print(f"KeyError: {e}.  The JSON response may not have the expected structure. Raw output: {result.stdout}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching ARN for {role_name}: {e}")
        return None

def main():
    """
    Reads IAM role names from a CSV file, retrieves their ARNs, and writes the ARN back to column 2 of the CSV.
    """
    csv_file = r'c:\users\jamiesmith\.vscode\cli\iam_roles-7.csv'
    print(f"Attempting to open CSV file: {csv_file}")

    try:
        # Read existing data first
        with open(csv_file, 'r') as infile:
            reader = csv.reader(infile)
            header = next(reader, None)  # Read header row (if any)
            data = list(reader)  # Read all rows into a list

        # Process the data and get ARNs
        for row in data:
            if row:  # Check if row is not empty
                role_name = row[0].strip()
                print(f"Processing role: {role_name}")

                role_arn = get_role_arn(role_name)
                if role_arn:
                    print(f"Role ARN: {role_arn}")
                    row.append(role_arn)  # Add ARN to the row
                else:
                    print(f"Failed to retrieve ARN for {role_name}")
                    row.append("ARN_NOT_FOUND")  # Add a placeholder value
            else:
                print("Skipping empty row")

        # Write back to the CSV file
        with open(csv_file, 'w', newline='') as outfile:  # Use newline='' to prevent extra blank rows
            writer = csv.writer(outfile)
            if header:
                writer.writerow(header + ['Role ARN'])  # Write header with new column
            writer.writerows(data)  # Write all rows
        print("Successfully updated CSV file with Role ARNs.")

    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
