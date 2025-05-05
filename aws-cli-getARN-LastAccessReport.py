import csv
import subprocess
import json
import time  # Import the time module

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

def get_last_accessed_details(role_arn):
    """
    Generates and retrieves the last accessed details for an IAM role using the AWS CLI.

    Args:
        role_arn (str): The ARN of the IAM role.

    Returns:
        dict: The full JSON response from the get-service-last-accessed-details command, or None if an error occurs.
    """
    try:
        # Generate service last accessed details
        generate_command = f"aws iam generate-service-last-accessed-details --arn {role_arn}"
        generate_result = subprocess.run(generate_command, shell=True, capture_output=True, text=True, check=True)
        generate_output = json.loads(generate_result.stdout)
        job_id = generate_output['JobId']

        # Get service last accessed details
        get_command = f"aws iam get-service-last-accessed-details --job-id {job_id}"

        # Wait and retry mechanism
        max_attempts = 10
        for attempt in range(max_attempts):
            get_result = subprocess.run(get_command, shell=True, capture_output=True, text=True)  # Don't check=True here

            if get_result.returncode == 0:
                get_output = json.loads(get_result.stdout)
                if get_output['JobStatus'] == 'COMPLETED':
                    return get_output  # Return the full JSON response
                elif get_output['JobStatus'] == 'IN_PROGRESS':
                    print(f"Job {job_id} in progress, attempt {attempt + 1}/{max_attempts}. Waiting...")
                else:
                    print(f"Job {job_id} failed with status: {get_output['JobStatus']}")
                    return get_output  # Return the full JSON response even if failed
            else:
                print(f"Attempt {attempt + 1}/{max_attempts} failed to retrieve details: {get_result.stderr}")

            if attempt < max_attempts - 1:
                time.sleep(5)  # Wait for 5 seconds before retrying

        print(f"Max attempts reached. Unable to retrieve details for job {job_id}")
        return None

    except subprocess.CalledProcessError as e:
        print(f"Error getting last accessed details for role {role_arn}: {e}")
        print(f"Stderr: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response for role {role_arn}: {e} - Raw Output: {get_result.stdout if 'get_result' in locals() else generate_result.stdout}")
        return None
    except KeyError as e:
        print(f"KeyError: {e}.  The JSON response may not have the expected structure. Raw output: {get_result.stdout if 'get_result' in locals() else generate_result.stdout}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching last accessed details for {role_arn}: {e}")
        return None

def main():
    """
    Reads IAM role names from a CSV file, retrieves their ARNs, gets last accessed details, and updates the CSV.
    """
    csv_file = r'c:\users\jamiesmith\.vscode\cli\iam_roles.csv'
    print(f"Attempting to open CSV file: {csv_file}")

    try:
        # Read existing data first
        with open(csv_file, 'r') as infile:
            reader = csv.reader(infile)
            header = next(reader, None)  # Read header row (if any)
            data = list(reader)  # Read all rows into a list

        # Process the data and get ARNs
        for row in data:
            if row and len(row) >= 1:  # Check if row is not empty and has at least one column
                role_name = row[0].strip()
                print(f"Processing role: {role_name}")

                role_arn = get_role_arn(role_name)
                if role_arn:
                    print(f"Role ARN: {role_arn}")
                    if len(row) < 2:  # If Role ARN is not already in column 2
                        row.append(role_arn)  # Add ARN to the row
                    else:
                        row[1] = role_arn  # Update the existing Role ARN

                    # Get Last Accessed Details
                    last_accessed_details = get_last_accessed_details(role_arn)  # Get the full JSON
                    if last_accessed_details:
                        # Convert the JSON response to a string for CSV storage
                        last_accessed_str = json.dumps(last_accessed_details)
                        row.append(last_accessed_str)  # Add the JSON string to the row
                        print(f"Last Accessed Details added to CSV.")
                    else:
                        row.append("DETAILS_FAILED")  # Indicate failure to retrieve details
                        print("Failed to retrieve Last Accessed Details.")
                else:
                    print(f"Failed to retrieve ARN for {role_name}")
                    if len(row) < 2:
                        row.append("ARN_NOT_FOUND")
                    else:
                        row[1] = "ARN_NOT_FOUND"
                    row.append("ARN_FAILED")  # No details if no ARN
            else:
                print("Skipping empty or incomplete row")

        # Write back to the CSV file
        with open(csv_file, 'w', newline='') as outfile:  # Use newline='' to prevent extra blank rows
            writer = csv.writer(outfile)
            if header:
                writer.writerow(header + ['Role ARN', 'LastAccessedDetails'])  # Write header with new columns
            else:
                writer.writerow(['Role Name', 'Role ARN', 'LastAccessedDetails'])  # Write default header
            writer.writerows(data)  # Write all rows
        print("Successfully updated CSV file with Role ARNs and Last Accessed Details.")

    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
